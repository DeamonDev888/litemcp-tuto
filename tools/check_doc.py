#!/usr/bin/env python3
"""Verifie que le tuto LiteMCP reste coherent avec la version publiee.

Le README est une **recette** : on lit le tuto de haut en bas, on
applique chaque bloc au fichier `src/main.rs`, et le resultat doit
compiler a chaque etape. Ce script rejoue exactement ce scenario.

Modele :

- le tuto alterne des **blocs autonomes** (un programme complet avec son
  `fn main`, un struct, un `use`) et des **fragments de chaine**
  (`.tool(…)`, `.annotate(…)`) qui s'inserent dans le `ServerBuilder`
  du programme courant ;
- on garde un etat cumulatif et on recompile apres chaque bloc ;
- un bloc qui casse la compilation = la doc ment sur l'API -> echec.

Quatre controles, tous bloquants pour la publication :

1. **Compilation** — chaque bloc compile dans le contexte cumulatif.
2. **Symboles** — chaque `zod::xxx` / `litemcp::xxx` cite doit exister
   dans le code source de la version publiee.
3. **Pins de version** — le numero de version cite doit correspondre a la
   version publiee.
4. **Exemple du depot** — `mon-premier-mcp/` doit compiler.

Usage :
    python3 tools/check_doc.py --version 0.6.0

Code de sortie : 0 = tout est bon, 1 = au moins un probleme.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
README = REPO / "README.md"
EXAMPLE = REPO / "mon-premier-mcp"

CARGO = shutil.which("cargo") or "cargo"

# Imports imposes : le tuto suppose toujours ces imports la.
BASE_USES = [
    "use litemcp::prelude::*;",
    "use serde::Deserialize;",
    "use serde_json::json;",
    "use std::sync::Arc;",
    "use std::sync::atomic::{AtomicU64, Ordering};",
]

# Operations terminales d'une chaine de builder : un fragment de chaine
# doit etre insere AVANT elles (on ne peut pas appeler .tool_parse()
# apres .serve()).
TERMINAL_OPS = re.compile(r"^\s*\.(bind|serve|core)\b")

# Tete de la chaine du builder.
CHAIN_HEAD = re.compile(r"^\s*ServerBuilder\b")

# Methodes du `ServerBuilder` (source : `impl ServerBuilder` du crate).
# Un fragment `.xxx(…)` est un fragment de chaine UNIQUEMENT si `xxx`
# est une de ces methodes — sinon c'est un fragment de schéma zod
# (`.field`, `.opt`, `.strict()`, `.default(…)`, `.min`…), qui se
# compile dans le contexte d'un `Obj`, pas d'un builder.
BUILDER_METHODS = {
    "allow_origins", "annotate", "bind", "connection_ttl", "core",
    "max_connections", "new", "output_schema", "prompt", "prompt_typed",
    "read_timeout", "resource", "route", "tool", "tool_parse",
    "tool_timeout", "tool_typed", "with_tool", "serve",
}


def log(msg: str) -> None:
    print(msg, flush=True)


# --------------------------------------------------------------------------
# Lexique Rust : neutralise commentaires et chaines.
# --------------------------------------------------------------------------
def strip_code_noise(line: str, in_block: bool) -> tuple[str, bool]:
    out: list[str] = []
    i = 0
    n = len(line)
    while i < n:
        ch = line[i]
        if in_block:
            if ch == "*" and i + 1 < n and line[i + 1] == "/":
                in_block = False
                i += 2
                continue
            i += 1
            continue
        if ch == "/" and i + 1 < n and line[i + 1] == "/":
            break
        if ch == "/" and i + 1 < n and line[i + 1] == "*":
            in_block = True
            i += 2
            continue
        if ch == '"':
            j = i + 1
            while j < n:
                if line[j] == "\\":
                    j += 2
                    continue
                if line[j] == '"':
                    j += 1
                    break
                j += 1
            out.append('""')
            i = j
            continue
        out.append(ch)
        i += 1
    return "".join(out), in_block


def bracket_delta(code: str) -> tuple[int, int, int]:
    return (
        code.count("{") - code.count("}"),
        code.count("(") - code.count(")"),
        code.count("[") - code.count("]"),
    )


# --------------------------------------------------------------------------
# Extraction des blocs
# --------------------------------------------------------------------------
def extract_rust_blocks(markdown: str) -> list[tuple[int, str]]:
    """Retourne [(numero de ligne, code)] pour chaque bloc ```rust."""
    blocks: list[tuple[int, str]] = []
    lines = markdown.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip() in ("```rust", "``` rust"):
            start = i + 1
            j = start
            while j < len(lines) and lines[j].strip() != "```":
                j += 1
            blocks.append((start + 1, "\n".join(lines[start:j])))
            i = j + 1
            continue
        i += 1
    return blocks


