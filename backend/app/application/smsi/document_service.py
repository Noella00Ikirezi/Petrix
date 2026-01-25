"""Document management service with versioning, audit trail, and collaboration features.

Features:
- View/Edit documents inline
- Version history with full audit trail
- Rollback to previous versions
- Last two validated versions quick access
- Document ownership and locking
- Comments and annotations
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from sqlalchemy.orm import selectinload

from app.infrastructure.database.smsi_models import (
    GeneratedDocument,
    DocumentVersion,
    DocumentComment,
    DocumentStatus,
    SMSIProject,
)
from app.infrastructure.database.models import User


@dataclass
class VersionInfo:
    """Version information for display."""
    version_number: int
    version_label: str
    modified_by: str
    modified_at: datetime
    change_summary: Optional[str]
    change_type: str
    is_validated: bool
    is_current: bool


@dataclass
class DocumentInfo:
    """Full document information including history."""
    id: str
    code: str
    name: str
    status: str
    content_markdown: str
    current_version: int
    owner: Optional[str]
    is_locked: bool
    locked_by: Optional[str]
    last_validated_version: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]


class DocumentService:
    """Service for document management with versioning and collaboration."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.lock_timeout_minutes = 30  # Auto-unlock after 30 minutes

    # =========================================================================
    # DOCUMENT RETRIEVAL
    # =========================================================================

    async def get_document(
        self,
        document_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Get document with full details for viewing/editing."""
        doc = await self.db.get(GeneratedDocument, document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        # Get project info for organization name
        project = await self.db.get(SMSIProject, doc.project_id)
        organization_name = project.organization_name if project else "Organisation"

        # Get owner info
        owner_name = None
        if doc.owner_id:
            owner = await self.db.get(User, doc.owner_id)
            owner_name = owner.email if owner else None

        # Check lock status
        is_locked = False
        locked_by_name = None
        if doc.locked_by_id and doc.locked_at:
            # Check if lock is still valid (not expired)
            lock_expiry = doc.locked_at + timedelta(minutes=self.lock_timeout_minutes)
            if datetime.utcnow() < lock_expiry:
                is_locked = doc.locked_by_id != user_id
                if doc.locked_by_id:
                    locker = await self.db.get(User, doc.locked_by_id)
                    locked_by_name = locker.email if locker else None
            else:
                # Lock expired, clear it
                doc.locked_by_id = None
                doc.locked_at = None
                await self.db.commit()

        return {
            "id": str(doc.id),
            "code": doc.code,
            "name": doc.name,
            "document_type": doc.document_type.value,
            "status": doc.status.value,
            "version": doc.version,
            "current_version_number": doc.current_version_number or 1,
            "content_markdown": doc.content_markdown,
            "content_html": doc.content_html,
            "organization_name": organization_name,
            "owner": owner_name,
            "is_locked": is_locked,
            "locked_by": locked_by_name,
            "last_validated_version": doc.last_validated_version,
            "second_last_validated_version": doc.second_last_validated_version,
            "ai_model_used": doc.ai_model_used,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
        }

    # =========================================================================
    # DOCUMENT EDITING
    # =========================================================================

    async def acquire_lock(
        self,
        document_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Acquire editing lock on a document."""
        doc = await self.db.get(GeneratedDocument, document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        # Check if already locked by someone else
        if doc.locked_by_id and doc.locked_by_id != user_id:
            lock_expiry = doc.locked_at + timedelta(minutes=self.lock_timeout_minutes)
            if datetime.utcnow() < lock_expiry:
                locker = await self.db.get(User, doc.locked_by_id)
                raise ValueError(f"Document is locked by {locker.email if locker else 'another user'}")

        # Acquire lock
        doc.locked_by_id = user_id
        doc.locked_at = datetime.utcnow()
        await self.db.commit()

        return {
            "success": True,
            "lock_expires_at": (doc.locked_at + timedelta(minutes=self.lock_timeout_minutes)).isoformat()
        }

    async def release_lock(
        self,
        document_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Release editing lock on a document."""
        doc = await self.db.get(GeneratedDocument, document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        # Only the lock holder can release (or admin)
        if doc.locked_by_id and doc.locked_by_id != user_id:
            raise ValueError("You don't have the lock on this document")

        doc.locked_by_id = None
        doc.locked_at = None
        await self.db.commit()

        return {"success": True}

    async def update_document(
        self,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
        content_markdown: str,
        change_summary: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update document content and create a new version."""
        doc = await self.db.get(GeneratedDocument, document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        # Check lock
        if doc.locked_by_id and doc.locked_by_id != user_id:
            raise ValueError("Document is locked by another user")

        # Get user info
        user = await self.db.get(User, user_id)

        # Create version snapshot of current content BEFORE updating
        if doc.content_markdown:
            current_version_num = doc.current_version_number or 1
            version = DocumentVersion(
                document_id=doc.id,
                version_number=current_version_num,
                version_label=doc.version,
                content_markdown=doc.content_markdown,
                content_html=doc.content_html,
                change_summary=change_summary or "Document updated",
                change_type="edit",
                modified_by_id=user_id,
            )
            self.db.add(version)

        # Update document
        new_version_num = (doc.current_version_number or 1) + 1
        doc.content_markdown = content_markdown
        doc.content_html = self._markdown_to_html(content_markdown)
        doc.current_version_number = new_version_num
        doc.version = f"1.{new_version_num - 1}"
        doc.updated_at = datetime.utcnow()

        # Refresh lock
        doc.locked_at = datetime.utcnow()

        await self.db.commit()

        logger.info(f"Document {doc.code} updated by {user.email}, version {new_version_num}")

        return {
            "success": True,
            "version_number": new_version_num,
            "version_label": doc.version,
            "updated_at": doc.updated_at.isoformat()
        }

    # =========================================================================
    # VERSION HISTORY
    # =========================================================================

    async def get_version_history(
        self,
        document_id: uuid.UUID,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get version history for a document."""
        stmt = select(DocumentVersion).where(
            DocumentVersion.document_id == document_id
        ).order_by(desc(DocumentVersion.version_number)).limit(limit)

        result = await self.db.execute(stmt)
        versions = result.scalars().all()

        # Get current document
        doc = await self.db.get(GeneratedDocument, document_id)

        history = []
        for v in versions:
            modifier = await self.db.get(User, v.modified_by_id)
            validator = None
            if v.validated_by_id:
                validator = await self.db.get(User, v.validated_by_id)

            history.append({
                "id": str(v.id),
                "version_number": v.version_number,
                "version_label": v.version_label,
                "modified_by": modifier.email if modifier else "Unknown",
                "modified_at": v.created_at.isoformat(),
                "change_summary": v.change_summary,
                "change_type": v.change_type,
                "is_validated": v.is_validated,
                "validated_by": validator.email if validator else None,
                "validated_at": v.validated_at.isoformat() if v.validated_at else None,
                "is_current": v.version_number == (doc.current_version_number or 1) - 1,
            })

        return history

    async def get_version_content(
        self,
        document_id: uuid.UUID,
        version_number: int
    ) -> Dict[str, Any]:
        """Get content of a specific version."""
        stmt = select(DocumentVersion).where(
            and_(
                DocumentVersion.document_id == document_id,
                DocumentVersion.version_number == version_number
            )
        )
        result = await self.db.execute(stmt)
        version = result.scalar_one_or_none()

        if not version:
            raise ValueError(f"Version {version_number} not found")

        modifier = await self.db.get(User, version.modified_by_id)

        return {
            "version_number": version.version_number,
            "version_label": version.version_label,
            "content_markdown": version.content_markdown,
            "content_html": version.content_html,
            "modified_by": modifier.email if modifier else "Unknown",
            "modified_at": version.created_at.isoformat(),
            "change_summary": version.change_summary,
            "is_validated": version.is_validated,
        }

    # =========================================================================
    # ROLLBACK
    # =========================================================================

    async def rollback_to_version(
        self,
        document_id: uuid.UUID,
        version_number: int,
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Rollback document to a previous version."""
        doc = await self.db.get(GeneratedDocument, document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        # Get the target version
        stmt = select(DocumentVersion).where(
            and_(
                DocumentVersion.document_id == document_id,
                DocumentVersion.version_number == version_number
            )
        )
        result = await self.db.execute(stmt)
        target_version = result.scalar_one_or_none()

        if not target_version:
            raise ValueError(f"Version {version_number} not found")

        user = await self.db.get(User, user_id)

        # Save current as a version before rollback
        if doc.content_markdown:
            current_version_num = doc.current_version_number or 1
            version = DocumentVersion(
                document_id=doc.id,
                version_number=current_version_num,
                version_label=doc.version,
                content_markdown=doc.content_markdown,
                content_html=doc.content_html,
                change_summary=f"Before rollback to version {version_number}",
                change_type="pre_rollback",
                modified_by_id=user_id,
            )
            self.db.add(version)

        # Apply rollback
        new_version_num = (doc.current_version_number or 1) + 1
        doc.content_markdown = target_version.content_markdown
        doc.content_html = target_version.content_html or self._markdown_to_html(target_version.content_markdown)
        doc.current_version_number = new_version_num
        doc.version = f"1.{new_version_num - 1}"
        doc.updated_at = datetime.utcnow()

        # Create rollback version entry
        rollback_version = DocumentVersion(
            document_id=doc.id,
            version_number=new_version_num,
            version_label=doc.version,
            content_markdown=doc.content_markdown,
            content_html=doc.content_html,
            change_summary=f"Rollback to version {version_number}",
            change_type="rollback",
            modified_by_id=user_id,
        )
        self.db.add(rollback_version)

        await self.db.commit()

        logger.info(f"Document {doc.code} rolled back to version {version_number} by {user.email}")

        return {
            "success": True,
            "new_version_number": new_version_num,
            "rolled_back_from": version_number,
            "updated_at": doc.updated_at.isoformat()
        }

    async def rollback_to_last_validated(
        self,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
        use_second_last: bool = False
    ) -> Dict[str, Any]:
        """Quick rollback to last (or second last) validated version."""
        doc = await self.db.get(GeneratedDocument, document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        target_version = doc.second_last_validated_version if use_second_last else doc.last_validated_version

        if not target_version:
            raise ValueError("No validated version available for rollback")

        return await self.rollback_to_version(document_id, target_version, user_id)

    # =========================================================================
    # VALIDATION
    # =========================================================================

    async def validate_version(
        self,
        document_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Validate the current version of a document."""
        doc = await self.db.get(GeneratedDocument, document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        current_version_num = doc.current_version_number or 1

        # Get or create current version entry
        stmt = select(DocumentVersion).where(
            and_(
                DocumentVersion.document_id == document_id,
                DocumentVersion.version_number == current_version_num - 1
            )
        )
        result = await self.db.execute(stmt)
        version = result.scalar_one_or_none()

        if version:
            version.is_validated = True
            version.validated_by_id = user_id
            version.validated_at = datetime.utcnow()

        # Update document's validated version pointers
        doc.second_last_validated_version = doc.last_validated_version
        doc.last_validated_version = current_version_num - 1
        doc.status = DocumentStatus.APPROVED
        doc.reviewed_by_id = user_id
        doc.reviewed_at = datetime.utcnow()

        await self.db.commit()

        user = await self.db.get(User, user_id)
        logger.info(f"Document {doc.code} version {current_version_num - 1} validated by {user.email}")

        return {
            "success": True,
            "validated_version": current_version_num - 1,
            "validated_by": user.email,
            "validated_at": datetime.utcnow().isoformat()
        }

    # =========================================================================
    # OWNERSHIP
    # =========================================================================

    async def set_owner(
        self,
        document_id: uuid.UUID,
        new_owner_id: uuid.UUID,
        by_user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Set document owner."""
        doc = await self.db.get(GeneratedDocument, document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        old_owner_id = doc.owner_id
        doc.owner_id = new_owner_id
        await self.db.commit()

        new_owner = await self.db.get(User, new_owner_id)
        by_user = await self.db.get(User, by_user_id)

        logger.info(f"Document {doc.code} ownership changed to {new_owner.email} by {by_user.email}")

        return {
            "success": True,
            "new_owner": new_owner.email
        }

    # =========================================================================
    # COMMENTS
    # =========================================================================

    async def add_comment(
        self,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        comment_type: str = "general",
        section_ref: Optional[str] = None,
        line_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """Add a comment to a document."""
        doc = await self.db.get(GeneratedDocument, document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        comment = DocumentComment(
            document_id=document_id,
            content=content,
            comment_type=comment_type,
            section_ref=section_ref,
            line_number=line_number,
            author_id=user_id,
        )
        self.db.add(comment)
        await self.db.commit()

        user = await self.db.get(User, user_id)

        return {
            "id": str(comment.id),
            "content": content,
            "author": user.email,
            "created_at": comment.created_at.isoformat()
        }

    async def get_comments(
        self,
        document_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Get all comments for a document."""
        stmt = select(DocumentComment).where(
            DocumentComment.document_id == document_id
        ).order_by(desc(DocumentComment.created_at))

        result = await self.db.execute(stmt)
        comments = result.scalars().all()

        comment_list = []
        for c in comments:
            author = await self.db.get(User, c.author_id)
            resolver = None
            if c.resolved_by_id:
                resolver = await self.db.get(User, c.resolved_by_id)

            comment_list.append({
                "id": str(c.id),
                "content": c.content,
                "comment_type": c.comment_type,
                "section_ref": c.section_ref,
                "line_number": c.line_number,
                "author": author.email if author else "Unknown",
                "created_at": c.created_at.isoformat(),
                "is_resolved": c.is_resolved,
                "resolved_by": resolver.email if resolver else None,
                "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
            })

        return comment_list

    async def resolve_comment(
        self,
        comment_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Mark a comment as resolved."""
        comment = await self.db.get(DocumentComment, comment_id)
        if not comment:
            raise ValueError(f"Comment {comment_id} not found")

        comment.is_resolved = True
        comment.resolved_by_id = user_id
        comment.resolved_at = datetime.utcnow()
        await self.db.commit()

        return {"success": True}

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _markdown_to_html(self, markdown_content: str) -> str:
        """Convert Markdown to HTML."""
        try:
            import markdown
            return markdown.markdown(
                markdown_content,
                extensions=['tables', 'toc', 'fenced_code']
            )
        except ImportError:
            return f"<pre>{markdown_content}</pre>"


def get_document_service(db: AsyncSession) -> DocumentService:
    """Get a DocumentService instance."""
    return DocumentService(db)
