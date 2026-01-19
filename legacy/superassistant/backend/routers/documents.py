from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.document import Document
from schemas.document import DocumentCreate, DocumentUpdate, DocumentResponse

router = APIRouter()


@router.get("/", response_model=List[DocumentResponse])
def get_documents(
    type: str = None,
    status: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Récupère tous les documents avec filtres"""
    query = db.query(Document)

    if type:
        query = query.filter(Document.type == type)
    if status:
        query = query.filter(Document.status == status)

    documents = query.offset(skip).limit(limit).all()
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    """Récupère un document par ID"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    return document


@router.post("/", response_model=DocumentResponse, status_code=201)
def create_document(document: DocumentCreate, db: Session = Depends(get_db)):
    """Crée un nouveau document"""
    db_document = Document(**document.model_dump())
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


@router.patch("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: int,
    document_update: DocumentUpdate,
    db: Session = Depends(get_db)
):
    """Met à jour un document"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouvé")

    update_data = document_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(document, field, value)

    db.commit()
    db.refresh(document)
    return document


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Supprime un document"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouvé")

    db.delete(document)
    db.commit()
    return None
