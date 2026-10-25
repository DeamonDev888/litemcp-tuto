//! Mon premier serveur MCP — le code complet du tutoriel LiteMCP.
//!
//! `cargo run`                      → http://127.0.0.1:8080/mcp
//! `cargo run -- 127.0.0.1:8180`    → adresse personnalisée (optionnel)
//!
//! Quatre outils :
//! - `hello`   (closure brute)        salue quelqu'un — valeur par défaut ;
//! - `analyze` (tool_parse + zod)     statistiques de texte, arguments typés ;
//! - `divide`  (closure brute)        division par zéro → `isError: true` ;
//! - `counter` (état partagé)         compteur qui survit aux connexions.

use litemcp::prelude::*;
use serde::Deserialize;
use serde_json::json;
use std::sync::Arc;
use std::sync::atomic::{AtomicU64, Ordering};

// Les arguments de « analyze », remplis automatiquement après validation.
#[derive(Deserialize)]
struct AnalyzeArgs {
    text: String,            // requis : 1 à 10 000 caractères (voir le schéma)
    uppercase: Option<bool>, // optionnel — porte une valeur par défaut (false)
}

fn main() -> std::io::Result<()> {
    // Adresse : celle donnée en 1er argument, sinon 127.0.0.1:8080.
    let addr = std::env::args()
        .nth(1)
        .unwrap_or_else(|| "127.0.0.1:8080".to_string());
    println!("Mon premier MCP écoute sur http://{addr}/mcp");

    // L'état partagé du compteur : il vit dans le processus,
    // partagé entre les threads de connexion via Arc<AtomicU64>.
    let counter = Arc::new(AtomicU64::new(0));
    let counter_state = Arc::clone(&counter);

    ServerBuilder::new("mon-premier-mcp", "0.1.0")
        // Outil 1 — le plus simple : la closure lit le JSON elle-même.
        .tool(
            "hello",
            "Dit bonjour à quelqu'un",
            |args| {
                let name = args
                    .get("name")
                    .and_then(|v| v.as_str())
                    .unwrap_or("monde");
                Ok(json!({ "message": format!("Bonjour, {name} !") }))
            },
        )
        // Outil 2 — schéma zod : arguments validés AVANT le handler,
        // puis désérialisés dans AnalyzeArgs (args.text est un vrai String).
        // `uppercase` porte une valeur par défaut : le champ est optionnel,
        // la valeur est publiée dans le schéma ET injectée si elle manque.
        .tool_parse(
            "analyze",
            "Statistiques d'un texte (mots, caractères, mot le plus long)",
            zod::object()
                .field("text", zod::string().min(1).max(10_000))
                .opt("uppercase", zod::boolean().default(false))
                .strict(),
            |args: AnalyzeArgs| {
                let longest = args
                    .text
                    .split_whitespace()
                    .max_by_key(|w| w.chars().count())
                    .unwrap_or("");
                let mut result = json!({
                    "words": args.text.split_whitespace().count(),
                    "chars": args.text.chars().count(),
                    "longest": longest,
                });
                if args.uppercase.unwrap_or(false) {
                    result["shout"] = json!(args.text.to_uppercase());
                }
                Ok(result)
            },
        )
        // Outil 3 — l'erreur métier : Err(...) devient isError: true,
        // le serveur continue de tourner.
        .tool("divide", "Divise a par b (erreur si b vaut 0)", |args| {
            let a = args
                .get("a")
                .and_then(|v| v.as_f64())
                .ok_or("a manquant ou pas un nombre")?;
            let b = args
                .get("b")
                .and_then(|v| v.as_f64())
                .ok_or("b manquant ou pas un nombre")?;
            if b == 0.0 {
                return Err("division par zéro".into());
            }
            Ok(json!({ "quotient": a / b }))
        })
        // Outil 4 — un outil avec mémoire : chaque appel incrémente le compteur.
        .tool(
            "counter",
            "Incrémente et renvoie le compteur interne",
            move |_args| {
                let count = counter_state.fetch_add(1, Ordering::SeqCst) + 1;
                Ok(json!({ "count": count }))
            },
        )
        // Annotations : métadonnées honnêtes publiées dans tools/list.
        .annotate(
            "hello",
            ToolAnnotations::new()
                .title("Bonjour")
                .read_only(true)
                .idempotent(true),
        )
        .annotate("analyze", ToolAnnotations::new().title("Analyse").read_only(true))
        .annotate("divide", ToolAnnotations::new().title("Division").read_only(true))
        .annotate("counter", ToolAnnotations::new().title("Compteur"))
        .bind(&addr)?
        .serve()
}