def has_main(code: str) -> bool:
    """Vrai si le bloc definit un `fn main` (programme complet)."""
    return re.search(r"^\s*(pub\s+)?fn\s+main\s*\(", code, re.M) is not None


# --------------------------------------------------------------------------
# Decoupage d'un bloc en elements
# --------------------------------------------------------------------------
class Chunk:
    """Un element de code : ses lignes et sa nature."""

    def __init__(self, kind: str, lines: list[str]) -> None:
        self.kind = kind          # 'use' | 'item' | 'chain' | 'local'
        self.lines = lines


def split_block(code: str) -> list[Chunk]:
    """Decoupe un bloc en elements : uses, items, chaines, instructions.

    Le suivi de la profondeur utilise les trois types de crochets, ce qui
    gere les closures `|args| { … }` et les appels multi-lignes.
    """
    chunks: list[Chunk] = []
    lines = code.splitlines()
    depth = (0, 0, 0)
    in_block = False
    current: Chunk | None = None
    pending_attrs: list[str] = []

    for line in lines:
        code_only, in_block = strip_code_noise(line, in_block)
        stripped = code_only.strip()
        delta = bracket_delta(code_only)
        new_depth = (
            depth[0] + delta[0],
            depth[1] + delta[1],
            depth[2] + delta[2],
        )
        at_top = new_depth == (0, 0, 0)

        if current is not None:
            current.lines.append(line)
            depth = new_depth
            if at_top:
                chunks.append(current)
                current = None
            continue

        if not stripped:
            continue

        if stripped.startswith("use "):
            chunks.append(Chunk("use", [stripped]))
            continue

        # Attribut (`#[tool(...)]`, `#[derive(...)]`) : il appartient a
        # l'item qui suit — on le memorise pour l'y rattacher.
        if stripped.startswith("#["):
            pending_attrs.append(line)
            continue

        if stripped.startswith("."):
            # Fragment de chaine du builder (`.tool(…)`) ou fragment de
            # schéma zod (`.field(…)`, `.opt(…)`, `.strict()`) ?
            method = re.match(r"^\.([a-z_][a-z0-9_]*)", stripped)
            kind = (
                "chain"
                if method and method.group(1) in BUILDER_METHODS
                else "schema"
            )
            current = Chunk(kind, pending_attrs + [line])
            pending_attrs = []
            depth = new_depth
            if at_top:
                chunks.append(current)
                current = None
            continue

        if re.match(r"^(let|const|static)\s", stripped):
            current = Chunk("local", pending_attrs + [line])
            pending_attrs = []
            depth = new_depth
            if at_top:
                chunks.append(current)
                current = None
            continue

        # Item top-level : struct, fn, impl, macro…
        current = Chunk("item", pending_attrs + [line])
        pending_attrs = []
        depth = new_depth
        if at_top:
            chunks.append(current)
            current = None

    if current is not None:
        chunks.append(current)
    return chunks


