from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
from sqlalchemy import select
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


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def get_vector_rows(path: str | Path) -> np.ndarray:
    vectors = np.load(path)
    if vectors.ndim != 2:
        raise ValueError(f"Expected a 2D array in {path}, got shape {vectors.shape}")
    return vectors


def find_embedding(
    session: Session,
    model_name: str,
    content_type: str,
    target_field: str,
    target_id: int,
) -> Embedding | None:
    target_column = getattr(Embedding, target_field)
    return session.scalar(
        select(Embedding).where(
            Embedding.model_name == model_name,
            Embedding.content_type == content_type,
            target_column == target_id,
        )
    )


def save_embedding(
    session: Session,
    model_name: str,
    dimensions: int,
    content_type: str,
    target_field: str,
    target_id: int,
    vector: np.ndarray,
) -> None:
    values = vector.astype(float).tolist()
    embedding = find_embedding(
        session, model_name, content_type, target_field, target_id
    )
    if embedding is None:
        embedding = Embedding(
            model_name=model_name,
            content_type=content_type,
            dimensions=dimensions,
            embedding=values,
        )
        setattr(embedding, target_field, target_id)
        session.add(embedding)
    else:
        embedding.dimensions = dimensions
        embedding.embedding = values


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

    counts = {"word": 0, "sense": 0, "sentence": 0, "sentence_pair": 0}
    word_items: dict[int, LexicalItem] = {}
    for record in metadata["word_records"]:
        item = session.scalar(
            select(LexicalItem).where(
                LexicalItem.source_entry_id == record["entry_id"]
            )
        )
        if item is not None:
            word_items[record["entry_id"]] = item

    for index, record in enumerate(metadata["word_records"]):
        item = word_items.get(record["entry_id"])
        if item is not None:
            save_embedding(
                session,
                model_name,
                dimensions,
                "word",
                "lexical_item_id",
                int(item.id),
                words[index],
            )
            counts["word"] += 1

    for index, record in enumerate(metadata["sense_records"]):
        item = word_items.get(record["entry_id"])
        if item is None:
            continue
        sense = session.scalar(
            select(LexicalSense).where(
                LexicalSense.lexical_item_id == item.id,
                LexicalSense.sense_number == record["sense_number"],
            )
        )
        if sense is not None:
            save_embedding(
                session,
                model_name,
                dimensions,
                "sense",
                "sense_id",
                int(sense.id),
                senses[index],
            )
            counts["sense"] += 1

    sentence_ids: dict[str, int] = {}
    for record in metadata["sentence_records"]:
        sentence = session.scalar(
            select(Sentence).where(Sentence.text == record["text"])
        )
        if sentence is not None:
            sentence_ids[record["pair_id"]] = sentence.id

    for index, record in enumerate(metadata["sentence_records"]):
        sentence_id = sentence_ids.get(record["pair_id"])
        if sentence_id is None:
            continue
        save_embedding(
            session,
            model_name,
            dimensions,
            "sentence",
            "sentence_id",
            int(sentence_id),
            sentences[index],
        )
        counts["sentence"] += 1

        translation = session.scalar(
            select(SentenceTranslation).where(
                SentenceTranslation.sentence_id == sentence_id,
                SentenceTranslation.translation == record["translation"],
            )
        )
        if translation is not None:
            save_embedding(
                session,
                model_name,
                dimensions,
                "sentence_pair",
                "sentence_translation_id",
                int(translation.id),
                sentence_pairs[index],
            )
            counts["sentence_pair"] += 1

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
