from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.task import Task
from schemas.task import TaskCreate, TaskUpdate, TaskResponse

router = APIRouter()


@router.get("/", response_model=List[TaskResponse])
def get_tasks(
    skip: int = 0,
    limit: int = 100,
    category: str = None,
    status: str = None,
    db: Session = Depends(get_db)
):
    """Récupère toutes les tâches avec filtres optionnels"""
    query = db.query(Task)

    if category:
        query = query.filter(Task.category == category)
    if status:
        query = query.filter(Task.status == status)

    tasks = query.offset(skip).limit(limit).all()
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Récupère une tâche par ID"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    return task


@router.post("/", response_model=TaskResponse, status_code=201)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Crée une nouvelle tâche"""
    db_task = Task(**task.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """Met à jour une tâche"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")

    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Supprime une tâche"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")

    db.delete(task)
    db.commit()
    return None
