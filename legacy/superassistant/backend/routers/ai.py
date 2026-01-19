from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.task import Task
from schemas.ai import (
    PrioritizationRequest,
    PrioritizationResponse,
    EmailGenerationRequest,
    EmailGenerationResponse,
    DocumentGenerationRequest,
    DocumentGenerationResponse,
    ChatRequest,
    ChatResponse
)
from services.priority_service import PriorityService
from services.email_service import EmailService
from services.document_service import DocumentService
from services.ai_service import AIService
from services.context_service import ContextService

router = APIRouter()


@router.post("/prioritize", response_model=PrioritizationResponse)
async def prioritize_tasks(
    request: PrioritizationRequest,
    db: Session = Depends(get_db)
):
    """Analyse et priorise les tâches"""
    try:
        # Récupérer les tâches actives (non complétées)
        tasks = db.query(Task).filter(
            Task.status.in_(["todo", "in_progress", "blocked"])
        ).all()

        if not tasks:
            return {
                "top_tasks": [],
                "daily_plan": "Aucune tâche à prioriser pour le moment.",
                "analysis": "Votre liste de tâches est vide ou toutes sont terminées!"
            }

        # Utiliser le service de priorisation
        priority_service = PriorityService()
        result = await priority_service.prioritize_tasks(tasks, request.context)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de priorisation: {str(e)}")


@router.post("/generate-email", response_model=EmailGenerationResponse)
async def generate_email(request: EmailGenerationRequest):
    """Génère un email professionnel"""
    try:
        email_service = EmailService()
        result = await email_service.generate_email(
            recipient_type=request.recipient_type,
            context=request.context,
            tone=request.tone,
            subject=request.subject,
            key_points=request.key_points,
            user_context=request.user_context
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de génération: {str(e)}")


@router.post("/generate-document", response_model=DocumentGenerationResponse)
async def generate_document(request: DocumentGenerationRequest):
    """Génère un document SMSI"""
    try:
        document_service = DocumentService()
        result = await document_service.generate_document(
            doc_type=request.doc_type,
            title=request.title,
            scope=request.scope,
            requirements=request.requirements,
            references=request.references
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de génération: {str(e)}")


@router.post("/chat", response_model=ChatResponse)
async def chat_assistant(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Assistant conversationnel"""
    try:
        # Récupérer le contexte utilisateur
        context_service = ContextService()
        user_context = context_service.get_full_context(db)

        # Combiner avec le contexte de la requête
        full_context = {**user_context, **request.context}

        # Construire le prompt système
        system_prompt = f"""Tu es SuperAssistant, un assistant de productivité pour un professionnel de la cybersécurité en alternance.

Tu aides avec:
- Organisation et gestion du temps
- Rédaction professionnelle
- Conseils cybersécurité
- Planification de projets

Contexte utilisateur: {full_context}

Sois concis, précis et actionnable."""

        # Générer la réponse
        ai_service = AIService()
        response = await ai_service.generate_response(
            system_prompt=system_prompt,
            user_message=request.message,
            max_tokens=1000
        )

        return {
            "response": response,
            "suggestions": []  # Peut être enrichi plus tard
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de chat: {str(e)}")
