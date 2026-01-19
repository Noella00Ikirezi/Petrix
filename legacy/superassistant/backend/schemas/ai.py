from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# Priorisation
class PrioritizationRequest(BaseModel):
    context: Optional[Dict[str, Any]] = {}


class PrioritizedTask(BaseModel):
    task_id: int
    title: str
    priority_score: float
    justification: str


class PrioritizationResponse(BaseModel):
    top_tasks: List[PrioritizedTask]
    daily_plan: str
    analysis: str


# Génération d'email
class EmailGenerationRequest(BaseModel):
    recipient_type: str = Field(..., description="manager/professeur/collègue/externe")
    context: str = Field(..., description="support/smsi/demande/incident/autre")
    tone: str = Field(default="professionnel", description="formel/professionnel/technique/amical")
    subject: str = Field(..., description="Sujet en quelques mots")
    key_points: List[str] = Field(..., description="Points clés à inclure")
    user_context: Optional[str] = None


class EmailGenerationResponse(BaseModel):
    subject: str
    body: str
    suggestions: Optional[List[str]] = []


# Génération de document SMSI
class DocumentGenerationRequest(BaseModel):
    doc_type: str = Field(..., description="politique/procedure/guide/registre/rapport/cr")
    title: str
    scope: str = Field(..., description="Périmètre/contexte")
    requirements: List[str] = Field(..., description="Exigences spécifiques")
    references: Optional[List[str]] = []


class DocumentGenerationResponse(BaseModel):
    title: str
    content: str
    structure: List[str]
    compliance_notes: Optional[List[str]] = []


# Chat assistant
class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = {}


class ChatResponse(BaseModel):
    response: str
    suggestions: Optional[List[str]] = []
