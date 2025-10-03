import os
import asyncio
import json
import time
import base64
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, BackgroundTasks, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from passlib.hash import bcrypt
import jwt
import uuid
from bson import ObjectId
from dotenv import load_dotenv
load_dotenv()
from src.security.crypto import encrypt_at_rest, decrypt_at_rest
from src.security.kms import get_dek
from src.security.rbac import allowed
from src.security.audit import append_audit
from src.document_processor.main import process_input
from src.multi_agent_system import AgentOrchestrator
from src.rag.service import get_rag_retriever
from src.multi_agent_system.agents import (
    DocumentUnderstandingAgent, AnalysisAgent,
    SecurityAssessmentAgent, AnonymizationAgent, ReportingAgent
)
from src.reporting.utils import export_pdf_from_md
from pydantic import BaseModel
from collections import defaultdict

class LoginRequest(BaseModel):
    username: str
    password: str

POSTGRES_DSN = f"dbname='{os.getenv('POSTGRES_DB')}' user='{os.getenv('POSTGRES_USER')}' password='{os.getenv('POSTGRES_PASSWORD')}' host='{os.getenv('POSTGRES_HOST')}' port='{os.getenv('POSTGRES_PORT')}'"
TENANT_ID = os.getenv("TENANT_ID", "demo")
JWT_ISSUER = os.getenv("JWT_ISSUER", "secproto")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "secproto-users")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "0") == "1"
JWT_ALG = "HS256"
JWT_SECRET = base64.b64decode(os.getenv("KEK_BASE64"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.mongodb_client = AsyncIOMotorClient(os.environ["MONGO_URI"])
    app.mongodb = app.mongodb_client[os.environ["MONGO_DB_NAME"]]
    print("Connected to MongoDB.")
    yield
    app.mongodb_client.close()
    print("MongoDB connection closed.")

app = FastAPI(
    title="Noctrix AI - Secure File Cleansing and Analysis Service",
    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_postgres_conn():
    return psycopg2.connect(POSTGRES_DSN)

class Job(BaseModel):
    job_id: str
    asset_id: int
    file_name: str
    status: str = "pending"
    message: str = "Job has been queued."
class LoginRequest(BaseModel): username: str; password: str
class UserCreateRequest(BaseModel): username: str; password: str; role: str
class ChangePasswordRequest(BaseModel): old_password: str; new_password: str

def get_request_ip(req: Request) -> str:
    return req.client.host if req.client else "-"

def issue_access_token(user_id: int, username: str, role: str):
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id), "usr": username, "role": role,
        "iss": JWT_ISSUER, "aud": JWT_AUDIENCE, "iat": datetime.now(timezone.utc),
        "exp": expire, "type": "access"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def issue_refresh_token_and_store(user_id: int):
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = base64.urlsafe_b64encode(os.urandom(32)).decode()
    
    conn = get_postgres_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET refresh_token_hash = %s, refresh_token_expires_at = %s WHERE id = %s",
              (bcrypt.hash(refresh_token), expire, user_id))
    conn.commit()
    conn.close()
    return refresh_token

def require_auth(req: Request):
    token = req.cookies.get("access_token")
    if not token: raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, JWT_SECRET, audience=JWT_AUDIENCE, algorithms=[JWT_ALG])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired, please refresh.")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    return payload

def require_admin(user: dict = Depends(require_auth)):
    if user.get("role") != "Admin":
        raise HTTPException(status_code=403, detail="Administrator privileges required.")
    return user

def to_serializable(obj):
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    elif hasattr(obj, "dict"):
        return obj.dict()
    elif isinstance(obj, list):
        return [to_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: to_serializable(v) for k, v in obj.items()}
    else:
        return obj

