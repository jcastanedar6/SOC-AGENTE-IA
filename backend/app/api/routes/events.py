from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.event import Event
from app.schemas.event import EventCreate, EventOut, EventStats
from app.auth.dependencies import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("", response_model=EventOut, status_code=201)
def create_event(payload: EventCreate, db: Session = Depends(get_db)):
    event = Event(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("", response_model=list[EventOut])
def list_events(
    skip: int = 0,
    limit: int = 100,
    severity: str | None = None,
    event_type: str | None = None,
    processed: bool | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Event)
    if severity:
        q = q.filter(Event.severity == severity)
    if event_type:
        q = q.filter(Event.event_type == event_type)
    if processed is not None:
        q = q.filter(Event.processed == processed)
    return q.order_by(Event.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/stats", response_model=EventStats)
def event_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Event.id)).scalar()
    unprocessed = db.query(func.count(Event.id)).filter(Event.processed == False).scalar()

    by_severity_rows = db.query(Event.severity, func.count(Event.id)).group_by(Event.severity).all()
    by_type_rows = db.query(Event.event_type, func.count(Event.id)).group_by(Event.event_type).all()

    return EventStats(
        total=total,
        unprocessed=unprocessed,
        by_severity={row[0]: row[1] for row in by_severity_rows},
        by_type={row[0]: row[1] for row in by_type_rows},
    )


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.delete("/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(event)
    db.commit()
