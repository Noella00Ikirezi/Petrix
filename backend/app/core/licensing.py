"""License management system for self-hosted deployments."""
import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from uuid import uuid4

from cryptography.fernet import Fernet, InvalidToken
from pydantic import BaseModel

from app.config import settings


class LicenseTier(str, Enum):
    """License tiers with feature limits."""
    COMMUNITY = "community"  # Free, limited features
    PROFESSIONAL = "professional"  # Paid, most features
    ENTERPRISE = "enterprise"  # Full features + support


class LicenseFeatures(BaseModel):
    """Features enabled by license tier."""
    max_assets: int
    max_users: int
    max_scans_per_month: int
    compliance_modules: bool
    ai_assistant: bool
    api_access: bool
    custom_reports: bool
    sso_integration: bool
    priority_support: bool


# Feature limits per tier
TIER_FEATURES = {
    LicenseTier.COMMUNITY: LicenseFeatures(
        max_assets=50,
        max_users=3,
        max_scans_per_month=10,
        compliance_modules=False,
        ai_assistant=False,
        api_access=True,
        custom_reports=False,
        sso_integration=False,
        priority_support=False,
    ),
    LicenseTier.PROFESSIONAL: LicenseFeatures(
        max_assets=500,
        max_users=25,
        max_scans_per_month=100,
        compliance_modules=True,
        ai_assistant=True,
        api_access=True,
        custom_reports=True,
        sso_integration=False,
        priority_support=False,
    ),
    LicenseTier.ENTERPRISE: LicenseFeatures(
        max_assets=-1,  # Unlimited
        max_users=-1,
        max_scans_per_month=-1,
        compliance_modules=True,
        ai_assistant=True,
        api_access=True,
        custom_reports=True,
        sso_integration=True,
        priority_support=True,
    ),
}


class LicenseInfo(BaseModel):
    """License information."""
    license_id: str
    organization: str
    tier: LicenseTier
    issued_at: datetime
    expires_at: datetime
    features: LicenseFeatures
    is_valid: bool = True
    days_remaining: int = 0


class LicenseManager:
    """Manages license validation and feature gating."""

    # In production, this would be a proper secret key management
    # For now, derive from settings.secret_key
    _SIGNING_KEY = None

    @classmethod
    def _get_signing_key(cls) -> bytes:
        """Get or derive the signing key."""
        if cls._SIGNING_KEY is None:
            # Derive a key from the secret
            key_material = hashlib.sha256(
                f"license-{settings.secret_key}".encode()
            ).digest()
            cls._SIGNING_KEY = base64.urlsafe_b64encode(key_material)
        return cls._SIGNING_KEY

    @classmethod
    def generate_license(
        cls,
        organization: str,
        tier: LicenseTier,
        valid_days: int = 365,
    ) -> str:
        """
        Generate a license key for an organization.

        This would typically be done on a separate license server,
        not on the client installation.
        """
        license_data = {
            "lid": str(uuid4()),
            "org": organization,
            "tier": tier.value,
            "iat": datetime.utcnow().isoformat(),
            "exp": (datetime.utcnow() + timedelta(days=valid_days)).isoformat(),
            "v": "1",  # License format version
        }

        # Serialize and encrypt
        json_data = json.dumps(license_data, separators=(',', ':'))
        fernet = Fernet(cls._get_signing_key())
        encrypted = fernet.encrypt(json_data.encode())

        # Add HMAC for additional integrity check
        signature = hmac.new(
            cls._get_signing_key(),
            encrypted,
            hashlib.sha256
        ).hexdigest()[:16]

        # Format: GRC-{signature}-{encrypted_base64}
        license_key = f"GRC-{signature}-{encrypted.decode()}"
        return license_key

    @classmethod
    def validate_license(cls, license_key: str) -> Optional[LicenseInfo]:
        """
        Validate a license key and return license info.

        Returns None if license is invalid.
        """
        try:
            # Parse license key format
            if not license_key.startswith("GRC-"):
                return None

            parts = license_key.split("-", 2)
            if len(parts) != 3:
                return None

            _, signature, encrypted_data = parts

            # Verify HMAC signature
            expected_sig = hmac.new(
                cls._get_signing_key(),
                encrypted_data.encode(),
                hashlib.sha256
            ).hexdigest()[:16]

            if not hmac.compare_digest(signature, expected_sig):
                return None

            # Decrypt license data
            fernet = Fernet(cls._get_signing_key())
            decrypted = fernet.decrypt(encrypted_data.encode())
            license_data = json.loads(decrypted.decode())

            # Parse dates
            issued_at = datetime.fromisoformat(license_data["iat"])
            expires_at = datetime.fromisoformat(license_data["exp"])
            now = datetime.utcnow()

            # Check expiration
            is_valid = now < expires_at
            days_remaining = max(0, (expires_at - now).days)

            # Get tier and features
            tier = LicenseTier(license_data["tier"])
            features = TIER_FEATURES[tier]

            return LicenseInfo(
                license_id=license_data["lid"],
                organization=license_data["org"],
                tier=tier,
                issued_at=issued_at,
                expires_at=expires_at,
                features=features,
                is_valid=is_valid,
                days_remaining=days_remaining,
            )

        except (InvalidToken, KeyError, ValueError, json.JSONDecodeError):
            return None

    @classmethod
    def get_community_license(cls) -> LicenseInfo:
        """Return a default community license for unlicensed installations."""
        now = datetime.utcnow()
        return LicenseInfo(
            license_id="community",
            organization="Unlicensed",
            tier=LicenseTier.COMMUNITY,
            issued_at=now,
            expires_at=now + timedelta(days=36500),  # 100 years
            features=TIER_FEATURES[LicenseTier.COMMUNITY],
            is_valid=True,
            days_remaining=36500,
        )


# Global license state (loaded at startup)
_current_license: Optional[LicenseInfo] = None


def get_current_license() -> LicenseInfo:
    """Get the current active license."""
    global _current_license
    if _current_license is None:
        _current_license = LicenseManager.get_community_license()
    return _current_license


def set_license(license_key: str) -> Optional[LicenseInfo]:
    """Set and validate a new license key."""
    global _current_license
    license_info = LicenseManager.validate_license(license_key)
    if license_info:
        _current_license = license_info
    return license_info


def check_feature(feature: str) -> bool:
    """Check if a feature is enabled by the current license."""
    license_info = get_current_license()
    return getattr(license_info.features, feature, False)


def check_limit(limit_name: str, current_count: int) -> bool:
    """Check if a limit is not exceeded (-1 means unlimited)."""
    license_info = get_current_license()
    limit = getattr(license_info.features, limit_name, 0)
    if limit == -1:
        return True
    return current_count < limit
