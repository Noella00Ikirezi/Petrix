from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from database import get_db
from models.event import Event
from schemas.event import EventCreate, EventUpdate, EventResponse

router = APIRouter()


@router.get("/", response_model=List[EventResponse])
def get_events(
    start_date: datetime = None,
    end_date: datetime = None,
    category: str = None,
    db: Session = Depends(get_db)
):
    """Récupère les événements avec filtres optionnels"""
    query = db.query(Event)

    if start_date:
        query = query.filter(Event.start_time >= start_date)
    if end_date:
        query = query.filter(Event.end_time <= end_date)
    if category:
        query = query.filter(Event.category == category)

    events = query.order_by(Event.start_time).all()
    return events


@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """Récupère un événement par ID"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")
    return event


@router.post("/", response_model=EventResponse, status_code=201)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    """Crée un nouvel événement"""
    db_event = Event(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


@router.patch("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: int,
    event_update: EventUpdate,
    db: Session = Depends(get_db)
):
    """Met à jour un événement"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")

    update_data = event_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)

    db.commit()
    db.refresh(event)
    return event


@router.delete("/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    """Supprime un événement"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Événement non trouvé")

    db.delete(event)
    db.commit()
    return None
