from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.lexicon.embedding_config import (
    MANIFEST_FILE,
    METADATA_FILE,
    SENSES_FILE,
    SENTENCE_PAIRS_FILE,
    SENTENCES_FILE,
    WORDS_FILE,
    load_config,
)
from app.models import (
    Embedding,
    LexicalItem,
    LexicalSense,
    Sentence,
    SentenceTranslation,
)

BATCH_SIZE = 5000


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def get_vector_rows(path: str | Path) -> np.ndarray:
    vectors = np.load(path)
    if vectors.ndim != 2:
        raise ValueError(f"Expected a 2D array in {path}, got shape {vectors.shape}")
    return vectors


def import_embeddings(
    session: Session,
    metadata: dict[str, Any],
    manifest: dict[str, Any],
    words: np.ndarray,
    senses: np.ndarray,
    sentences: np.ndarray,
    sentence_pairs: np.ndarray,
) -> dict[str, int]:
    model_name = manifest["model"]
    dimensions = int(manifest["dimensions"])

    # Validate shapes
    expected = {
        "words": (words, metadata["word_records"]),
        "senses": (senses, metadata["sense_records"]),
        "sentences": (sentences, metadata["sentence_records"]),
        "sentence_pairs": (sentence_pairs, metadata["sentence_records"]),
    }
    for name, (vectors, records) in expected.items():
        if len(vectors) != len(records):
            raise ValueError(
                f"{name}: {len(vectors)} vectors but {len(records)} metadata records"
            )
        if vectors.shape[1] != dimensions:
            raise ValueError(
                f"{name}: vectors have {vectors.shape[1]} dimensions; "
                f"manifest expects {dimensions}"
            )

    # ── Bulk lookup: map external IDs to DB IDs ──────────────────────
    items = session.scalars(select(LexicalItem)).all()
    word_by_entry_id: dict[int, LexicalItem] = {
        item.source_entry_id: item for item in items if item.source_entry_id is not None
    }

    senses_by_item: dict[tuple[int, int], LexicalSense] = {}
    for sense in session.scalars(select(LexicalSense)).all():
        senses_by_item[(sense.lexical_item_id, sense.sense_number)] = sense

    all_sentences = session.scalars(select(Sentence)).all()
    sentence_by_text: dict[str, Sentence] = {s.text: s for s in all_sentences}

    all_translations = session.scalars(select(SentenceTranslation)).all()
    translation_by_key: dict[tuple[int, str], SentenceTranslation] = {
        (t.sentence_id, t.translation): t for t in all_translations
    }

    # ── Delete existing embeddings for this model ────────────────────
    session.execute(delete(Embedding).where(Embedding.model_name == model_name))
    session.flush()

    # ── Build and insert in batches ──────────────────────────────────
    counts: dict[str, int] = {"word": 0, "sense": 0, "sentence": 0, "sentence_pair": 0}

    def _vector(values: np.ndarray, index: int) -> list[float]:
        """Convert a single numpy row to Python list, avoiding holding all at once."""
        return values[index].astype(float).tolist()

    def _flush(batch: list[dict[str, Any]]) -> None:
        if not batch:
            return
        session.execute(insert(Embedding), batch)
        session.flush()
        batch.clear()

    batch: list[dict[str, Any]] = []

    # Words
    for index, record in enumerate(metadata["word_records"]):
        item = word_by_entry_id.get(record["entry_id"])
        if item is None:
            continue
        batch.append(
            {
                "model_name": model_name,
                "content_type": "word",
                "dimensions": dimensions,
                "lexical_item_id": item.id,
                "embedding": _vector(words, index),
            }
        )
        counts["word"] += 1
        if len(batch) >= BATCH_SIZE:
            _flush(batch)
    _flush(batch)

    # Senses
    for index, record in enumerate(metadata["sense_records"]):
        item = word_by_entry_id.get(record["entry_id"])
        if item is None:
            continue
        sense = senses_by_item.get((item.id, record["sense_number"]))
        if sense is None:
            continue
        batch.append(
            {
                "model_name": model_name,
                "content_type": "sense",
                "dimensions": dimensions,
                "sense_id": sense.id,
                "embedding": _vector(senses, index),
            }
        )
        counts["sense"] += 1
        if len(batch) >= BATCH_SIZE:
            _flush(batch)
    _flush(batch)

    # Sentences + sentence pairs
    for index, record in enumerate(metadata["sentence_records"]):
        sentence = sentence_by_text.get(record["text"])
        if sentence is None:
            continue
        batch.append(
            {
                "model_name": model_name,
                "content_type": "sentence",
                "dimensions": dimensions,
                "sentence_id": sentence.id,
                "embedding": _vector(sentences, index),
            }
        )
        counts["sentence"] += 1
        if len(batch) >= BATCH_SIZE:
            _flush(batch)

        translation = translation_by_key.get(
            (sentence.id, record["translation"])
        )
        if translation is None:
            continue
        batch.append(
            {
                "model_name": model_name,
                "content_type": "sentence_pair",
                "dimensions": dimensions,
                "sentence_translation_id": translation.id,
                "embedding": _vector(sentence_pairs, index),
            }
        )
        counts["sentence_pair"] += 1
        if len(batch) >= BATCH_SIZE:
            _flush(batch)
    _flush(batch)

    session.commit()
    return counts


def download_modal_outputs(directory: Path) -> dict[str, Path]:
    config = load_config()
    directory.mkdir(parents=True, exist_ok=True)
    filenames = {
        "metadata": METADATA_FILE,
        "manifest": MANIFEST_FILE,
        "words": WORDS_FILE,
        "senses": SENSES_FILE,
        "sentences": SENTENCES_FILE,
        "sentence_pairs": SENTENCE_PAIRS_FILE,
    }
    modal_command = shutil.which("modal") or "uv"
    for filename in filenames.values():
        destination = directory / filename
        command = (
            [modal_command, "run", "modal", "volume", "get"]
            if modal_command == "uv"
            else [modal_command, "volume", "get"]
        )
        command.extend(
            [config.volume_name, filename, str(destination), "--force"]
        )
        subprocess.run(command, check=True, cwd=Path.cwd())
    return {key: directory / filename for key, filename in filenames.items()}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download and import Modal embeddings into PostgreSQL"
    )
    parser.add_argument("--download-dir", type=Path, default=Path("data/embeddings"))
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--words", type=Path)
    parser.add_argument("--senses", type=Path)
    parser.add_argument("--sentences", type=Path)
    parser.add_argument("--sentence-pairs", type=Path)
    args = parser.parse_args()

    downloaded = download_modal_outputs(args.download_dir)
    paths = {
        "metadata": args.metadata or downloaded["metadata"],
        "manifest": args.manifest or downloaded["manifest"],
        "words": args.words or downloaded["words"],
        "senses": args.senses or downloaded["senses"],
        "sentences": args.sentences or downloaded["sentences"],
        "sentence_pairs": args.sentence_pairs or downloaded["sentence_pairs"],
    }
    metadata = load_json(paths["metadata"])
    manifest = load_json(paths["manifest"])
    with SessionLocal() as session:
        counts = import_embeddings(
            session,
            metadata,
            manifest,
            get_vector_rows(paths["words"]),
            get_vector_rows(paths["senses"]),
            get_vector_rows(paths["sentences"]),
            get_vector_rows(paths["sentence_pairs"]),
        )
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()