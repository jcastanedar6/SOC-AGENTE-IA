from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, UTC
from app.db.session import get_db
from app.models.server import Server
from app.schemas.server import ServerCreate, ServerUpdate, ServerOut
from app.auth.dependencies import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[ServerOut])
def list_servers(db: Session = Depends(get_db)):
    return db.query(Server).order_by(Server.hostname).all()


@router.post("", response_model=ServerOut, status_code=201)
def create_server(payload: ServerCreate, db: Session = Depends(get_db)):
    if db.query(Server).filter(Server.hostname == payload.hostname).first():
        raise HTTPException(status_code=409, detail="Server already exists")
    server = Server(**payload.model_dump())
    db.add(server)
    db.commit()
    db.refresh(server)
    return server


@router.get("/{server_id}", response_model=ServerOut)
def get_server(server_id: int, db: Session = Depends(get_db)):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server


@router.patch("/{server_id}", response_model=ServerOut)
def update_server(server_id: int, payload: ServerUpdate, db: Session = Depends(get_db)):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(server, key, value)
    server.last_seen = datetime.now(UTC)

    db.commit()
    db.refresh(server)
    return server


@router.delete("/{server_id}", status_code=204)
def delete_server(server_id: int, db: Session = Depends(get_db)):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    db.delete(server)
    db.commit()
