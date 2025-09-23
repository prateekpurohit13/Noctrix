#!/usr/bin/env bash
set -e
python scripts/init_db.py
uvicorn app.main:app --port 8000
