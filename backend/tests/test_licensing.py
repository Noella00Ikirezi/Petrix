"""Tests for license management."""
from app.core.licensing import (
    LicenseTier,
    LicenseFeatures,
    LicenseManager,
    TIER_FEATURES,
    get_current_license,
    check_feature,
    check_limit,
)


class TestTierFeatures:
    def test_community_limits(self):
        features = TIER_FEATURES[LicenseTier.COMMUNITY]
        assert features.max_assets == 50
        assert features.max_users == 3
        assert features.compliance_modules is False
        assert features.ai_assistant is False

    def test_professional_features(self):
        features = TIER_FEATURES[LicenseTier.PROFESSIONAL]
        assert features.max_assets == 500
        assert features.compliance_modules is True
        assert features.ai_assistant is True

    def test_enterprise_unlimited(self):
        features = TIER_FEATURES[LicenseTier.ENTERPRISE]
        assert features.max_assets == -1
        assert features.max_users == -1
        assert features.sso_integration is True
        assert features.priority_support is True


class TestLicenseManager:
    def test_generate_license_format(self):
        key = LicenseManager.generate_license("TestOrg", LicenseTier.PROFESSIONAL)
        assert key.startswith("PTX-")
        parts = key.split("-", 2)
        assert len(parts) == 3

    def test_validate_roundtrip(self):
        key = LicenseManager.generate_license("TestOrg", LicenseTier.ENTERPRISE)
        info = LicenseManager.validate_license(key)
        assert info is not None
        assert info.organization == "TestOrg"
        assert info.tier == LicenseTier.ENTERPRISE
        assert info.is_valid is True

    def test_validate_invalid_key(self):
        result = LicenseManager.validate_license("INVALID-KEY")
        assert result is None

    def test_validate_garbage(self):
        result = LicenseManager.validate_license("not-a-license-at-all")
        assert result is None

    def test_community_license_defaults(self):
        info = LicenseManager.get_community_license()
        assert info.tier == LicenseTier.COMMUNITY
        assert info.organization == "Unlicensed"
        assert info.is_valid is True
        assert info.features.max_assets == 50


class TestCheckLimit:
    def test_community_asset_limit_within(self):
        # Community license has max_assets=50, so 49 < 50 passes
        assert check_limit("max_assets", 49) is True

    def test_community_asset_limit_exceeded(self):
        # 50 is not < 50, so this should fail
        assert check_limit("max_assets", 50) is False

    def test_check_feature_api_access(self):
        # Community license has api_access=True
        assert check_feature("api_access") is True

    def test_check_feature_ai_disabled_community(self):
        assert check_feature("ai_assistant") is False
