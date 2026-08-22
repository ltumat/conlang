"""Import conjugated verb forms from Lexique4.tsv into lexical_forms.

This script reads the ``Lexique4.tsv`` via the shared reader in
``sentence_loader`` and creates ``LexicalForm`` records with
``form_type = 'conjugation'`` / ``'past_participle'`` / ``'infinitive'``
and structured ``features`` JSON.

Run after the initial database population::

    python -m app.lexicon.import_conjugations

It is idempotent — it skips existing (lexical_item_id, form_type, form) tuples.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocal
from app.lexicon.embedding_config import load_config
from app.lexicon.sentence_loader import (
    parse_info_ver,
    read_lexique_entries,
    verb_form_type_from_features,
)
from app.models import LexicalForm, LexicalItem

BATCH_SIZE = 5_000


def import_conjugations(lexique_path: str | Path) -> dict[str, int]:
    """Parse Lexique4.tsv and create conjugation LexicalForm records."""
    with SessionLocal() as session:
        # ── Build lemma → LexicalItem lookup ──────────────────────────
        items = (
            session.execute(select(LexicalItem).order_by(LexicalItem.id))
            .scalars()
            .all()
        )
        item_by_lemma: dict[str, list[LexicalItem]] = {}
        for item in items:
            item_by_lemma.setdefault(item.word.casefold(), []).append(item)

        existing = (
            session.execute(select(LexicalForm)).scalars().all()
        )
        existing_keys: set[tuple[int, str, str]] = {
            (f.lexical_item_id, f.form_type, f.form) for f in existing
        }

        print(
            f"Found {len(items):,} lexical items, "
            f"{len(existing):,} existing forms (idempotency keys)."
        )

        # ── Read Lexique via shared reader ────────────────────────────
        rows = read_lexique_entries(lexique_path)
        print(f"Read {len(rows):,} rows from Lexique.")

        # ── Create forms ──────────────────────────────────────────────
        new_forms: list[LexicalForm] = []
        skipped = 0
        merged: dict[tuple[int, str, str], list[dict]] = {}

        for row in rows:
            if row["5_Cgram"] not in ("VER", "AUX"):
                continue
            if not row["conjugation_tags"]:
                continue

            candidates = item_by_lemma.get(row["4_Lemme"].casefold(), [])
            if not candidates:
                skipped += 1
                continue

            for features in row["conjugation_tags"]:
                form_type = verb_form_type_from_features(features)
                for item in candidates:
                    key = (item.id, form_type, row["1_Mot"])
                    if key in existing_keys:
                        continue
                    merged.setdefault(key, []).append(features)

        # Convert merged features into LexicalForm rows
        for (item_id, form_type, surface), feats_list in merged.items():
            if len(feats_list) == 1:
                features = feats_list[0]
            else:
                unique_feats = [
                    dict(t)
                    for t in {tuple(sorted(f.items())) for f in feats_list}
                ]
                features = unique_feats if len(unique_feats) > 1 else unique_feats[0]
            new_forms.append(
                LexicalForm(
                    lexical_item_id=item_id,
                    form=surface,
                    form_type=form_type,
                    features=features,
                )
            )

        # ── Batch insert ──────────────────────────────────────────────
        total = len(new_forms)
        for i in range(0, total, BATCH_SIZE):
            session.add_all(new_forms[i : i + BATCH_SIZE])
            session.flush()
            print(
                f"  Inserted {min(i + BATCH_SIZE, total):,}/{total:,} "
                f"conjugation forms..."
            )

        session.commit()
        print(
            f"Done: {total:,} new conjugation forms, "
            f"{skipped:,} rows with no matching lexical item."
        )
        return {"new_conjugation_forms": total, "skipped_rows": skipped}


def main() -> None:
    config = load_config()
    parser = argparse.ArgumentParser(
        description="Import conjugated verb forms from Lexique"
    )
    parser.add_argument("--lexique-file", type=Path, default=config.lexique_file)
    args = parser.parse_args()
    import_conjugations(args.lexique_file)


if __name__ == "__main__":
    main()