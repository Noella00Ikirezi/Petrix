from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.knowledge import KnowledgeItem
from schemas.knowledge import KnowledgeCreate, KnowledgeUpdate, KnowledgeResponse

router = APIRouter()


@router.get("/", response_model=List[KnowledgeResponse])
def get_knowledge_items(
    category: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Récupère les items de la base de connaissances"""
    query = db.query(KnowledgeItem)

    if category:
        query = query.filter(KnowledgeItem.category == category)

    items = query.offset(skip).limit(limit).all()
    return items


@router.get("/{item_id}", response_model=KnowledgeResponse)
def get_knowledge_item(item_id: int, db: Session = Depends(get_db)):
    """Récupère un item par ID"""
    item = db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item non trouvé")
    return item


@router.post("/", response_model=KnowledgeResponse, status_code=201)
def create_knowledge_item(item: KnowledgeCreate, db: Session = Depends(get_db)):
    """Crée un nouvel item"""
    db_item = KnowledgeItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.patch("/{item_id}", response_model=KnowledgeResponse)
def update_knowledge_item(
    item_id: int,
    item_update: KnowledgeUpdate,
    db: Session = Depends(get_db)
):
    """Met à jour un item"""
    item = db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item non trouvé")

    update_data = item_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def delete_knowledge_item(item_id: int, db: Session = Depends(get_db)):
    """Supprime un item"""
    item = db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item non trouvé")

    db.delete(item)
    db.commit()
    return None
