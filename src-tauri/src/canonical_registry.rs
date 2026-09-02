use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::{fs, path::PathBuf};

const REGISTRY_ROOT: &str = r"G:\Vertex_Project\Development\vertex_canonical_registry";

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CanonicalCard {
    pub card_id: String,
    pub formal_name: String,
    #[serde(default)]
    pub abbreviation: String,
    #[serde(default)]
    pub aliases: Vec<String>,
    #[serde(default)]
    pub summary: String,
    #[serde(default)]
    pub function: String,
    #[serde(default)]
    pub description: String,
    pub status: String,
    #[serde(default = "default_importance")]
    pub importance: String,
    #[serde(default)]
    pub scope: String,
    #[serde(default)]
    pub category: String,
    #[serde(default)]
    pub origin: String,
    #[serde(default)]
    pub related: Vec<String>,
    #[serde(default)]
    pub supersedes: Vec<String>,
    #[serde(default)]
    pub replaced_by: Vec<String>,
    #[serde(default)]
    pub flavor_badge: String,
    #[serde(default)]
    pub notes: String,
    #[serde(default)]
    pub adopted_by: String,
    #[serde(default)]
    pub created_at: String,
    #[serde(default)]
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct RegistrySnapshot {
    pub source: &'static str,
    pub cards: Vec<CanonicalCard>,
}

fn default_importance() -> String {
    "NORMAL".to_string()
}

fn root() -> PathBuf {
    PathBuf::from(REGISTRY_ROOT)
}

fn cards_path() -> PathBuf {
    root().join("data").join("cards.json")
}

fn languages_dir() -> PathBuf {
    root().join("languages")
}

fn ensure_registry() -> Result<(), String> {
    fs::create_dir_all(root().join("data")).map_err(|e| e.to_string())?;
    fs::create_dir_all(languages_dir()).map_err(|e| e.to_string())?;

    let cards = cards_path();
    if !cards.exists() {
        fs::write(&cards, b"[]\n").map_err(|e| e.to_string())?;
    }
    Ok(())
}

fn validate_card(card: &CanonicalCard) -> Result<(), String> {
    if card.card_id.trim().is_empty() {
        return Err("card_id is required".to_string());
    }
    if card.formal_name.trim().is_empty() {
        return Err("formal_name is required".to_string());
    }
    if !matches!(
        card.status.as_str(),
        "IDEA" | "CANDIDATE" | "ADOPTED" | "DEPRECATED"
    ) {
        return Err(format!("unsupported status: {}", card.status));
    }
    if !matches!(
        card.importance.as_str(),
        "NORMAL" | "IMPORTANT" | "CRITICAL"
    ) {
        return Err(format!("unsupported importance: {}", card.importance));
    }
    Ok(())
}

fn read_cards() -> Result<Vec<CanonicalCard>, String> {
    ensure_registry()?;
    let raw = fs::read_to_string(cards_path()).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

fn write_cards(cards: &[CanonicalCard]) -> Result<(), String> {
    ensure_registry()?;
    let encoded = serde_json::to_string_pretty(cards).map_err(|e| e.to_string())?;
    let target = cards_path();
    let temp = target.with_extension("json.pending");
    fs::write(&temp, format!("{encoded}\n")).map_err(|e| e.to_string())?;

    if target.exists() {
        fs::remove_file(&target).map_err(|e| e.to_string())?;
    }
    fs::rename(&temp, &target).map_err(|e| e.to_string())
}

fn language_path(language: &str) -> Result<PathBuf, String> {
    let clean = language.trim();
    if clean.is_empty() || clean.contains('/') || clean.contains('\\') || clean.contains("..") {
        return Err("invalid language id".to_string());
    }

    Ok(languages_dir().join(format!("{clean}.json")))
}

#[tauri::command]
pub fn canonical_registry_list() -> Result<RegistrySnapshot, String> {
    let mut cards = read_cards()?;
    cards.sort_by(|a, b| {
        a.formal_name
            .to_lowercase()
            .cmp(&b.formal_name.to_lowercase())
    });

    Ok(RegistrySnapshot {
        source: "VERTEX_CANONICAL_REGISTRY",
        cards,
    })
}

#[tauri::command]
pub fn canonical_registry_upsert(card: CanonicalCard) -> Result<RegistrySnapshot, String> {
    validate_card(&card)?;
    let mut cards = read_cards()?;

    if let Some(existing) = cards.iter_mut().find(|item| item.card_id == card.card_id) {
        *existing = card;
    } else {
        cards.push(card);
    }

    write_cards(&cards)?;
    canonical_registry_list()
}

#[tauri::command]
pub fn canonical_registry_delete(card_id: String) -> Result<RegistrySnapshot, String> {
    let id = card_id.trim();
    if id.is_empty() {
        return Err("card_id is required".to_string());
    }

    let mut cards = read_cards()?;
    cards.retain(|card| card.card_id != id);
    write_cards(&cards)?;
    canonical_registry_list()
}

#[tauri::command]
pub fn canonical_registry_language_pack(language: String) -> Result<Value, String> {
    ensure_registry()?;
    let path = language_path(&language)?;
    if !path.exists() {
        return Err(format!("language pack not found: {}", path.display()));
    }

    let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&raw).map_err(|e| e.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn valid_statuses_are_stable_machine_semantics() {
        for status in ["IDEA", "CANDIDATE", "ADOPTED", "DEPRECATED"] {
            let card = CanonicalCard {
                card_id: "x".into(),
                formal_name: "X".into(),
                abbreviation: String::new(),
                aliases: vec![],
                summary: String::new(),
                function: String::new(),
                description: String::new(),
                status: status.into(),
                importance: "NORMAL".into(),
                scope: String::new(),
                category: String::new(),
                origin: String::new(),
                related: vec![],
                supersedes: vec![],
                replaced_by: vec![],
                flavor_badge: String::new(),
                notes: String::new(),
                adopted_by: String::new(),
                created_at: String::new(),
                updated_at: String::new(),
            };
            assert!(validate_card(&card).is_ok());
        }
    }

    #[test]
    fn language_id_cannot_escape_registry() {
        assert!(language_path("../secret").is_err());
        assert!(language_path(r"..\secret").is_err());
        assert!(language_path("vertex-ja").is_ok());
    }

    #[test]
    fn card_requires_formal_name() {
        let card = CanonicalCard {
            card_id: "x".into(),
            formal_name: String::new(),
            abbreviation: String::new(),
            aliases: vec![],
            summary: String::new(),
            function: String::new(),
            description: String::new(),
            status: "ADOPTED".into(),
            importance: "NORMAL".into(),
            scope: String::new(),
            category: String::new(),
            origin: String::new(),
            related: vec![],
            supersedes: vec![],
            replaced_by: vec![],
            flavor_badge: String::new(),
            notes: String::new(),
            adopted_by: String::new(),
            created_at: String::new(),
            updated_at: String::new(),
        };
        assert!(validate_card(&card).is_err());
    }
}
