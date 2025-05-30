# File: backend/search/management/commands/bulk_index.py
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterator

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from elasticsearch import Elasticsearch, helpers
from search.es import INDEX as DEFAULT_INDEX, MAPPING

DEFAULT_JSONL   = Path("/code/data/ssoar_docs.jsonl")
CHUNK           = 5_000          # docs per progress tick
MAX_FULLTEXT    = 1_000_000      # ES highlight offset limit


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def read_jsonl(path: Path) -> Iterator[dict]:
    """Yield dicts parsed from a JSONL file, trimming very long full_text."""
    with path.open(encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"⚠️  Line {n}: {exc}", file=sys.stderr)
                continue

            ft = rec.get("full_text")
            if isinstance(ft, str) and len(ft) > MAX_FULLTEXT:
                rec["full_text"] = ft[:MAX_FULLTEXT]

            yield rec


# --------------------------------------------------------------------------- #
# Management command
# --------------------------------------------------------------------------- #
class Command(BaseCommand):
    """
    django-admin bulk_index [--file F] [--index NAME] [--recreate]

    Streams a JSONL file into Elasticsearch without loading the whole file
    into memory.  Safe on large corpora.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "-f", "--file", type=Path, default=DEFAULT_JSONL,
            help=f"JSON Lines input (default: {DEFAULT_JSONL})"
        )
        parser.add_argument(
            "-i", "--index", default=DEFAULT_INDEX,
            help=f"Target index (default: {DEFAULT_INDEX})"
        )
        parser.add_argument(
            "--recreate", action="store_true",
            help="Drop the index first if it already exists"
        )

    # ------------------------------------------------------------------ #
    def handle(self, *args, **opts):
        jsonl   : Path = opts["file"]
        index   : str  = opts["index"]
        recreate: bool = opts["recreate"]

        if not jsonl.exists():
            raise CommandError(f"JSONL file not found: {jsonl}")

        es = Elasticsearch(settings.ES_HOST)

        # ── index lifecycle ────────────────────────────────────────── #
        if es.indices.exists(index=index):
            if not recreate:
                raise CommandError(
                    f"Index '{index}' already exists – use --recreate to overwrite."
                )
            self.stdout.write(f"Deleting index '{index}' …")
            es.indices.delete(index=index)

        self.stdout.write(f"Creating index '{index}' …")
        es.indices.create(index=index, body=MAPPING)

        # ── bulk import (streaming) ───────────────────────────────── #
        self.stdout.write(f"Streaming docs from {jsonl} …")
        success, failed = 0, 0

        def actions():
            for rec in read_jsonl(jsonl):
                yield {
                    "_op_type": "index",
                    "_index": index,
                    "_id": rec["id"],
                    "_source": rec,
                }

        try:
            for ok, _ in helpers.streaming_bulk(
                es,
                actions(),
                chunk_size      = CHUNK,
                raise_on_error  = False,
                request_timeout = 120,
            ):
                if ok:
                    success += 1
                else:
                    failed += 1
                if (success + failed) % CHUNK == 0:
                    self.stdout.write(f"  indexed {success:,}   failed {failed:,}")
        except Exception as exc:                       # generic catch-all from client
            raise CommandError(f"Elasticsearch error: {exc}") from exc

        es.indices.refresh(index=index)
        total = es.count(index=index)["count"]

        self.stdout.write(
            self.style.SUCCESS(
                f"✔ Finished. Success: {success:,} – Failed: {failed:,} – "
                f"Total in index: {total:,}"
            )
        )