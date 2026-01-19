"""Asset repository for inventory management."""

from typing import List, Optional, Any
from sqlalchemy import select, and_, or_, func

from .base_repository import BaseRepository
from ..models import Asset, AssetType, AssetStatus, Criticality, Tag


class AssetRepository(BaseRepository[Asset]):
    """Repository for Asset entity operations."""

    def __init__(self, session):
        super().__init__(session, Asset)

    def find_by_ip(self, ip_address: str) -> Optional[Asset]:
        """Find asset by IP address."""
        stmt = select(Asset).where(Asset.ip_address == ip_address)
        result = self._session.execute(stmt)
        return result.scalar_one_or_none()

    def find_by_mac(self, mac_address: str) -> Optional[Asset]:
        """Find asset by MAC address."""
        stmt = select(Asset).where(Asset.mac_address == mac_address)
        result = self._session.execute(stmt)
        return result.scalar_one_or_none()

    def find_by_hostname(self, hostname: str) -> Optional[Asset]:
        """Find asset by hostname."""
        stmt = select(Asset).where(Asset.hostname == hostname)
        result = self._session.execute(stmt)
        return result.scalar_one_or_none()

    def find_by_type(self, asset_type: AssetType) -> List[Asset]:
        """Find assets by type."""
        stmt = select(Asset).where(Asset.asset_type == asset_type)
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def find_by_status(self, status: AssetStatus) -> List[Asset]:
        """Find assets by status."""
        stmt = select(Asset).where(Asset.status == status)
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def find_by_criticality(self, criticality: Criticality) -> List[Asset]:
        """Find assets by criticality."""
        stmt = select(Asset).where(Asset.criticality == criticality)
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def find_by_location(self, location: str) -> List[Asset]:
        """Find assets by location."""
        stmt = select(Asset).where(Asset.location.ilike(f"%{location}%"))
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def find_by_department(self, department: str) -> List[Asset]:
        """Find assets by department."""
        stmt = select(Asset).where(Asset.department.ilike(f"%{department}%"))
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def find_by_tag(self, tag_name: str) -> List[Asset]:
        """Find assets with specific tag."""
        stmt = select(Asset).join(Asset.tags).where(Tag.name == tag_name)
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def find_active(self) -> List[Asset]:
        """Find all active assets."""
        stmt = select(Asset).where(Asset.status == AssetStatus.ACTIVE)
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def find_critical_assets(self) -> List[Asset]:
        """Find critical and high criticality assets."""
        stmt = select(Asset).where(
            Asset.criticality.in_([Criticality.CRITICAL, Criticality.HIGH])
        )
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def search(self, query: str) -> List[Asset]:
        """Search assets by name, hostname, IP, or notes."""
        search_pattern = f"%{query}%"
        stmt = select(Asset).where(
            or_(
                Asset.name.ilike(search_pattern),
                Asset.hostname.ilike(search_pattern),
                Asset.ip_address.ilike(search_pattern),
                Asset.notes.ilike(search_pattern),
            )
        )
        result = self._session.execute(stmt)
        return list(result.scalars().all())

    def count_by_type(self) -> dict[AssetType, int]:
        """Count assets by type."""
        stmt = (
            select(Asset.asset_type, func.count(Asset.id))
            .group_by(Asset.asset_type)
        )
        result = self._session.execute(stmt)
        return {row[0]: row[1] for row in result}

    def count_by_status(self) -> dict[AssetStatus, int]:
        """Count assets by status."""
        stmt = (
            select(Asset.status, func.count(Asset.id))
            .group_by(Asset.status)
        )
        result = self._session.execute(stmt)
        return {row[0]: row[1] for row in result}

    def count_by_criticality(self) -> dict[Criticality, int]:
        """Count assets by criticality."""
        stmt = (
            select(Asset.criticality, func.count(Asset.id))
            .group_by(Asset.criticality)
        )
        result = self._session.execute(stmt)
        return {row[0]: row[1] for row in result}

    def get_unique_locations(self) -> List[str]:
        """Get list of unique locations."""
        stmt = (
            select(Asset.location)
            .where(Asset.location.isnot(None))
            .distinct()
        )
        result = self._session.execute(stmt)
        return [row[0] for row in result if row[0]]

    def get_unique_departments(self) -> List[str]:
        """Get list of unique departments."""
        stmt = (
            select(Asset.department)
            .where(Asset.department.isnot(None))
            .distinct()
        )
        result = self._session.execute(stmt)
        return [row[0] for row in result if row[0]]

    def find_by_criteria(
        self,
        asset_type: Optional[AssetType] = None,
        status: Optional[AssetStatus] = None,
        criticality: Optional[Criticality] = None,
        location: Optional[str] = None,
        department: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        **kwargs: Any,
    ) -> List[Asset]:
        """Find assets by multiple criteria."""
        stmt = select(Asset)
        conditions = []

        if asset_type:
            conditions.append(Asset.asset_type == asset_type)
        if status:
            conditions.append(Asset.status == status)
        if criticality:
            conditions.append(Asset.criticality == criticality)
        if location:
            conditions.append(Asset.location.ilike(f"%{location}%"))
        if department:
            conditions.append(Asset.department.ilike(f"%{department}%"))
        if search:
            search_pattern = f"%{search}%"
            conditions.append(
                or_(
                    Asset.name.ilike(search_pattern),
                    Asset.hostname.ilike(search_pattern),
                    Asset.ip_address.ilike(search_pattern),
                )
            )

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(Asset.name).limit(limit).offset(offset)
        result = self._session.execute(stmt)
        return list(result.scalars().all())


class TagRepository(BaseRepository[Tag]):
    """Repository for Tag entity operations."""

    def __init__(self, session):
        super().__init__(session, Tag)

    def find_by_name(self, name: str) -> Optional[Tag]:
        """Find tag by name."""
        stmt = select(Tag).where(Tag.name == name)
        result = self._session.execute(stmt)
        return result.scalar_one_or_none()

    def find_or_create(self, name: str, color: str = "#6c757d") -> Tag:
        """Find existing tag or create new one."""
        tag = self.find_by_name(name)
        if not tag:
            tag = Tag(name=name, color=color)
            self.add(tag)
        return tag

    def find_by_criteria(self, **criteria: Any) -> List[Tag]:
        """Find tags by criteria."""
        stmt = select(Tag)
        if "name_like" in criteria:
            stmt = stmt.where(Tag.name.ilike(f"%{criteria['name_like']}%"))
        result = self._session.execute(stmt)
        return list(result.scalars().all())
