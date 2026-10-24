<div align="center">
  <h1><font color="#2ECC71">Mon premier serveur MCP en Rust</font></h1>
  <p><strong>Le guide ULTRA débutant pour créer vos propres outils IA avec <a href="https://github.com/DeamonDev888/litemcp">LiteMCP</a>.</strong></p>
  <p>Aucune connaissance de MCP requise. Si vous savez lancer un terminal, vous pouvez suivre.</p>
  <p>
    <img src="https://img.shields.io/badge/Rust-1.85%2B-DEA584?style=for-the-badge&logo=rust" alt="Rust 1.85+">
    <img src="https://img.shields.io/badge/LiteMCP-0.5-2ECC71?style=for-the-badge" alt="LiteMCP 0.5">
    <img src="https://img.shields.io/badge/Spec_MCP-2026--07--28-3fb950?style=for-the-badge" alt="Spec MCP 2026-07-28">
    <img src="https://img.shields.io/badge/niveau-d%C3%A9butant-F9D34C?style=for-the-badge" alt="Niveau débutant">
  </p>
</div>

---

## 📜 Table des matières

- [🌟 Introduction — c'est quoi MCP ?](#-introduction--cest-quoi-mcp-)
- [🧰 C'est quoi un « outil » ?](#-cest-quoi-un-outil-)
- [⚡ Pourquoi LiteMCP ?](#-pourquoi-litemcp-)
- [📋 Prérequis](#-prérequis)
- [🚀 Étape 1 — Créer le projet](#-étape-1--créer-le-projet)
- [📦 Étape 2 — Installer LiteMCP](#-étape-2--installer-litemcp)
- [✍️ Étape 3 — Votre premier outil](#️-étape-3--votre-premier-outil)
- [▶️ Étape 4 — Lancer le serveur](#️-étape-4--lancer-le-serveur)
- [🧪 Étape 5 — Tester avec curl](#-étape-5--tester-avec-curl)
- [🔍 Étape 6 — L'Inspecteur MCP (client visuel)](#-étape-6--linspecteur-mcp-client-visuel)
- [🛡️ Étape 7 — Des outils qui se protègent tout seuls](#️-étape-7--des-outils-qui-se-protègent-tout-seuls)
- [⚠️ Étape 8 — Gérer les erreurs](#️-étape-8--gérer-les-erreurs)
- [🧠 Étape 9 — Un outil avec de la mémoire](#-étape-9--un-outil-avec-de-la-mémoire)
- [🏷️ Étape 10 — Les annotations](#️-étape-10--les-annotations)
- [🎁 Bonus — La macro `#[tool]`](#-bonus--la-macro-tool)
- [🤖 Étape finale — Connecter un vrai client IA](#-étape-finale--connecter-un-vrai-client-ia)
- [🖥️ Aller plus loin](#️-aller-plus-loin)
- [📖 Référence rapide](#-référence-rapide)
- [🤝 Contribution](#-contribution)

---

## 🌟 Introduction — c'est quoi MCP ?

Un agent IA (Claude, Hermes, Gemini CLI…) est un cerveau brillant **enfermé dans une pièce sans fenêtre**.
Il peut réfléchir, écrire, planifier… mais il ne peut pas :

* 📄 lire un fichier sur votre disque,
* 🌐 chercher une information sur le web,
* ✉️ envoyer un email,
* 🧮 faire un calcul que VOUS avez programmé,
* 🗄️ parler à votre base de données.

Le **MCP** (*Model Context Protocol*) perce des **portes** dans cette pièce.
C'est un langage commun, standardisé, qui permet à n'importe quelle IA de
**découvrir et utiliser des outils** que vous avez écrits — dans n'importe quel
langage, sur n'importe quelle machine.

```
┌──────────────────┐   HTTP (JSON)      ┌──────────────────────┐
│   Client IA      │ ─────────────────► │   Votre serveur MCP  │
│  (Claude, Hermes │                    │   (vos outils, en    │
│   ou un script)  │ ◄───────────────── │    Rust)             │
└──────────────────┘   résultat JSON    └──────────────────────┘
```

Un **serveur MCP** est donc juste un petit programme qui **expose des outils**.
Ce tutoriel vous apprend à écrire le vôtre en Rust, en partant de zéro.

> 💡 **À la fin de ce tuto** vous aurez un serveur qui tourne avec 4 outils
> (bonjour, analyse de texte, division, compteur), testé et prêt à brancher
> sur n'importe quel client MCP. Le code complet est dans le dossier
> [`mon-premier-mcp/`](./mon-premier-mcp) de ce dépôt.

---

## 🧰 C'est quoi un « outil » ?

Un outil MCP, c'est **trois choses** :

1. Un **nom** — par ex. `analyze` ;
2. Une **description** en français courant — c'est elle que l'IA lit pour
   décider *quand* utiliser l'outil (« Statistiques d'un texte… ») ;
3. Des **paramètres** — quels champs l'IA doit vous envoyer (et lesquels sont
   optionnels), décrits par un schéma.

Quand l'IA veut se servir de l'outil, elle envoie un appel du style :
« appelle `analyze` avec `text = "bonjour le monde"` ». Votre code s'exécute,
renvoie un résultat JSON, et l'IA l'utilise pour continuer sa réflexion.

**Chaque nouvel outil est un nouveau super-pouvoir pour votre agent.**
Lecture de fichiers ? Un outil. Requête à une API météo ? Un outil.
Contrôle de votre maison intelligente ? Un outil. C'est vous qui décidez.

---

## ⚡ Pourquoi LiteMCP ?

[**LiteMCP**](https://github.com/DeamonDev888/litemcp) est une bibliothèque
Rust (publiée sur [crates.io](https://crates.io/crates/litemcp)) pensée pour
être **la plus légère de l'écosystème** :

| | |
|---|---|
| 🪶 **Minuscule** | 2 dépendances seulement (`serde` + `serde_json`) |
| 🚀 **Sans usine à gaz** | pas de tokio, pas de framework web — les threads standards de Rust |
| ✍️ **Quelques lignes suffisent** | votre premier serveur tient en 10 lignes |
| 🛡️ **Sûr par défaut** | validation des entrées, garde DNS-rebinding, corps limité |
| 📏 **Spéc 2026-07-28** | le MCP stateless moderne (Streamable HTTP), à la lettre |

Concrètement : vous écrivez quelques lignes, vous appelez `.serve()`, et un
vrai serveur MCP tourne **dans** votre programme.

---

## 📋 Prérequis

Avant de commencer, assurez-vous d'avoir :

1. <img src="https://img.shields.io/badge/Rust-1.85%2B-nécessaire-DEA584?logo=rust" alt="Rust nécessaire"> — le compilateur Rust, installé via [rustup](https://rustup.rs) :

   ```bash
   # Vérifiez votre installation :
   cargo --version
   # → cargo 1.85.0 (ou plus récent)
   ```

   Si rien ne s'affiche, installez Rust avec la commande officielle
   (https://rustup.rs), puis rouvrez votre terminal.

2. <img src="https://img.shields.io/badge/curl-pour_tester-blue" alt="curl pour tester"> — déjà présent sur macOS, Linux et Windows 10/11.

   ```bash
   curl --version
   ```

3. <img src="https://img.shields.io/badge/Node.js-optionnel-pour_l_Inspecteur-339933?logo=nodedotjs" alt="Node.js optionnel"> — *(optionnel)* uniquement pour l'Inspecteur MCP de l'étape 6 (`npx`).

C'est tout. **Pas de Docker, pas de Redis, pas de base de données.**

---

## 🚀 Étape 1 — Créer le projet

Ouvrez un terminal et lancez :

```bash
cargo new mon-premier-mcp
cd mon-premier-mcp
```

Cargo vient de créer cette structure :

```
mon-premier-mcp/
├── Cargo.toml      ← la carte d'identité du projet (nom, dépendances)
└── src/
    └── main.rs     ← votre code, exécuté au démarrage
```

Vérifiez que le squelette compile et tourne :

```bash
cargo run
#    Compiling mon-premier-mcp v0.1.0
#     Finished `dev` profile
#      Running `target\debug\mon-premier-mcp.exe`
# Hello, world!
```

👍 Si vous voyez `Hello, world!`, tout est prêt.

---

## 📦 Étape 2 — Installer LiteMCP

Ouvrez `Cargo.toml` et ajoutez les dépendances sous `[dependencies]` :

```toml
[dependencies]
litemcp = "0.5"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
```

* `litemcp` — la bibliothèque qui transforme votre programme en serveur MCP ;
* `serde` / `serde_json` — pour lire le JSON envoyé par l'IA et écrire vos réponses.

Téléchargez-les :

```bash
cargo fetch
```

> 💡 `serde` et `serde_json` sont les **seules** dépendances que LiteMCP
> embarque. Rien d'autre ne sera ajouté à votre projet.

---

## ✍️ Étape 3 — Votre premier outil

Remplacez **tout** le contenu de `src/main.rs` par :

```rust
use litemcp::prelude::*;

fn main() -> std::io::Result<()> {
    println!("Mon premier MCP écoute sur http://127.0.0.1:8080/mcp");

    ServerBuilder::new("mon-premier-mcp", "0.1.0")
        .tool(
            "hello",                        // 1. le nom de l'outil
            "Dit bonjour à quelqu'un",      // 2. la description (lue par l'IA)
            |args| {                        // 3. le code exécuté à chaque appel
                let name = args.get("name")
                    .and_then(|v| v.as_str())
                    .unwrap_or("monde");
                Ok(serde_json::json!({ "message": format!("Bonjour, {name} !") }))
            },
        )
        .bind("127.0.0.1:8080")?   // le serveur écoute sur le port 8080
        .serve()                   // bloque ici et répond aux requêtes
}
```

Lisons ce programme **ligne par ligne** :

| Ligne | Ce qu'elle fait |
|---|---|
| `use litemcp::prelude::*;` | importe tout le nécessaire de LiteMCP (`ServerBuilder`, `zod`, annotations…) |
| `fn main() -> std::io::Result<()>` | le point d'entrée ; le `Result` permet d'écrire `?` pour propager les erreurs réseau proprement |
| `ServerBuilder::new("mon-premier-mcp", "0.1.0")` | crée le serveur : son **nom** et sa **version** (c'est ce que l'IA verra) |
| `.tool("hello", "Dit bonjour…", \|args\| …)` | déclare UN outil : nom + description + fonction. C'est le cœur du tuto |
| `args.get("name")` | lit le champ `name` dans le JSON envoyé par l'IA |
| `.unwrap_or("monde")` | si l'IA n'a pas envoyé `name`, on salue « monde » (valeur par défaut) |
| `Ok(serde_json::json!({ … }))` | la **réponse** de l'outil : un objet JSON. `Ok(...)` = tout s'est bien passé |
| `.bind("127.0.0.1:8080")?` | ouvre le socket sur votre machine (127.0.0.1 = accessible uniquement en local) |
| `.serve()` | fait tourner le serveur — le programme reste ici, en attente d'appels |

L'outil `hello` est né. Passons au test.

---

## ▶️ Étape 4 — Lancer le serveur

```bash
cargo run
```

```
   Compiling mon-premier-mcp v0.1.0
    Finished `dev` profile
     Running `target\debug\mon-premier-mcp.exe`
Mon premier MCP écoute sur http://127.0.0.1:8080/mcp
```

Le serveur tourne. **Laissez ce terminal ouvert** — si vous le fermez, le
serveur s'arrête. Ouvrez un **second** terminal pour la suite.

> 💡 Besoin d'arrêter le serveur ? `Ctrl+C` dans son terminal.

---

## 🧪 Étape 5 — Tester avec curl

Un client MCP parle au serveur en JSON-RPC : une requête `POST` sur `/mcp`
avec un objet JSON qui dit ce qu'il veut. Testons les deux requêtes fondamentales.

### Appeler un outil : `tools/call`

Dans le second terminal :

```bash
curl -s http://127.0.0.1:8080/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"hello","arguments":{"name":"Alex"}}}'
```

Réponse :

```json
{"jsonrpc":"2.0","id":1,
 "result":{
   "content":[{"type":"text","text":"{\"message\":\"Bonjour, Alex !\"}"}],
   "structuredContent":{"message":"Bonjour, Alex !"},
   "resultType":"complete",
   "_meta":{"io.modelcontextprotocol/serverInfo":{"name":"mon-premier-mcp","version":"0.1.0"}}}}
```

🎉 **Votre outil vient d'être appelé à distance.** Ne vous fiez pas aux
champs en plus (`resultType`, `_meta`) : c'est le protocole qui ajoute la
carte d'identité du serveur à chaque réponse — normal et automatique.
Décortiquons la requête :

| Champ | Rôle |
|---|---|
| `"jsonrpc":"2.0"` | la version du protocole d'appel (toujours `2.0`) |
| `"id":1` | un numéro de ticket — il vous est **renvoyé tel quel** dans la réponse |
| `"method":"tools/call"` | l'action : « appelle un outil » |
| `"params.name":"hello"` | **quel** outil appeler |
| `"params.arguments":{"name":"Alex"}` | les arguments — c'est votre `args` côté Rust |

Et la réponse : le résultat se lit dans `result.structuredContent` (le JSON
exact que votre fonction a renvoyé) ; `result.content` contient la même chose
sous forme de texte, pour les clients qui préfèrent afficher du texte.

Essayez sans argument — la valeur par défaut prend le relais :

```bash
curl -s http://127.0.0.1:8080/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"hello","arguments":{}}}'
# → {"message":"Bonjour, monde !"}
```

### Lister les outils : `tools/list`

C'est **la première chose que fait un client IA** quand il se connecte :
il demande le catalogue pour savoir ce qui existe.

```bash
curl -s http://127.0.0.1:8080/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/list"}'
```

Réponse (abrégée) :

```json
{"jsonrpc":"2.0","id":3,"result":{"tools":[
  {"name":"hello",
   "description":"Dit bonjour à quelqu'un",
   "inputSchema":{"type":"object","properties":{...}}}
]}}
```

L'IA reçoit le nom, la description **et** le schéma des arguments : elle sait
tout ce qu'il faut pour appeler `hello` correctement.

### Bonus : la sonde de vie

```bash
curl -s http://127.0.0.1:8080/health
# ok
```

`/health` répond « ok » sans JSON-RPC — pratique pour vérifier en un clin
d'œil que le serveur vit (les outils de supervision l'utilisent).

---

## 🔍 Étape 6 — L'Inspecteur MCP (client visuel)

curl, c'est bien pour comprendre ; voir ses outils dans une **interface
graphique officielle**, c'est mieux. Le protocole MCP fournit un inspecteur.

### Lancement

```bash
npx @modelcontextprotocol/inspector
```

Cette commande démarre un serveur proxy et ouvre l'interface dans votre
navigateur, généralement à l'adresse `http://localhost:6274`.

### Configuration de la connexion

Dans la barre latérale :

1. **Type de transport** : sélectionnez `Streamable HTTP` ;
2. **URL** : entrez `http://127.0.0.1:8080/mcp` ;
3. Pas de token, pas d'options — votre serveur local n'en demande pas.

### Connexion

Cliquez sur **« Connect »**. L'inspecteur interroge votre serveur.

### Interaction

Une fois connecté, utilisez les onglets pour interagir :

* **Tools** — listez vos outils, remplissez leurs paramètres dans un
  formulaire généré depuis le schéma, et appelez-les d'un clic ;
* **Resources** / **Prompts** — les autres registres MCP (hors scope de ce
  tuto, votre serveur n'en expose pas encore).

Vous venez de reproduire exactement ce que fera un agent IA réel quand il
découvrira votre serveur — mais avec des formulaires au lieu de JSON.

---

## 🛡️ Étape 7 — Des outils qui se protègent tout seuls

Le registre `tool` de l'étape 3 est le plus simple : il vous laisse le JSON
brut et **vous** vérifiez tout. Pour un vrai outil, on veut mieux :

* que les **mauvais arguments soient rejetés avant** de toucher votre code ;
* que la **documentation** (le schéma publié à `tools/list`) soit **exacte** ;
* recevoir des arguments **déjà typés** dans une struct Rust.

C'est le job de `tool_parse` + les schémas `zod`. Ajoutons un outil `analyze`
qui fait des statistiques sur un texte. Dans `src/main.rs`, ajoutez en haut :

```rust
use serde::Deserialize;

// Les arguments de « analyze », remplis automatiquement après validation.
#[derive(Deserialize)]
struct AnalyzeArgs {
    text: String,             // requis
    uppercase: Option<bool>,  // optionnel
}
```

Puis dans la chaîne du `ServerBuilder`, juste après le bloc `.tool(...)` :

```rust
        .tool_parse(
            "analyze",
            "Statistiques d'un texte (mots, caractères, mot le plus long)",
            zod::object()
                .field("text", zod::string().min(1).max(10_000))  // requis, 1 à 10 000 caractères
                .opt("uppercase", zod::boolean())                 // optionnel
                .strict(),                                       // refuse les champs inconnus
            |args: AnalyzeArgs| {
                let longest = args.text.split_whitespace()
                    .max_by_key(|w| w.chars().count())
                    .unwrap_or("");
                let mut result = serde_json::json!({
                    "words": args.text.split_whitespace().count(),
                    "chars": args.text.chars().count(),
                    "longest": longest,
                });
                if args.uppercase.unwrap_or(false) {
                    result["shout"] = serde_json::json!(args.text.to_uppercase());
                }
                Ok(result)
            },
        )
```

Relancez le serveur (`Ctrl+C` puis `cargo run`) et testez :

```bash
curl -s http://127.0.0.1:8080/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"analyze","arguments":{"text":"le rust c est fort"}}'
```

```json
{"jsonrpc":"2.0","id":1,"result":{"structuredContent":{"words":5,"chars":19,"longest":"fort"}}}
```

Notez le gain côté code : `args.text` est un vrai `String`, `args.uppercase`
un vrai `Option<bool>` — **pas de `args.get(...)` manuel**.

### Et si l'IA envoie n'importe quoi ?

Le schéma est **exécuté avant** votre fonction. Texte vide, texte trop long,
champ inconnu — votre code n'est jamais appelé. Testez :

```bash
curl -s http://127.0.0.1:8080/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"analyze","arguments":{"text":""}}}'
```

```json
{"jsonrpc":"2.0","id":1,"error":{"code":-32602,
 "message":"Arguments invalides : `arguments.text` : au moins 1 caractère(s)",
 "data":{"issues":["`arguments.text` : au moins 1 caractère(s)"]}}}
```

`-32602` = « arguments invalides », et `error.data.issues` liste **chaque**
problème, en français, champ par champ (texte trop court, champ inconnu,
mauvais type…). C'est ce niveau de détail qui permet à l'IA de se corriger
elle-même et de rappeler l'outil correctement.

---

## ⚠️ Étape 8 — Gérer les erreurs

Il y a **deux sortes** d'erreurs, et il faut choisir la bonne :

| Situation | Quel registre | Ce que reçoit le client |
|---|---|---|
| Les arguments ne respectent pas le schéma | `tool_parse` / `tool_typed` | erreur `-32602` avec les `issues` — **votre code n'a pas tourné** |
| Votre code a tourné mais a échoué (division par zéro, fichier absent…) | `Err(message)` dans la closure | HTTP 200 avec `isError: true` et le message — **l'IA lit l'explication** |

Ajoutons l'exemple classique — la division :

```rust
        .tool("divide", "Divise a par b (erreur si b vaut 0)", |args| {
            let a = args.get("a").and_then(|v| v.as_f64).ok_or("a manquant ou pas un nombre")?;
            let b = args.get("b").and_then(|v| v.as_f64).ok_or("b manquant ou pas un nombre")?;
            if b == 0.0 {
                return Err("division par zéro".to_string());
            }
            Ok(serde_json::json!({ "quotient": a / b }))
        })
```

```bash
# Ça marche :
curl -s http://127.0.0.1:8080/mcp -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"divide","arguments":{"a":10,"b":4}}}'
# → {"structuredContent":{"quotient":2.5}}

# Et la division par zéro échoue PROPREMENT :
curl -s http://127.0.0.1:8080/mcp -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"divide","arguments":{"a":10,"b":0}}}'
# → {"result":{"isError":true,"content":[{"type":"text","text":"division par zéro"}]}}
```

Le serveur, lui, **continue de tourner** dans les deux cas : une erreur
d'outil n'est jamais un crash. Règle simple à retenir :

> **Arguments pourris → schéma (`-32602`). Échec de l'action → `Err(msg)`.**

---

## 🧠 Étape 9 — Un outil avec de la mémoire

Vos outils peuvent partager un **état** qui vit dans le processus et survit
aux connexions. Ajoutez en haut de `main.rs` :

```rust
use std::sync::Arc;
use std::sync::atomic::{AtomicU64, Ordering};
```

Puis, **avant** le `ServerBuilder` :

```rust
    let counter = Arc::new(AtomicU64::new(0));
    let counter_state = Arc::clone(&counter);
```

Et dans la chaîne :

```rust
        .tool("counter", "Incrémente et renvoie le compteur interne", move |_args| {
            let count = counter_state.fetch_add(1, Ordering::SeqCst) + 1;
            Ok(serde_json::json!({ "count": count }))
        })
```

Appelez-le plusieurs fois :

```bash
curl -s http://127.0.0.1:8080/mcp -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"counter","arguments":{}}}'
# → {"count":1}   … puis {"count":2}, {"count":3}, …
```

Chaque appel incrémente le compteur — même depuis des clients différents.
`Arc<AtomicU64>` est la façon standard en Rust de partager un compteur entre
plusieurs threads (LiteMCP lance un thread par connexion). Une base de
données, un cache, une file de tâches… tout se branche sur le même principe :
l'état vit **à côté** des outils, les closures le capturent.

---

## 🏷️ Étape 10 — Les annotations

Les annotations sont des **métadonnées honnêtes** publiées dans `tools/list` :
elles préviennent le client de ce que votre outil fait avant qu'il l'appelle.
Ajoutez-les à la fin de la chaîne, avant `.bind(...)` :

```rust
        .annotate("hello", ToolAnnotations::new().title("Bonjour").read_only(true).idempotent(true))
        .annotate("analyze", ToolAnnotations::new().title("Analyse").read_only(true))
        .annotate("divide", ToolAnnotations::new().title("Division").read_only(true))
        .annotate("counter", ToolAnnotations::new().title("Compteur"))
```

| Annotation | Signification pour le client |
|---|---|
| `.title("…")` | un joli nom d'affichage |
| `.read_only(true)` | l'outil ne modifie rien |
| `.destructive(true)` | l'outil peut détruire des données — le client peut demander confirmation |
| `.idempotent(true)` | appeler 2 fois donne le même résultat qu'une fois |
| `.open_world(true)` | l'outil parle à l'extérieur (web, API tierce) |

Un agent peut par exemple **refuser d'appeler un outil destructif** sans vous
demander confirmation. Déclarer honnêtement vos outils améliore la qualité des
décisions de l'IA.

---

## 🎁 Bonus — La macro `#[tool]`

Activez la feature `macros` dans `Cargo.toml` :

```toml
litemcp = { version = "0.5", features = ["macros"] }
```

Le schéma peut alors être **dérivé des types des paramètres** d'une fonction
ordinaire — plus de double déclaration schéma/struct :

```rust
use litemcp::macros::tool;

#[tool(name = "add", description = "Additionne deux entiers")]
fn add(a: i64, b: i64) -> litemcp::ToolResult {
    Ok(serde_json::json!({ "somme": a + b }))
}

fn main() -> std::io::Result<()> {
    ServerBuilder::new("mon-premier-mcp", "0.1.0")
        .with_tool(register_add)   // la macro a généré register_add
        .bind("127.0.0.1:8080")?
        .serve()
}
```

Types supportés : entiers, `f32`/`f64`, `bool`, `String`, `Option<T>`
(champ optionnel), `Vec<T>`. Même principe pour `#[resource]` et `#[prompt]`
(les deux autres registres MCP) — voir le
[README de LiteMCP](https://github.com/DeamonDev888/litemcp#macros-tool--resource--prompt-feature-macros).

---

## 🤖 Étape finale — Connecter un vrai client IA

Votre serveur tourne en HTTP sur `http://127.0.0.1:8080/mcp` — n'importe quel
client MCP capable de pointer sur une URL peut s'y brancher.

### Claude Desktop / Claude Code

```json
{
  "mcpServers": {
    "mon-premier-mcp": {
      "url": "http://localhost:8080/mcp"
    }
  }
}
```

### Hermes Agent (config.yaml)

```yaml
mcp:
  mon-premier-mcp:
    url: "http://localhost:8080/mcp"
```

### MCP Command Center

Le [MCP Command Center](https://github.com/DeamonDev888/mcp-command-center)
reconnaît les serveurs LiteMCP **par fingerprint** (sonde `/health` + version
de protocole) et les badgen automatiquement : état, liste des tools, latence,
journal — sans rien ajouter à votre code.

Une fois branché, demandez simplement à votre agent :
*« Analyse ce texte avec l'outil analyze »* — il découvrira tout seul comment
l'appeler grâce au schéma publié par `tools/list`. C'est toute la magie de MCP.

---

## 🖥️ Aller plus loin

* **Le code complet** de ce tuto (les 4 outils + annotations, prêt à compiler) :
  dossier [`mon-premier-mcp/`](./mon-premier-mcp) de ce dépôt — il accepte en
  plus une adresse en argument (`cargo run -- 127.0.0.1:8180`) si le port
  8080 est déjà occupé sur votre machine ;
* **Options du serveur** (chemin de route, timeouts, plafond de connexions,
  arrêt propre) : [README LiteMCP, section Configuration](https://github.com/DeamonDev888/litemcp#configuration) ;
* **Sécurité** : par défaut le bind est `127.0.0.1` (local uniquement). Pour
  exposer sur le réseau, placez le serveur derrière un reverse proxy (nginx)
  qui apporte TLS et authentification ;
* **Déploiement en service** (Linux) — extrait systemd :

  ```ini
  [Unit]
  Description=Mon premier serveur MCP
  After=network.target

  [Service]
  ExecStart=/opt/mon-premier-mcp/target/release/mon-premier-mcp
  Restart=always
  RestartSec=5

  [Install]
  WantedBy=multi-user.target
  ```

  (compilez avec `cargo build --release` pour le binaire de production) ;
* **Exemple de référence** : le serveur démo de validation de LiteMCP
  ([`litemcp-it`](https://github.com/DeamonDev888/litemcp-it)) — mêmes outils
  que ce tuto, avec 12 tests d'intégration sur de vraies sockets.

---

## 📖 Référence rapide

### Les trois registres d'outils

| API | Le handler reçoit | Schéma publié | Validation |
|---|---|---|---|
| `.tool(nom, desc, f)` | `&Value` (JSON brut) | générique | à votre charge |
| `.tool_typed(nom, desc, schéma, f)` | `&Value` (déjà validé) | dérivé du schéma | automatique |
| `.tool_parse(nom, desc, schéma, f)` | struct `Deserialize` | dérivé du schéma | automatique |

### Les schémas `zod`

| Expression | Contrôle |
|---|---|
| `zod::string().min(2).max(64)` | chaîne, longueur bornée |
| `zod::string().email()` / `.uuid()` / `.url()` / `.datetime()` | format vérifié |
| `zod::integer().min(1).max(100)` | entier borné |
| `zod::number().min(0.0)` | flottant borné |
| `zod::boolean()` | booléen |
| `zod::enumeration(&["utc", "local"])` | valeur parmi une liste |
| `zod::array(zod::string()).min(1).max(10)` | tableau borné |
| `zod::nullable(schéma)` | accepte `null` |
| `zod::describe("…", schéma)` | publie une description de champ |
| `zod::object().field(..).opt(..).strict()` | objet ; `.strict()` refuse l'inconnu |

### Les erreurs en un coup d'œil

| Code | Quand | Votre code a tourné ? |
|---|---|---|
| `-32602` + `issues` | arguments hors schéma | ❌ non |
| `isError: true` | le handler a renvoyé `Err(msg)` | ✅ oui |
| `-32601` | outil inconnu | ❌ non |
| `-32700` | JSON invalide | ❌ non |

---

## 🤝 Contribution

Les contributions sont les bienvenues ! Ouvrez une _issue_ pour discuter des
changements que vous souhaitez apporter, ou une _PR_ directement pour les
corrections simples (typos, exemples).

> 🔗 **LiteMCP** — [github.com/DeamonDev888/litemcp](https://github.com/DeamonDev888/litemcp) ·
> [crates.io/crates/litemcp](https://crates.io/crates/litemcp) — MIT OR Apache-2.0
