import sys, os
from app.db import SessionLocal, Base, engine
from app.models import User
from app.security import hash_password

def main(username, password):
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        if db.query(User).filter_by(username=username).first():
            print("User exists")
            return
        u = User(username=username, password_hash=hash_password(password), role="Admin")
        db.add(u); db.commit()
        print("Admin created")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        username = os.getenv("ADMIN_USERNAME", "admin")
        password = os.getenv("ADMIN_PASSWORD", "Admin123")
        print(f"Using defaults: {username} / (hidden)")
        main(username, password)
    elif len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python -m scripts.create_admin [<username> <password>]")
        raise SystemExit(1)
