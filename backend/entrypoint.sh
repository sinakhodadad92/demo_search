#!/bin/sh
set -e

# ── wait until Elasticsearch answers ───────────────────────────────
until curl -s -o /dev/null "$ES_HOST"; do
  echo "💤  waiting for Elasticsearch at $ES_HOST …"
  sleep 2
done
echo "🚀 Elasticsearch is up"

# ── Django housekeeping ───────────────────────────────────────────
python manage.py migrate --noinput

# ── (re-)create the search index and stream-import the JSONL file ─
python manage.py bulk_index \
        --file /code/data/ssoar_docs.jsonl \
        --index ssoar_demo \
        --recreate

# ── run the web server ────────────────────────────────────────────
exec gunicorn backend.wsgi:application --bind 0.0.0.0:8000