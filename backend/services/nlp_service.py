
import re
from collections import Counter

import spacy
from bs4 import BeautifulSoup


nlp = spacy.load("en_core_web_sm")

ENTITY_TYPES = {
    "PERSON",
    "ORG",
    "GPE",
    "LOC",
    "NORP",
    "EVENT"
}


def clean_text(text):
    if not text:
        return ""

    text = BeautifulSoup(
        text, "html.parser"
    ).get_text(" ", strip=True)

    # Remove NewsAPI truncation markers.
    text = re.sub(
        r"\s*\[\+\d+\s+chars?\]\s*$",
        "",
        text
    )

    # Normalize whitespace.
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def process_text(text):
    cleaned = clean_text(text)

    if not cleaned:
        return {
            "cleaned_text": "",
            "word_count": 0,
            "tokens": [],
            "keywords": [],
            "entities": []
        }

    doc = nlp(cleaned)

    tokens = [
        token.lemma_.lower()
        for token in doc
        if token.is_alpha
        and not token.is_stop
        and len(token.text) > 2
    ]

    keyword_counts = Counter(tokens)

    keywords = [
        {
            "word": word,
            "frequency": count
        }
        for word, count in keyword_counts.most_common(15)
    ]

    entities = []
    seen = set()

    for ent in doc.ents:
        if ent.label_ not in ENTITY_TYPES:
            continue

        key = (ent.text.lower(), ent.label_)

        if key not in seen:
            entities.append({
                "text": ent.text,
                "label": ent.label_
            })
            seen.add(key)

    return {
        "cleaned_text": cleaned,
        "word_count": sum(
            1 for token in doc if token.is_alpha
        ),
        "tokens": tokens,
        "keywords": keywords,
        "entities": entities
    }