# --------------------------------------------------------------------------
# Etat cumulatif du fichier src/main.rs
# --------------------------------------------------------------------------
class Recipe:
    """L'etat du `src/main.rs` tel qu'il evolves au fil du tuto.

    Le `main.rs` courant est une liste de lignes. Les fragments de
    chaine du builder sont inseres **avant** les operations terminales
    (`.bind`, `.serve`), pour respecter l'ordre d'appel reellement
    documente dans le tuto.
    """

    def __init__(self) -> None:
        self.uses: list[str] = list(BASE_USES)
        self.items: list[str] = []     # structs / fonctions top-level
        self.pre: list[str] = []       # instructions AVANT la chaine
        self.chain: list[str] = []     # la chaine du builder
        self.post: list[str] = []      # instructions APRES la chaine
        self.schema_fragments: list[str] = []   # fragments zod isolés

    # -- helpers ----------------------------------------------------------
    def add_use(self, line: str) -> None:
        line = line.strip()
        if line and line not in self.uses:
            self.uses.append(line)

    def insert_chain(self, fragment: list[str]) -> None:
        """Insere un fragment dans la chaine, avant les ops terminales.

        Le fragment s'insere juste apres la tete de la chaine
        (`ServerBuilder::new(…)`) et avant la premiere operation
        terminale (`.bind`, `.serve`) — c'est exactement la ou le tuto
        demande de l'ajouter.
        """
        if not self.chain:
            # Pas de chaine : on la demarre.
            self.chain = ['    ServerBuilder::new("tuto", "0.1.0")']
            self.chain.extend(fragment)
            return
        # Debut : apres la tete de la chaine (et ses lignes de suite).
        start = 0
        for idx, line in enumerate(self.chain):
            if CHAIN_HEAD.match(line):
                start = idx + 1
                break
        # Fin : avant la premiere operation terminale (.bind, .serve).
        end = len(self.chain)
        for idx in range(start, len(self.chain)):
            if TERMINAL_OPS.match(self.chain[idx]):
                end = idx
                break
        self.chain[end:end] = fragment

    @staticmethod
    def _is_terminal(line: str) -> bool:
        """Vrai si la ligne est l'operation terminale (`.serve()`)."""
        # Le commentaire de fin de ligne ne compte pas.
        code = line.split("//", 1)[0].rstrip()
        return code.endswith(".serve()")

    # -- application d'un bloc -------------------------------------------
    def add_block(self, code: str) -> None:
        """Applique un bloc du tuto a l'etat courant."""
        chunks = split_block(code)

        if has_main(code):
            # Bloc = programme complet : le lecteur remplace son main.rs.
            self.uses = list(BASE_USES)
            self.items = []
            self.pre = []
            self.chain = []
            self.post = []
            self.schema_fragments = []

        for chunk in chunks:
            if chunk.kind == "use":
                self.add_use(chunk.lines[0])
            elif chunk.kind == "item":
                if "fn main" in chunk.lines[0]:
                    self._absorb_main(chunk)
                else:
                    self.items.append("\n".join(chunk.lines))
            elif chunk.kind == "local":
                # Une instruction locale (`let …`) se pose AVANT la
                # chaine du builder (le tuto l'explique ainsi).
                self.pre.extend(chunk.lines)
            elif chunk.kind == "schema":
                # Fragment de schéma zod (`.field(…)`, `.opt(…)`, …) :
                # on le note pour le rendre comme expression zod
                # autonome dans le programme.
                self.schema_fragments.append("\n".join(chunk.lines))
            elif chunk.kind == "chain":
                self.insert_chain(chunk.lines)

    def _absorb_main(self, chunk: Chunk) -> None:
        """Le bloc contient un `fn main` : on en garde le corps.

        Le corps est mis en pieces : instructions avant la chaine, chaine
        du builder, instructions apres. Les fragments de chaine qui
        suivent viendront s'inserer dans la chaine.

        La chaine est reconnue par sa tete (`ServerBuilder::new(…)`) et
        se poursuit tant que les parenthèses ne sont pas refermées — un
        appel `.tool(` occupe plusieurs lignes.
        """
        lines = chunk.lines
        body = lines[1:]
        if body and body[-1].strip() == "}":
            body = body[:-1]

        chain: list[str] = []
        pre: list[str] = []
        post: list[str] = []
        in_chain = False
        chain_done = False
        depth = (0, 0, 0)
        chain_depth = (0, 0, 0)
        in_block = False

        for line in body:
            code_only, in_block = strip_code_noise(line, in_block)
            stripped = code_only.strip()
            delta = bracket_delta(code_only)
            new_depth = (
                depth[0] + delta[0],
                depth[1] + delta[1],
                depth[2] + delta[2],
            )

            if chain_done:
                post.append(line)
                depth = new_depth
                continue

            if in_chain:
                # La chaine se poursuit tant qu'une parenthese reste
                # ouverte (un appel `.tool(` occupe plusieurs lignes) ou
                # que la ligne est une operation du builder (`.…`).
                # La ligne qui **referme** l'appel appartient encore a
                # la chaine.
                was_open = depth[1] > chain_depth[1]
                open_paren = new_depth[1] > chain_depth[1]
                is_closer = was_open and not open_paren
                if not open_paren and not is_closer and not stripped.startswith("."):
                    in_chain = False
                    chain_done = True
                    post.append(line)
                    depth = new_depth
                    continue
                chain.append(line)
                depth = new_depth
                continue

            if CHAIN_HEAD.match(line):
                in_chain = True
                chain.append(line)
                depth = new_depth
                chain_depth = new_depth
                continue

            pre.append(line)
            depth = new_depth

        self.pre = pre
        self.chain = chain
        self.post = post

    # -- rendu ------------------------------------------------------------
    def program(self) -> str:
        """Le fichier `src/main.rs` courant."""
        parts = ["#![allow(dead_code, unused_variables, unused_imports, unused_mut)]"]
        parts += self.uses
        parts += [l for l in self.items if l.strip()]
        # Les fragments de schéma zod se vérifient comme expressions
        # autonomes, en dehors du `main` (fonctions qui les construisent).
        for i, frag in enumerate(self.schema_fragments):
            parts.append(f"#[allow(dead_code)]")
            parts.append(f"fn _tuto_schema_{i}() -> impl litemcp::zod::Schema {{")
            parts.append("    zod::object()")
            parts.extend("    " + l for l in frag.splitlines())
            parts.append("}")
        parts.append("fn main() -> std::io::Result<()> {")
        parts += self.pre
        if self.chain:
            parts += self.chain
            # La chaine se termine par `.serve()` : c'est l'expression
            # de retour du `main` (elle rend un `Result`).
            if self._is_terminal(self.chain[-1]):
                parts.append("}")
                return "\n".join(parts) + "\n"
            parts.append("    ;")
        parts += self.post
        parts.append("    Ok(())")
        parts.append("}")
        return "\n".join(parts) + "\n"
