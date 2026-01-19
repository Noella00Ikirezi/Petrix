"""
Compliance Base Classes
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Any, Callable
from datetime import datetime


class ComplianceStatus(str, Enum):
    """Compliance check status"""
    PASS = "pass"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"
    ERROR = "error"
    MANUAL = "manual_review"


class ComplianceLevel(str, Enum):
    """CIS Profile Levels"""
    LEVEL_1 = "Level 1"  # Basic security
    LEVEL_2 = "Level 2"  # Defense in depth


@dataclass
class ComplianceResult:
    """Result of a single compliance check"""
    check_id: str
    title: str
    description: str
    status: ComplianceStatus
    level: ComplianceLevel
    category: str

    # Details
    expected: str = ""
    actual: str = ""
    remediation: str = ""
    references: list[str] = field(default_factory=list)

    # Metadata
    scored: bool = True
    automated: bool = True
    evidence: str = ""
    checked_at: datetime = field(default_factory=datetime.now)


@dataclass
class ComplianceCheck:
    """Definition of a compliance check"""
    id: str
    title: str
    description: str
    level: ComplianceLevel
    category: str
    check_func: Callable
    remediation: str = ""
    references: list[str] = field(default_factory=list)
    scored: bool = True
    automated: bool = True


class ComplianceBenchmark(ABC):
    """Base class for compliance benchmarks"""

    def __init__(self, executor=None):
        from ...platform.executor import LocalExecutor
        self.executor = executor or LocalExecutor()
        self.checks: list[ComplianceCheck] = []
        self._register_checks()

    @abstractmethod
    def _register_checks(self):
        """Register all compliance checks"""
        pass

    @property
    @abstractmethod
    def benchmark_name(self) -> str:
        """Name of the benchmark"""
        pass

    @property
    @abstractmethod
    def benchmark_version(self) -> str:
        """Version of the benchmark"""
        pass

    async def run_all_checks(
        self,
        level: ComplianceLevel = ComplianceLevel.LEVEL_1
    ) -> list[ComplianceResult]:
        """
        Run all compliance checks

        Args:
            level: Compliance level to check (Level 1 or Level 2)

        Returns:
            List of compliance results
        """
        results = []

        for check in self.checks:
            # Skip Level 2 checks if only Level 1 requested
            if level == ComplianceLevel.LEVEL_1 and check.level == ComplianceLevel.LEVEL_2:
                continue

            try:
                result = await check.check_func()
                results.append(result)
            except Exception as e:
                results.append(ComplianceResult(
                    check_id=check.id,
                    title=check.title,
                    description=check.description,
                    status=ComplianceStatus.ERROR,
                    level=check.level,
                    category=check.category,
                    evidence=str(e),
                ))

        return results

    async def run_category(
        self,
        category: str,
        level: ComplianceLevel = ComplianceLevel.LEVEL_1
    ) -> list[ComplianceResult]:
        """Run checks for a specific category"""
        results = []

        for check in self.checks:
            if check.category != category:
                continue

            if level == ComplianceLevel.LEVEL_1 and check.level == ComplianceLevel.LEVEL_2:
                continue

            try:
                result = await check.check_func()
                results.append(result)
            except Exception as e:
                results.append(ComplianceResult(
                    check_id=check.id,
                    title=check.title,
                    description=check.description,
                    status=ComplianceStatus.ERROR,
                    level=check.level,
                    category=check.category,
                    evidence=str(e),
                ))

        return results

    def get_categories(self) -> list[str]:
        """Get list of check categories"""
        return list(set(c.category for c in self.checks))

    def get_summary(self, results: list[ComplianceResult]) -> dict:
        """Get summary statistics for results"""
        total = len(results)
        passed = sum(1 for r in results if r.status == ComplianceStatus.PASS)
        failed = sum(1 for r in results if r.status == ComplianceStatus.FAIL)
        manual = sum(1 for r in results if r.status == ComplianceStatus.MANUAL)
        errors = sum(1 for r in results if r.status == ComplianceStatus.ERROR)
        na = sum(1 for r in results if r.status == ComplianceStatus.NOT_APPLICABLE)

        scored_results = [r for r in results if r.scored]
        scored_passed = sum(1 for r in scored_results if r.status == ComplianceStatus.PASS)

        compliance_score = (scored_passed / len(scored_results) * 100) if scored_results else 0

        return {
            "benchmark": self.benchmark_name,
            "version": self.benchmark_version,
            "total_checks": total,
            "passed": passed,
            "failed": failed,
            "manual_review": manual,
            "errors": errors,
            "not_applicable": na,
            "compliance_score": round(compliance_score, 1),
            "by_category": self._group_by_category(results),
        }

    def _group_by_category(self, results: list[ComplianceResult]) -> dict:
        """Group results by category"""
        by_category = {}

        for result in results:
            if result.category not in by_category:
                by_category[result.category] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                }

            by_category[result.category]["total"] += 1
            if result.status == ComplianceStatus.PASS:
                by_category[result.category]["passed"] += 1
            elif result.status == ComplianceStatus.FAIL:
                by_category[result.category]["failed"] += 1

        return by_category
