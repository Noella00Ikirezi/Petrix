"""Point d'entrée de l'application FastAPI Petrix.

Initialise l'application, configure le middleware CORS, enregistre le routeur API
et gère les événements de démarrage/arrêt via le gestionnaire de contexte ``lifespan``.
Ce module est le seul endroit où la topologie de l'application est assemblée.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.infrastructure.database import Base, engine
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire de cycle de vie FastAPI : démarrage et arrêt de l'application.

    Au démarrage :
    - Crée les tables SQLAlchemy si elles n'existent pas encore. L'appel est
      encadré d'un try/except car plusieurs workers Uvicorn peuvent s'exécuter
      en parallèle et déclencher une erreur de concurrence sur ``CREATE TABLE``.
    - Crée l'utilisateur admin par défaut s'il est absent, afin que la plateforme
      soit immédiatement opérationnelle à l'issue du premier déploiement.

    À l'arrêt : journalise la fermeture propre (le yield délimite les deux phases).
    """
    logger.info("Starting Petrix API...")

    # Création des tables — le try/except absorbe la race condition multi-workers
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")
    except Exception as e:
        logger.warning(f"create_all skipped (likely already done by another worker): {e}")

    # Imports différés pour éviter les dépendances circulaires au niveau module
    from app.infrastructure.database import SessionLocal
    from app.infrastructure.database.models import User
    from app.core.security import get_password_hash
    from app.core.permissions import UserRole

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == settings.admin_email).first()
        if not admin:
            admin = User(
                email=settings.admin_email,
                password_hash=get_password_hash(settings.admin_password),
                first_name="Admin",
                last_name="User",
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin)
            db.commit()
            logger.info(f"Admin user created: {settings.admin_email}")
    finally:
        db.close()

    yield

    logger.info("Shutting down Petrix API...")


app = FastAPI(
    title=settings.app_name,
    description="Petrix API - Security & Compliance Platform",
    version="0.1.0",
    lifespan=lifespan,
    # redirect_slashes=False : évite les redirections 307 non souhaitées sur les
    # routes avec ou sans slash final (comportement prévisible pour les clients API).
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health")
async def health_check():
    """Retourne le statut de disponibilité de l'API (sonde de liveness HTTP simple).

    Intentionnellement léger : ne consulte pas la base de données ni Redis pour ne
    pas bloquer un redémarrage en cas de panne de ces dépendances.
    """
    return {"status": "healthy", "version": "0.1.0"}
