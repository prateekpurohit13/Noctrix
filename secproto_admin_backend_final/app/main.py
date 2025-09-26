from fastapi import FastAPI
from .routers import admin as admin_router
from .routers import auth as auth_router

app = FastAPI(title="SecProto Admin APIs (Final)", version="1.1.0")

app.include_router(auth_router.router)
app.include_router(admin_router.router)

@app.get("/healthz")
def healthz():
    return {"ok": True}
