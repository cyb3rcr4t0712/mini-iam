from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime

from .database import engine, Base, get_db
from . import models, auth
from .rbac import require_role
from .audit import log_action

app = FastAPI(title="MiniIAM – Identity Lifecycle Simulator")

Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "MiniIAM is running"}


# ────────────────────────────────────────────────
# Authentication
# ────────────────────────────────────────────────

@app.post("/register")
def register(
    username: str,
    password: str,
    role: str,
    department: str = None,
    db: Session = Depends(get_db)
):
    if role not in ["Admin", "Manager", "Employee"]:
        raise HTTPException(400, "Invalid role")

    existing = db.query(models.User).filter(models.User.username == username).first()
    if existing:
        raise HTTPException(400, "Username already exists")

    user = models.User(
        username=username,
        password_hash=auth.hash_password(password),
        role=role,
        department=department,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User created", "username": username}


@app.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, username, password)
    if not user:
        raise HTTPException(401, "Invalid credentials")

    user.last_login = datetime.utcnow()
    db.commit()
    token = auth.create_access_token({
    "sub": user.username,
    "role": user.role,
    "id": user.id,
    "department": user.department
    })
    return {"access_token": token, "token_type": "bearer"}


# ────────────────────────────────────────────────
# IAM Operations
# ────────────────────────────────────────────────

@app.post("/users/{user_id}/deprovision")
def deprovision(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_role("Admin")),
    request: Request = None
):
    target = db.query(models.User).filter(models.User.id == user_id).first()
    if not target:
        raise HTTPException(404, "User not found")
    if not target.is_active:
        raise HTTPException(400, "Already inactive")

    target.is_active = False
    db.commit()

    log_action(
        db, current_user["id"], "DEPROVISION",
        f"Deprovisioned {target.username} (id {user_id})",
        request.client.host if request else None
    )

    return {"message": "User deprovisioned"}


@app.post("/access/request")
def request_access(
    resource: str,
    reason: str,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user),
    request: Request = None
):
    user = db.query(models.User).filter(models.User.username == current_user["username"]).first()
    req = models.AccessRequest(
        user_id=user.id,
        resource=resource,
        reason=reason
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    log_action(
        db, user.id, "REQUEST_ACCESS",
        f"Requested {resource} – {reason}",
        request.client.host if request else None
    )

    return {"message": "Request submitted", "id": req.id}


@app.post("/access/approve/{req_id}")
def approve(
    req_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user),
    request: Request = None
):
    req = db.query(models.AccessRequest).filter(models.AccessRequest.id == req_id).first()
    if not req:
        raise HTTPException(404, "Request not found")
    if req.status != "Pending":
        raise HTTPException(400, "Already processed")

    requester = db.query(models.User).get(req.user_id)

    # Approval rules
    if current_user["role"] == "Admin":
        pass
    elif current_user["role"] == "Manager":
        if requester.department != current_user.get("department"):
            raise HTTPException(403, "Can only approve own department")
    else:
        raise HTTPException(403, "Not allowed")

    req.status = "Approved"
    req.approved_by = current_user["username"]
    db.commit()

    log_action(
        db, current_user["id"], "APPROVE_REQUEST",
        f"Approved request {req_id} for {req.resource}",
        request.client.host if request else None
    )

    return {"message": "Approved"}


@app.get("/reports/access-review")
def access_review(
    db: Session = Depends(get_db),
    current_user = Depends(require_role("Admin"))
):
    users = db.query(models.User).all()
    data = []

    for u in users:
        data.append({
            "username": u.username,
            "role": u.role,
            "department": u.department or "—",
            "active": u.is_active,
            "last_login": u.last_login.isoformat() if u.last_login else "Never",
            "privileged": u.role in ("Admin", "Manager")
        })

    return {
        "generated": datetime.utcnow().isoformat(),
        "users": data,
        "summary": {
            "total": len(data),
            "active": sum(1 for x in data if x["active"]),
            "privileged": sum(1 for x in data if x["privileged"])
        }
    }