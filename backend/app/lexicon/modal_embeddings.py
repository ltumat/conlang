from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import modal

from app.lexicon.embedding_config import (
    EMBEDDING_DIMENSIONS,
    MANIFEST_FILE,
    METADATA_FILE,
    SENSES_FILE,
    SENTENCE_PAIRS_FILE,
    SENTENCES_FILE,
    WORDS_FILE,
    load_config,
)
from app.lexicon.sentence_loader import load_lexique_forms, load_sentence_pairs
from app.lexicon.tei_loader import load_tei_entries

CONFIG = load_config()
MODELS = {
    CONFIG.model: {"dimensions": EMBEDDING_DIMENSIONS, "e5_prefix": False}
}

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("sentence-transformers", "torch", "numpy", "python-dotenv")
    .env(
        {
            "EMBEDDING_MODEL": CONFIG.model,
            "EMBEDDING_DIMENSIONS": str(EMBEDDING_DIMENSIONS),
            "MODAL_HF_SECRET_NAME": CONFIG.secret_name,
            "MODAL_VOLUME_NAME": CONFIG.volume_name,
            "FRENCH_TEI_FILE": CONFIG.tei_file,
            "FRENCH_SENTENCES_FILE": CONFIG.sentences_file,
            "FRENCH_LEXIQUE_FILE": CONFIG.lexique_file,
        }
    )
    .add_local_python_source("app")
)
app = modal.App("conlang-french-embeddings")
embeddings_volume = modal.Volume.from_name(
    CONFIG.volume_name, create_if_missing=True
)


def _sense_records(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for entry in entries:
        word = entry.get("word")
        if not word:
            continue
        for index, sense in enumerate(entry.get("senses", []), start=1):
            translations = sense.get("translations", [])
            if translations:
                records.append(
                    {
                        "entry_id": entry["id"],
                        "sense_number": sense.get("number", index),
                        "word": word,
                        "translation": translations[0],
                        "text": f"{word} — {translations[0]}",
                    }
                )
    return records


def _sentence_records(sentences: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "pair_id": sentence["pair_id"],
            "sentence_id": sentence["sentence_id"],
            "text": sentence["text"],
            "translation": sentence["translation"],
            "words": sentence.get("words", []),
        }
        for sentence in sentences
    ]


@app.function(
    image=image,
    gpu="A10G",
    timeout=7200,
    volumes={"/output": embeddings_volume},
    secrets=[modal.Secret.from_name(CONFIG.secret_name)],
)
def embed_all(
    entries: list[dict[str, Any]],
    sentences: list[dict[str, Any]],
    batch_size: int = 64,
) -> dict[str, Any]:
    """Compute all current Qwen representations and save them to the volume."""
    import numpy as np
    from sentence_transformers import SentenceTransformer

    word_records = [
        {"entry_id": entry["id"], "word": entry["word"], "text": entry["word"]}
        for entry in entries
        if entry.get("word")
    ]
    sense_records = _sense_records(entries)
    sentence_records = _sentence_records(sentences)
    metadata = {
        "word_records": word_records,
        "sense_records": sense_records,
        "sentence_records": sentence_records,
        "models": MODELS,
    }
    Path(f"/output/{METADATA_FILE}").write_text(
        json.dumps(metadata, ensure_ascii=False), encoding="utf-8"
    )

    model = SentenceTransformer(CONFIG.model)
    dimensions = model.get_embedding_dimension()
    if dimensions != EMBEDDING_DIMENSIONS:
        raise ValueError(
            f"{CONFIG.model} returned {dimensions} dimensions; "
            f"expected {EMBEDDING_DIMENSIONS}"
        )

    def encode(texts: list[str]) -> Any:
        return model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

    word_vectors = encode([record["text"] for record in word_records])
    sense_vectors = encode([record["text"] for record in sense_records])
    sentence_vectors = encode([record["text"] for record in sentence_records])
    pair_vectors = encode(
        [
            f"French: {record['text']}\nEnglish: {record['translation']}"
            for record in sentence_records
        ]
    )

    np.save(f"/output/{WORDS_FILE}", word_vectors)
    np.save(f"/output/{SENSES_FILE}", sense_vectors)
    np.save(f"/output/{SENTENCES_FILE}", sentence_vectors)
    np.save(f"/output/{SENTENCE_PAIRS_FILE}", pair_vectors)

    manifest = {
        "model": CONFIG.model,
        "dimensions": EMBEDDING_DIMENSIONS,
        "files": {
            "metadata": METADATA_FILE,
            "manifest": MANIFEST_FILE,
            "words": WORDS_FILE,
            "senses": SENSES_FILE,
            "sentences": SENTENCES_FILE,
            "sentence_pairs": SENTENCE_PAIRS_FILE,
        },
        "word_count": len(word_records),
        "sense_count": len(sense_records),
        "sentence_count": len(sentence_records),
        "sentence_text_format": "French sentence only",
        "sentence_pair_text_format": "French: sentence\\nEnglish: translation",
    }
    Path(f"/output/{MANIFEST_FILE}").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    embeddings_volume.commit()
    return manifest


@app.local_entrypoint()
def main(
    batch_size: int = 64,
) -> None:
    """Parse configured local files, embed remotely, and persist outputs."""
    entries = load_tei_entries(CONFIG.tei_file)
    forms = load_lexique_forms(CONFIG.lexique_file)
    sentences = load_sentence_pairs(CONFIG.sentences_file, forms)
    manifest = embed_all.remote(entries, sentences, batch_size=batch_size)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