async def run_ai_pipeline(job_id: str, asset_id: int, file_name: str, temp_file_path: str, db):
    print(f"[{job_id}] Starting background AI processing for asset {asset_id}...")
    try:
        await db.jobs.update_one({"job_id": job_id}, {"$set": {"status": "processing", "message": "Creating DOM..."}})
        doms = process_input(Path(temp_file_path))
        if not doms: raise ValueError("DOM creation failed.")
        dom = doms[0]
        
        orchestrator = AgentOrchestrator()
        rag_retriever = get_rag_retriever()
        agents = [
            DocumentUnderstandingAgent(rag_retriever=rag_retriever),
            AnalysisAgent(rag_retriever=rag_retriever),
            SecurityAssessmentAgent(rag_retriever=rag_retriever),
            AnonymizationAgent(rag_retriever=rag_retriever),
            ReportingAgent()
        ]
        for agent in agents: orchestrator.register_agent(agent)

        await db.jobs.update_one({"job_id": job_id}, {"$set": {"message": "Running AI analysis pipeline..."}})
        loop = asyncio.get_event_loop()
        pipeline_results = await loop.run_in_executor(None, orchestrator.process_document, dom)
        serializable_results = to_serializable(pipeline_results)

        await db.jobs.update_one(
            {"job_id": job_id},
            {"$set": {"status": "complete", "message": "Processing complete.", "results": serializable_results}}
        )
        print(f"[{job_id}] AI Processing finished successfully for asset {asset_id}.")
    except Exception as e:
        import traceback
        error_message = f"An error occurred: {str(e)}"
        traceback.print_exc()
        await db.jobs.update_one({"job_id": job_id}, {"$set": {"status": "failed", "message": error_message}})
    finally:
        if os.path.exists(temp_file_path): os.remove(temp_file_path)

