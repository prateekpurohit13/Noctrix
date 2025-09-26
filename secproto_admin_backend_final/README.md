# SecProto Admin Backend (Final)

Bulletproof build:
- Uses **bcrypt** directly with pre-slicing to 72 bytes → no more bcrypt length errors.
- SQLite by default; Postgres optional via `DATABASE_URL`.
- No-arg admin seeder for fast start.

## Quickstart (Windows PowerShell)

1) Unzip and open PowerShell here
2) Venv + deps:
```
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
3) Seed first admin (defaults: `admin` / `Admin123`):
```
python -m scripts.create_admin
```
4) Run server:
```
.un_dev.ps1
```
Open http://localhost:8000/docs
