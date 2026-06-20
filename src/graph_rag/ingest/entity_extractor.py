"""Entity extraction from text using regex patterns and spaCy NER."""

import re
from typing import List, Optional

from graph_rag.models import Entity, EntityType
from graph_rag.utils.text_utils import parse_orig_tags

# Regex patterns for legal entities
LEGAL_ENTITY_PATTERNS = {
    EntityType.PARTY: [
        r"\b(?:Party\s+[A-Z]|Licensor|Licensee|Contractor|Subcontractor)\b",
        r"\b(?:the\s+)?(?:Buyer|Seller|Purchaser|Vendor)\b",
    ],
    EntityType.DATE: [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
        r"\b\d{4}-\d{2}-\d{2}\b",  # ISO dates
    ],
    EntityType.AMOUNT: [
        r"\$\d+(?:,\d{3})*(?:\.\d{2})?",
        r"\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|EUR|GBP|KWD)",
        r"\d+(?:,\d{3})*\s*(?:dollars?|euros?|pounds?)",
    ],
    EntityType.CLAUSE_REF: [
        r"\b(?:Article|Section|Clause|Paragraph)\s+\d+",
        r"\bArt\.\s+\d+",
        r"\bSec\.\s+\d+",
        r"\bCl\.\s+\d+",
    ],
    EntityType.LEGAL_TERM: [
        r"\b(?:Decree|Law|Regulation|Ordinance|Statute)\s+(?:No\.?\s+)?\d+",
        r"\b(?:Act|Bill|Resolution)\s+\d+",
    ],
}

# Try to import spaCy, but handle gracefully if not available
try:
    import spacy

    nlp = None

    def _load_spacy_model():
        """Load spaCy model lazily."""
        global nlp
        if nlp is None:
            try:
                nlp = spacy.load("en_core_web_sm")
            except OSError:
                # Model not installed, will use fallback
                pass
        return nlp

except ImportError:
    nlp = None

    def _load_spacy_model():
        """Fallback when spaCy not available."""
        return None


def extract_entities_from_text(
    text: str, chunk_id: Optional[str] = None
) -> List[Entity]:
    """Extract entities from text using hybrid approach.

    Args:
        text: Text to extract entities from
        chunk_id: Optional chunk ID for entity metadata

    Returns:
        List of Entity objects
    """
    entities = []

    # Extract using regex patterns
    for entity_type, patterns in LEGAL_ENTITY_PATTERNS.items():
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entity_text = match.group(0)
                # Parse <orig> tags if present
                display_text, original_name = parse_orig_tags(entity_text)
                entity = Entity(
                    id=f"{chunk_id}_{entity_type.value}_{len(entities)}"
                    if chunk_id
                    else f"{entity_type.value}_{len(entities)}",
                    text=display_text,
                    entity_type=entity_type,
                    canonical_form=display_text,
                    original_name=original_name,
                    metadata={"start": match.start(), "end": match.end()},
                )
                entities.append(entity)

    # Extract using spaCy NER if available
    spacy_model = _load_spacy_model()
    if spacy_model:
        doc = spacy_model(text)
        for ent in doc.ents:
            # Map spaCy labels to our entity types
            entity_type_map = {
                "PERSON": EntityType.PERSON,
                "ORG": EntityType.ORGANIZATION,
                "GPE": EntityType.LOCATION,
                "LOC": EntityType.LOCATION,
            }
            entity_type = entity_type_map.get(ent.label_)
            if entity_type:
                display_text, original_name = parse_orig_tags(ent.text)
                entity = Entity(
                    id=f"{chunk_id}_spacy_{len(entities)}"
                    if chunk_id
                    else f"spacy_{len(entities)}",
                    text=display_text,
                    entity_type=entity_type,
                    canonical_form=display_text,
                    original_name=original_name,
                    metadata={
                        "start": ent.start_char,
                        "end": ent.end_char,
                        "spacy_label": ent.label_,
                    },
                )
                entities.append(entity)
    else:
        # Fallback: extract capitalized phrases as potential entities
        capitalized_pattern = r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b"
        matches = re.finditer(capitalized_pattern, text)
        for match in matches:
            entity_text = match.group(0)
            # Skip common false positives
            if entity_text not in ["Article", "Section", "Clause", "Decree", "Law"]:
                display_text, original_name = parse_orig_tags(entity_text)
                entity = Entity(
                    id=f"{chunk_id}_fallback_{len(entities)}"
                    if chunk_id
                    else f"fallback_{len(entities)}",
                    text=display_text,
                    entity_type=EntityType.ORGANIZATION,  # Default assumption
                    canonical_form=display_text,
                    original_name=original_name,
                    metadata={"start": match.start(), "end": match.end()},
                )
                entities.append(entity)

    return entities

