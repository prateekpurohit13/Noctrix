@echo off
python scripts\init_db.py
uvicorn app.main:app --port 8000
