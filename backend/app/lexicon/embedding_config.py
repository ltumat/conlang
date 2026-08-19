from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

# Public, stable output names.
METADATA_FILE = "metadata.json"
MANIFEST_FILE = "models.json"
WORDS_FILE = "word_embeddings.npy"
SENSES_FILE = "sense_embeddings.npy"
SENTENCES_FILE = "sentence_embeddings.npy"
SENTENCE_PAIRS_FILE = "sentence_pair_embeddings.npy"


@dataclass(frozen=True)
class PrivateConfig:
    model: str
    dimensions: int
    secret_name: str
    volume_name: str
    tei_file: str
    sentences_file: str
    lexique_file: str


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing {name}; add it to backend/.env")
    return value


def embedding_dimensions() -> int:
    return int(_required("EMBEDDING_DIMENSIONS"))


def load_config() -> PrivateConfig:
    return PrivateConfig(
        model=_required("EMBEDDING_MODEL"),
        dimensions=embedding_dimensions(),
        secret_name=_required("MODAL_HF_SECRET_NAME"),
        volume_name=os.getenv("MODAL_VOLUME_NAME", "conlang-french-embeddings"),
        tei_file=_required("FRENCH_TEI_FILE"),
        sentences_file=_required("FRENCH_SENTENCES_FILE"),
        lexique_file=_required("FRENCH_LEXIQUE_FILE"),
    )