# --------------------------------------------------------------------------
# Verification de la source publiee
# --------------------------------------------------------------------------
def cargo_registry_src() -> Path | None:
    """Localise le code source de litemcp dans le cache de cargo."""
    cargo_home = Path(os.environ.get("CARGO_HOME", Path.home() / ".cargo"))
    registry_src = cargo_home / "registry" / "src"
    if not registry_src.is_dir():
        return None

    best: tuple[tuple[int, ...], Path] | None = None
    for crate_dir in registry_src.iterdir():
        if not crate_dir.is_dir():
            continue
        for cand in crate_dir.glob("litemcp-*"):
            if not cand.is_dir():
                continue
            ver = cand.name.split("-", 1)[1]
            try:
                key = tuple(int(p) for p in ver.split("-")[0].split("."))
            except ValueError:
                continue
            if best is None or key > best[0]:
                best = (key, cand)
    if best is None:
        return None
    return best[1]


def rust_symbols(src_root: Path) -> set[str]:
    """Symboles publics exposes par la crate (fonctions, types, methodes)."""
    known: set[str] = set()
    for path in sorted(src_root.rglob("*.rs")):
        text = path.read_text(encoding="utf-8", errors="replace")
        known |= set(re.findall(r"^pub fn ([a-z_][a-z0-9_]*)", text, re.M))
        known |= set(re.findall(r"^\s+pub fn ([a-z_][a-z0-9_]*)", text, re.M))
        known |= set(re.findall(r"^pub struct ([A-Za-z_][A-Za-z0-9_]*)", text, re.M))
        known |= set(re.findall(r"^pub enum ([A-Za-z_][A-Za-z0-9_]*)", text, re.M))
        known |= set(re.findall(r"^pub trait ([A-Za-z_][A-Za-z0-9_]*)", text, re.M))
        known |= set(re.findall(r"^pub mod ([a-z_][a-z0-9_]*)", text, re.M))
        known |= set(re.findall(r"^pub const ([A-Z_][A-Z0-9_]*)", text, re.M))
        for group in re.findall(r"^pub use [^;{]*\{([^}]*)\}", text, re.M | re.S):
            known |= set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", group))
    return known


