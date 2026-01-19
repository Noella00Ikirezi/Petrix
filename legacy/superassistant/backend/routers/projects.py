from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.project import Project
from schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse

router = APIRouter()


@router.get("/", response_model=List[ProjectResponse])
def get_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupère tous les projets"""
    projects = db.query(Project).offset(skip).limit(limit).all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """Récupère un projet par ID"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return project


@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Crée un nouveau projet"""
    db_project = Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """Met à jour un projet"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")

    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """Supprime un projet"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")

    db.delete(project)
    db.commit()
    return None