@app.post("/auth/login")
def login(data: LoginRequest, req: Request):
    username = data.username
    password = data.password
    conn = get_postgres_conn()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = c.fetchone()
    conn.close()

    if not user or not bcrypt.verify(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = issue_access_token(user["id"], user["username"], user["role"])
    refresh_token = issue_refresh_token_and_store(user["id"])

    resp = JSONResponse({"ok": True, "role": user["role"], "password_change_required": user.get("password_change_required", False)})
    resp.set_cookie("access_token", access_token, httponly=True, secure=COOKIE_SECURE, samesite="lax")
    resp.set_cookie("refresh_token", refresh_token, httponly=True, secure=COOKIE_SECURE, samesite="lax")
    append_audit(user["id"], user["role"], "auth:login", None, get_request_ip(req), req.headers.get("user-agent", "-"), True, "")
    return resp

@app.post("/auth/refresh")
def refresh(req: Request):
    refresh_token = req.cookies.get("refresh_token")
    if not refresh_token: raise HTTPException(status_code=401, detail="Refresh token missing")

    conn = get_postgres_conn()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    
    found_user = None
    for user in users:
        if user["refresh_token_hash"] and bcrypt.verify(refresh_token, user["refresh_token_hash"]):
            if user["refresh_token_expires_at"].replace(tzinfo=timezone.utc) > datetime.now(timezone.utc):
                found_user = user
                break
    conn.close()

    if not found_user:
        raise HTTPException(status_code=403, detail="Invalid or expired refresh token")

    access_token = issue_access_token(found_user["id"], found_user["username"], found_user["role"])
    resp = JSONResponse({"ok": True})
    resp.set_cookie("access_token", access_token, httponly=True, secure=COOKIE_SECURE, samesite="lax")
    return resp

@app.post("/auth/logout")
def logout(req: Request, user: dict = Depends(require_auth)):
    conn = get_postgres_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET refresh_token_hash = NULL, refresh_token_expires_at = NULL WHERE id = %s", (int(user["sub"]),))
    conn.commit()
    conn.close()

    resp = JSONResponse({"ok": True})
    resp.delete_cookie("access_token")
    resp.delete_cookie("refresh_token")
    append_audit(int(user["sub"]), user["role"], "auth:logout", None, get_request_ip(req), req.headers.get("user-agent", "-"), True, "")
    return resp

@app.post("/users/me/change-password")
def change_password(req: Request, data: ChangePasswordRequest, user: dict = Depends(require_auth)):
    user_id = int(user["sub"])
    conn = get_postgres_conn(); c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,)); db_user = c.fetchone()
    if not db_user or not bcrypt.verify(data.old_password, db_user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid old password")
    new_hash = bcrypt.hash(data.new_password)
    c.execute("UPDATE users SET password_hash = %s, password_change_required = FALSE WHERE id = %s", (new_hash, user_id))
    conn.commit(); conn.close()
    resp = JSONResponse({"ok": True, "message": "Password changed successfully. Please log in again."})
    resp.delete_cookie("access_token"); resp.delete_cookie("refresh_token")
    return resp

@app.post("/admin/users")
def add_user(data: UserCreateRequest, admin: dict = Depends(require_admin)):
    conn = get_postgres_conn(); c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = %s", (data.username,));
    if c.fetchone(): raise HTTPException(status_code=409, detail="Username already exists")
    new_hash = bcrypt.hash(data.password)
    c.execute("INSERT INTO users (username, password_hash, role, password_change_required) VALUES (%s, %s, %s, TRUE)", (data.username, new_hash, data.role))
    conn.commit(); conn.close()
    return {"ok": True, "username": data.username, "role": data.role}

@app.delete("/admin/users/{user_id}", status_code=204)
def remove_user(user_id: int, admin: dict = Depends(require_admin)):
    conn = get_postgres_conn(); c = conn.cursor()
    c.execute("DELETE FROM users WHERE id = %s", (user_id,)); conn.commit(); conn.close()
    return Response(status_code=204)

@app.get("/admin/users")
def list_users(admin: dict = Depends(require_admin)):
    conn = get_postgres_conn(); c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("SELECT id, username, role, refresh_token_expires_at as last_login FROM users"); users = c.fetchall(); conn.close()
    return users

@app.get("/admin/analytics/summary")
async def analytics_summary(admin: dict = Depends(require_admin)):
    conn = get_postgres_conn()
    c = conn.cursor(cursor_factory=RealDictCursor)
    c.execute("SELECT COUNT(*) as total_users FROM users")
    total_users = c.fetchone()['total_users']
    c.execute("SELECT COUNT(*) as login_success FROM audit WHERE action = 'auth:login' AND success = TRUE")
    login_success = c.fetchone()['login_success']
    c.execute("SELECT COUNT(*) as login_failed FROM audit WHERE action = 'auth:login' AND success = FALSE")
    login_failed = c.fetchone()['login_failed']   
    conn.close()
    files_processed_last_7d = await app.mongodb.jobs.count_documents({
        "status": "complete",
    })

    return {
        "total_users": total_users,
        "files_processed_last_7d": files_processed_last_7d,
        "login_success": login_success,
        "login_failed": login_failed,
    }

@app.get("/admin/analytics/usage_over_time")
async def usage_over_time(days: int = 30, admin: dict = Depends(require_admin)):
    conn = get_postgres_conn()
    c = conn.cursor(cursor_factory=RealDictCursor)
    since = datetime.now(timezone.utc) - timedelta(days=days)
    c.execute("""
        SELECT 
            to_char(to_timestamp(ts), 'YYYY-MM-DD') as bucket, 
            COUNT(*) as logins_count
        FROM audit
        WHERE to_timestamp(ts) >= %s AND action = 'auth:login' AND success = TRUE
        GROUP BY bucket
        ORDER BY bucket;
    """, (since,))
    logins_rows = c.fetchall()
    conn.close()
    pipeline = [
        {"$match": {
            "status": "complete",
            "created_at": {"$gte": since}
        }},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "jobs_count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    jobs_rows = await app.mongodb.jobs.aggregate(pipeline).to_list(length=100)
    logins_by_day = {row["bucket"]: row["logins_count"] for row in logins_rows}
    jobs_by_day = {row["_id"]: row["jobs_count"] for row in jobs_rows}
    all_days = sorted(set(logins_by_day.keys()) | set(jobs_by_day.keys()))
    points = []
    for day in all_days:
        points.append({
            "bucket": day,
            "logins_count": logins_by_day.get(day, 0),
            "jobs_count": jobs_by_day.get(day, 0)
        })
    return {"granularity": "day", "points": points}

@app.get("/users/me")
def get_current_user_info(user: dict = Depends(require_auth)):

    return user

@app.post("/upload", status_code=202)
async def upload_file(req: Request, file: UploadFile = File(...), user: dict = Depends(require_auth)):
    role = user.get("role")
    if not allowed(role, "upload:create"): raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    content = await file.read()
    dek = get_dek(TENANT_ID, "uploads")
    blob = encrypt_at_rest(content, dek)

    conn = get_postgres_conn()
    c = conn.cursor()
    c.execute("INSERT INTO assets(tenant_id,purpose,filename,blob_json,created_at) VALUES(%s,%s,%s,%s,%s) RETURNING id",
              (TENANT_ID, "raw", file.filename, json.dumps(blob), int(time.time())))
    asset_id = c.fetchone()[0]
    conn.commit()
    conn.close()
    
    append_audit(int(user["sub"]), role, "upload:create", asset_id, get_request_ip(req), req.headers.get("user-agent", "-"), True, file.filename)
    return {"ok": True, "asset_id": asset_id, "message": "File uploaded. Use /process/{asset_id} to start analysis."}

@app.post("/process/{asset_id}", response_model=Job, status_code=202)
async def process_asset(asset_id: int, background_tasks: BackgroundTasks, req: Request, user: dict = Depends(require_auth)):
    role = user.get("role")
    if not allowed(role, "process:create"): raise HTTPException(status_code=403, detail="Insufficient permissions")

    conn = get_postgres_conn()
    c = conn.cursor()
    c.execute("SELECT tenant_id, filename, blob_json FROM assets WHERE id = %s", (asset_id,))
    row = c.fetchone()
    conn.close()
    if not row: raise HTTPException(status_code=404, detail="Asset not found")
    tenant_id, filename, blob_json = row

    blob = json.loads(blob_json)
    dek = get_dek(tenant_id, "uploads")
    content = decrypt_at_rest(blob, dek)
    
    job_id = str(uuid.uuid4())
    temp_dir = "temp_uploads"; os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, f"{job_id}_{filename}")
    with open(temp_file_path, "wb") as f: f.write(content)
    job_data = Job(job_id=job_id, asset_id=asset_id, file_name=filename)
    job_dict = job_data.model_dump()
    job_dict["created_at"] = datetime.now(timezone.utc)
    await app.mongodb.jobs.insert_one(job_dict)
    background_tasks.add_task(run_ai_pipeline, job_id, asset_id, filename, temp_file_path, app.mongodb)
    append_audit(int(user["sub"]), role, "process:create", asset_id, get_request_ip(req), req.headers.get("user-agent", "-"), True, filename)
    
    return job_data

@app.get("/jobs/{job_id}/status")
async def get_job_status(job_id: str, user: dict = Depends(require_auth)):
    job = await app.mongodb.jobs.find_one({"job_id": job_id}, {"results": 0})
    if job:
        if "_id" in job and isinstance(job["_id"], ObjectId):
            job["_id"] = str(job["_id"])
        return job
    raise HTTPException(status_code=404, detail="Job not found")

@app.get("/jobs/{job_id}/results.json")
async def get_job_results(job_id: str, user: dict = Depends(require_auth)):
    job = await app.mongodb.jobs.find_one({"job_id": job_id})
    if not job or job.get("status") != "complete":
        raise HTTPException(status_code=404, detail="Job not found or not complete.")
    if "_id" in job and isinstance(job["_id"], ObjectId):
        job["_id"] = str(job["_id"])
    return Response(content=json.dumps(job.get("results"), default=str, indent=2), media_type="application/json")

@app.get("/jobs/{job_id}/report.pdf")
async def get_pdf_report(job_id: str, user: dict = Depends(require_auth)):
    job = await app.mongodb.jobs.find_one({"job_id": job_id})
    if not job or job.get("status") != "complete":
        raise HTTPException(status_code=404, detail="Job not found or not complete.")
    
    results = job.get("results", {})
    md_report = results.get("markdown_security_report")
    if not md_report and "output" in results:
        md_report = results["output"].get("markdown_security_report")
    if not md_report:
        raise HTTPException(status_code=404, detail="Markdown report not found.")
    file_name_stem = os.path.splitext(job.get("file_name", "report"))[0]
    temp_dir = "temp_reports"; os.makedirs(temp_dir, exist_ok=True)
    pdf_path = os.path.join(temp_dir, f"{job_id}.pdf")   
    export_pdf_from_md(md_report, pdf_path)

    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f: pdf_bytes = f.read()
        os.remove(pdf_path)
        return Response(content=pdf_bytes, media_type="application/pdf",
                        headers={"Content-Disposition": f"attachment; filename={file_name_stem}_report.pdf"})
    raise HTTPException(status_code=500, detail="Failed to generate PDF report.")