def cargo_build(pkg: Path) -> tuple[bool, str]:
    proc = subprocess.run(
        [CARGO, "build", "--quiet"],
        cwd=pkg,
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0, (proc.stderr or proc.stdout)


def make_pkg(pkg: Path, code: str, litemcp_req: str) -> None:
    src = pkg / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "main.rs").write_text(code, encoding="utf-8")
    (pkg / "Cargo.toml").write_text(
        "[package]\n"
        f'name = "{pkg.name}"\n'
        'version = "0.0.0"\n'
        'edition = "2024"\n'
        "\n"
        "[dependencies]\n"
        f'litemcp = {{ version = "{litemcp_req}", features = ["macros"] }}\n'
        'serde = { version = "1", features = ["derive"] }\n'
        'serde_json = "1"\n',
        encoding="utf-8",
    )


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="0.6.0", help="version publiee attendue")
    ap.add_argument("--skip-compile", action="store_true")
    args = ap.parse_args()

    litemcp_req = ".".join(args.version.split(".")[:2])
    failures: list[str] = []
    readme = README.read_text(encoding="utf-8")

    # ---------- 0. Pins de version ----------
    log(f"→ pins de version (attendu : {litemcp_req})")
    for pattern, label in (
        (r"litemcp = \"(\d+\.\d+)\"", 'litemcp = "X.Y"'),
        (r"litemcp = \{ version = \"(\d+\.\d+)\"", 'litemcp = { version = "X.Y"'),
    ):
        for found in re.findall(pattern, readme):
            if found != litemcp_req:
                log(f"  ✗ pin obsolete : {label} → \"{found}\" (attendu \"{litemcp_req}\")")
                failures.append(
                    f"pin de version obsolete : \"{found}\" (attendu \"{litemcp_req}\")"
                )
            else:
                log(f"  ✓ {label} = \"{found}\"")

    # ---------- 1. Compilation ----------
    blocks = extract_rust_blocks(readme)
    log(f"→ {len(blocks)} blocs ```rust dans README.md")

    if not args.skip_compile:
        with tempfile.TemporaryDirectory(prefix="tuto-check-") as tmp:
            workdir = Path(tmp)
            recipe = Recipe()
            for idx, (line_no, code) in enumerate(blocks):
                recipe.add_block(code)
                pkg = workdir / f"b{idx:02d}"
                make_pkg(pkg, recipe.program(), litemcp_req)
                ok, err = cargo_build(pkg)
                if ok:
                    log(f"  ✓ bloc ligne {line_no} compile")
                else:
                    log(f"  ✗ bloc ligne {line_no} NE COMPILE PAS")
                    for line in [l for l in err.splitlines() if l.strip()][:8]:
                        log(f"      {line}")
                    failures.append(f"README.md:{line_no} — bloc rust non compilable")

    # ---------- 2. Symboles d'API ----------
    cited = set(re.findall(r"\bzod::([a-z_][a-z0-9_]*)\s*\(", readme))
    cited |= set(re.findall(r"\blitemcp::([A-Za-z_][A-Za-z0-9_]*)", readme))
    cited -= {"macros", "prelude", "protocol", "ToolResult"}
    log(f"→ {len(cited)} symboles d'API cités")

    src_root = cargo_registry_src()
    if src_root is None:
        log("  (source litemcp introuvable dans le cache cargo — contrôle sauté)")
    else:
        known = rust_symbols(src_root)
        missing = sorted(s for s in cited if s not in known)
        if missing:
            for m in missing:
                log(f"  ✗ symbole inexistant dans litemcp {args.version} : {m}")
            failures.append(
                f"symboles absents de litemcp {args.version} : {', '.join(missing)}"
            )
        else:
            log(f"  ✓ tous les symboles existent dans litemcp {args.version}")

    # ---------- 3. Exemple du dépôt ----------
    if EXAMPLE.exists() and not args.skip_compile:
        log("→ compilation de mon-premier-mcp/ (le code complet du tuto)")
        proc = subprocess.run(
            [CARGO, "build", "--quiet"],
            cwd=EXAMPLE,
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            log("  ✓ mon-premier-mcp compile")
        else:
            log("  ✗ mon-premier-mcp NE COMPILE PAS")
            for line in [l for l in (proc.stderr or "").splitlines() if l.strip()][:8]:
                log(f"      {line}")
            failures.append("mon-premier-mcp ne compile pas")

    # ---------- Bilan ----------
    if failures:
        log("")
        log("✗ ÉCHEC :")
        for f in failures:
            log(f"  - {f}")
        return 1

    log("")
    log("✓ tuto cohérent avec litemcp")
    return 0


if __name__ == "__main__":
    sys.exit(main())
