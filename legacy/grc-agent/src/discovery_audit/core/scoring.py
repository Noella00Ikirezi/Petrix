"""
Scoring Engine - Système de notation des audits
Calcule un score global basé sur les findings et génère une note A-F
"""

from .models import AuditResult, AuditScore, Finding, Severity


class ScoringEngine:
    """
    Moteur de scoring pour les audits
    Calcule des scores par catégorie et un score global
    """

    # Poids des sévérités (impact sur le score)
    SEVERITY_WEIGHTS = {
        Severity.CRITICAL: 40,
        Severity.HIGH: 25,
        Severity.MEDIUM: 10,
        Severity.LOW: 3,
        Severity.INFO: 0,
    }

    # Seuils pour les grades
    GRADE_THRESHOLDS = {
        'A': 90,  # 90-100
        'B': 75,  # 75-89
        'C': 60,  # 60-74
        'D': 40,  # 40-59
        'F': 0,   # 0-39
    }

    # Multiplicateurs par nombre de findings critiques
    CRITICAL_MULTIPLIERS = {
        0: 1.0,
        1: 0.85,
        2: 0.70,
        3: 0.55,
        5: 0.40,
        10: 0.25,
    }

    def calculate_score(self, result: AuditResult) -> AuditScore:
        """
        Calcule le score global d'un audit

        La logique:
        1. Score de base = 100
        2. Soustraire des points selon la sévérité des findings
        3. Appliquer un multiplicateur si beaucoup de critiques
        4. Calculer les scores par catégorie
        5. Déterminer le grade et le niveau de risque
        """
        # Compter les findings par sévérité
        counts = self._count_by_severity(result.findings)

        # Score de base
        base_score = 100.0

        # Pénalités par sévérité
        penalties = 0.0
        for severity, count in counts.items():
            weight = self.SEVERITY_WEIGHTS.get(severity, 0)
            penalties += count * weight

        # Limiter les pénalités à 100
        penalties = min(penalties, 100)

        # Score avant multiplicateur
        score = base_score - penalties

        # Appliquer le multiplicateur pour les critiques
        multiplier = self._get_critical_multiplier(counts.get(Severity.CRITICAL, 0))
        score = score * multiplier

        # Assurer que le score reste dans [0, 100]
        score = max(0.0, min(100.0, score))

        # Calculer les scores par catégorie
        network_score = self._calculate_category_score(result.findings, "network")
        system_score = self._calculate_category_score(result.findings, "system")
        web_score = self._calculate_category_score(result.findings, "web")

        # Déterminer le grade
        grade = self._score_to_grade(score)

        # Déterminer le niveau de risque
        risk_level = self._determine_risk_level(counts, score)

        # Générer le résumé
        summary = self._generate_summary(counts, score, grade)

        return AuditScore(
            overall_score=round(score, 1),
            grade=grade,
            network_score=round(network_score, 1),
            system_score=round(system_score, 1),
            web_score=round(web_score, 1),
            critical_count=counts.get(Severity.CRITICAL, 0),
            high_count=counts.get(Severity.HIGH, 0),
            medium_count=counts.get(Severity.MEDIUM, 0),
            low_count=counts.get(Severity.LOW, 0),
            info_count=counts.get(Severity.INFO, 0),
            risk_level=risk_level,
            summary=summary,
        )

    def _count_by_severity(self, findings: list[Finding]) -> dict[Severity, int]:
        """Compte les findings par sévérité"""
        counts: dict[Severity, int] = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 0,
            Severity.MEDIUM: 0,
            Severity.LOW: 0,
            Severity.INFO: 0,
        }

        for finding in findings:
            if not finding.false_positive:
                severity = Severity(finding.severity) if isinstance(finding.severity, str) else finding.severity
                counts[severity] = counts.get(severity, 0) + 1

        return counts

    def _get_critical_multiplier(self, critical_count: int) -> float:
        """Retourne le multiplicateur basé sur le nombre de critiques"""
        for threshold, multiplier in sorted(
            self.CRITICAL_MULTIPLIERS.items(),
            reverse=True
        ):
            if critical_count >= threshold:
                return multiplier
        return 1.0

    def _calculate_category_score(
        self,
        findings: list[Finding],
        category: str
    ) -> float:
        """Calcule le score pour une catégorie spécifique"""
        category_findings = [
            f for f in findings
            if f.category == category and not f.false_positive
        ]

        if not category_findings:
            return 100.0  # Pas de findings = score parfait

        score = 100.0
        for finding in category_findings:
            severity = Severity(finding.severity) if isinstance(finding.severity, str) else finding.severity
            weight = self.SEVERITY_WEIGHTS.get(severity, 0)
            score -= weight

        return max(0.0, min(100.0, score))

    def _score_to_grade(self, score: float) -> str:
        """Convertit un score en grade A-F"""
        for grade, threshold in sorted(
            self.GRADE_THRESHOLDS.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            if score >= threshold:
                return grade
        return 'F'

    def _determine_risk_level(
        self,
        counts: dict[Severity, int],
        score: float
    ) -> str:
        """Détermine le niveau de risque global"""
        critical = counts.get(Severity.CRITICAL, 0)
        high = counts.get(Severity.HIGH, 0)

        if critical >= 3 or score < 20:
            return "CRITICAL"
        elif critical >= 1 or high >= 5 or score < 40:
            return "HIGH"
        elif high >= 2 or score < 60:
            return "MEDIUM"
        elif score < 80:
            return "LOW"
        else:
            return "MINIMAL"

    def _generate_summary(
        self,
        counts: dict[Severity, int],
        score: float,
        grade: str
    ) -> str:
        """Génère un résumé textuel du score"""
        total = sum(counts.values())
        critical = counts.get(Severity.CRITICAL, 0)
        high = counts.get(Severity.HIGH, 0)

        if total == 0:
            return "Excellent! No security issues were found during this audit."

        if grade == 'A':
            return f"Very good security posture. {total} minor issues found, no critical vulnerabilities."

        if grade == 'B':
            return f"Good security posture with room for improvement. {total} issues found including {high} high severity."

        if grade == 'C':
            return f"Average security posture. {total} issues found including {high} high and {critical} critical. Remediation recommended."

        if grade == 'D':
            return f"Poor security posture. {total} issues found with {critical} critical vulnerabilities. Immediate action required."

        return f"Critical security posture. {total} issues found with {critical} critical vulnerabilities. Urgent remediation required!"

    def calculate_cvss_score(self, cvss_vector: str) -> float:
        """
        Calcule un score CVSS à partir d'un vecteur
        Supporte CVSS v3.1

        Example vector: CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H
        """
        # Implémentation simplifiée - en production utiliser une lib CVSS
        if not cvss_vector:
            return 0.0

        try:
            parts = cvss_vector.split('/')
            metrics = {}
            for part in parts:
                if ':' in part:
                    key, value = part.split(':')
                    metrics[key] = value

            # Calcul simplifié basé sur les métriques principales
            av_scores = {'N': 0.85, 'A': 0.62, 'L': 0.55, 'P': 0.2}
            ac_scores = {'L': 0.77, 'H': 0.44}
            pr_scores = {'N': 0.85, 'L': 0.62, 'H': 0.27}
            ui_scores = {'N': 0.85, 'R': 0.62}
            cia_scores = {'H': 0.56, 'L': 0.22, 'N': 0}

            av = av_scores.get(metrics.get('AV', 'N'), 0.85)
            ac = ac_scores.get(metrics.get('AC', 'L'), 0.77)
            pr = pr_scores.get(metrics.get('PR', 'N'), 0.85)
            ui = ui_scores.get(metrics.get('UI', 'N'), 0.85)

            c = cia_scores.get(metrics.get('C', 'N'), 0)
            i = cia_scores.get(metrics.get('I', 'N'), 0)
            a = cia_scores.get(metrics.get('A', 'N'), 0)

            # Formule simplifiée
            impact = 1 - (1 - c) * (1 - i) * (1 - a)
            exploitability = av * ac * pr * ui

            if impact <= 0:
                return 0.0

            score = min(10, (impact + exploitability) * 5)
            return round(score, 1)

        except Exception:
            return 0.0

    def severity_from_cvss(self, cvss_score: float) -> Severity:
        """Convertit un score CVSS en sévérité"""
        if cvss_score >= 9.0:
            return Severity.CRITICAL
        elif cvss_score >= 7.0:
            return Severity.HIGH
        elif cvss_score >= 4.0:
            return Severity.MEDIUM
        elif cvss_score >= 0.1:
            return Severity.LOW
        else:
            return Severity.INFO
