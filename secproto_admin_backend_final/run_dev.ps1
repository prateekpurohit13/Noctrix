Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
if (-not $env:JWT_SECRET) { $env:JWT_SECRET = "dev_secret_change_me" }
if (-not $env:JWT_TTL_SECONDS) { $env:JWT_TTL_SECONDS = "86400" }
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
