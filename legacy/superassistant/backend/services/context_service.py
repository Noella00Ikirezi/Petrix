from sqlalchemy.orm import Session
from models.user_context import UserContext
from typing import Dict, Any, Optional


class ContextService:
    """Service de gestion du contexte utilisateur"""

    @staticmethod
    def get_context(db: Session, category: Optional[str] = None) -> Dict[str, Any]:
        """Récupère le contexte utilisateur"""
        query = db.query(UserContext)
        if category:
            query = query.filter(UserContext.category == category)

        contexts = query.all()
        return {ctx.key: ctx.value for ctx in contexts}

    @staticmethod
    def set_context(
        db: Session,
        key: str,
        value: str,
        category: str
    ) -> UserContext:
        """Définit ou met à jour un élément de contexte"""
        context = db.query(UserContext).filter(UserContext.key == key).first()

        if context:
            context.value = value
            context.category = category
        else:
            context = UserContext(key=key, value=value, category=category)
            db.add(context)

        db.commit()
        db.refresh(context)
        return context

    @staticmethod
    def delete_context(db: Session, key: str) -> bool:
        """Supprime un élément de contexte"""
        context = db.query(UserContext).filter(UserContext.key == key).first()
        if context:
            db.delete(context)
            db.commit()
            return True
        return False

    @staticmethod
    def get_full_context(db: Session) -> Dict[str, Any]:
        """Récupère le contexte complet structuré par catégorie"""
        contexts = db.query(UserContext).all()

        result = {}
        for ctx in contexts:
            if ctx.category not in result:
                result[ctx.category] = {}
            result[ctx.category][ctx.key] = ctx.value

        return result
