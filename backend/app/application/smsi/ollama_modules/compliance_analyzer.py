"""
Analyseur de Conformité SMSI
Analyse des documents existants contre les exigences réglementaires
"""
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict

sys.path.append(str(Path(__file__).parent.parent))
from config.settings import ANALYSES_DIR
from modules.ollama_client import OllamaClient


@dataclass
class ComplianceGap:
    """Représente un écart de conformité identifié"""
    requirement_ref: str
    requirement_text: str
    expected: str
    found: str
    score: int  # 0-5
    gap_type: str  # major_nc, minor_nc, observation, compliant
    recommendation: str
    priority: str
    effort: str


@dataclass
class ComplianceReport:
    """Rapport de conformité complet"""
    document_name: str
    analysis_date: str
    requirements_analyzed: List[str]
    overall_score: float
    risk_level: str
    gaps: List[ComplianceGap]
    summary: str
    action_plan: List[Dict]


class ComplianceAnalyzer:
    """
    Analyseur de conformité documentaire

    Usage:
        analyzer = ComplianceAnalyzer()
        report = analyzer.analyze_document(
            document_content="...",
            requirements=["A.9.1.1", "A.9.2.1"]
        )
        analyzer.save_report(report)
    """

    SYSTEM_PROMPT = """# RÔLE
Tu es un auditeur ISO 27001 Lead Auditor certifié avec 10 ans d'expérience en :
- Audit de conformité multi-référentiel (ISO 27001, RGPD, PCI-DSS, NIS2)
- Gap analysis et évaluation de maturité CMMI
- Identification des non-conformités selon ISO 19011

# PRINCIPES D'AUDIT

1. **Objectivité** : Base-toi uniquement sur les preuves documentaires
2. **Traçabilité** : Chaque constat doit référencer une exigence précise
3. **Proportionnalité** : Évalue la gravité en fonction du risque business
4. **Constructivité** : Chaque écart doit avoir une recommandation actionnable

# GRILLE D'ÉVALUATION DE MATURITÉ

| Score | Niveau | Critères |
|-------|--------|----------|
| 0 | Inexistant | Aucune mesure, pas de documentation |
| 1 | Initial | Mesures ad-hoc, non répétables, non documentées |
| 2 | Géré | Documenté mais application incohérente |
| 3 | Défini | Standardisé, documenté, communiqué, appliqué |
| 4 | Maîtrisé | Mesuré, surveillé, indicateurs en place |
| 5 | Optimisé | Amélioration continue, benchmarking |

# CLASSIFICATION DES CONSTATS

- **Non-conformité majeure** : Absence totale ou échec systémique d'une exigence
- **Non-conformité mineure** : Écart ponctuel ou partiel
- **Observation** : Point d'amélioration, non bloquant
- **Conforme** : Exigence satisfaite avec preuves"""

    ANALYSIS_PROMPT = """# DOCUMENT À ANALYSER

```
{document_content}
```

# EXIGENCES À VÉRIFIER

{requirements_text}

# INSTRUCTIONS D'ANALYSE

Pour CHAQUE exigence listée ci-dessus, tu DOIS fournir une analyse structurée.

# FORMAT DE SORTIE OBLIGATOIRE (JSON)

Réponds UNIQUEMENT avec un JSON valide, sans texte avant ou après :

```json
{{
  "overall_score": 3.5,
  "risk_level": "Modéré",
  "summary": "Synthèse en 2-3 phrases",
  "gaps": [
    {{
      "requirement_ref": "A.9.1.1",
      "requirement_text": "Texte de l'exigence",
      "expected": "Ce qui est attendu selon la norme",
      "found": "Ce qui a été constaté dans le document",
      "score": 3,
      "gap_type": "minor_nc",
      "recommendation": "Action corrective recommandée",
      "priority": "high",
      "effort": "medium"
    }}
  ],
  "action_plan": [
    {{
      "priority": 1,
      "action": "Description de l'action",
      "responsible": "Rôle suggéré",
      "deadline": "Court terme (1-3 mois)",
      "deliverable": "Livrable attendu"
    }}
  ]
}}
```

# RÈGLES

- gap_type : "major_nc", "minor_nc", "observation", ou "compliant"
- priority : "critical", "high", "medium", ou "low"
- effort : "low", "medium", ou "high"
- score : entier de 0 à 5
- overall_score : moyenne pondérée des scores (float)
- risk_level : "Critique", "Élevé", "Modéré", ou "Faible"

Analyse maintenant le document :"""

    # Base de connaissances des exigences ISO 27001:2022
    REQUIREMENTS_DB = {
        "A.5.1": {
            "title": "Politiques de sécurité de l'information",
            "text": "Des politiques de sécurité de l'information doivent être définies, approuvées par la direction, publiées et communiquées.",
            "controls": ["Existence d'une politique", "Approbation direction", "Diffusion", "Revue périodique"]
        },
        "A.5.2": {
            "title": "Rôles et responsabilités",
            "text": "Les rôles et responsabilités en matière de sécurité doivent être définis et attribués.",
            "controls": ["Organigramme sécurité", "Fiches de poste", "RACI", "Nominations formelles"]
        },
        "A.9.1.1": {
            "title": "Politique de contrôle d'accès",
            "text": "Une politique de contrôle d'accès doit être établie, documentée et revue sur la base des exigences métier et de sécurité.",
            "controls": ["Politique documentée", "Principe du moindre privilège", "Revue des accès", "Processus d'autorisation"]
        },
        "A.9.2.1": {
            "title": "Enregistrement et désinscription des utilisateurs",
            "text": "Un processus formel d'enregistrement et de désinscription des utilisateurs doit être mis en œuvre.",
            "controls": ["Processus d'onboarding", "Processus d'offboarding", "Traçabilité", "Délais"]
        },
        "A.9.2.3": {
            "title": "Gestion des droits d'accès à privilèges",
            "text": "L'attribution et l'utilisation des droits d'accès à privilèges doivent être restreintes et contrôlées.",
            "controls": ["Inventaire comptes privilégiés", "Justification", "Revue trimestrielle", "Journalisation"]
        },
        "A.9.4.2": {
            "title": "Procédures de connexion sécurisées",
            "text": "L'accès aux systèmes doit être contrôlé par des procédures de connexion sécurisées.",
            "controls": ["MFA", "Verrouillage après échecs", "Timeout", "Journalisation"]
        },
        "A.12.4.1": {
            "title": "Journalisation des événements",
            "text": "Des journaux d'événements enregistrant les activités des utilisateurs, exceptions et événements de sécurité doivent être créés, conservés et régulièrement revus.",
            "controls": ["Événements journalisés", "Durée de rétention", "Protection des logs", "Revue régulière"]
        },
        "A.8.2.1": {
            "title": "Classification de l'information",
            "text": "L'information doit être classifiée en termes d'exigences légales, de valeur, de criticité et de sensibilité.",
            "controls": ["Schéma de classification", "Critères définis", "Attribution", "Revue"]
        },
    }

    def __init__(self, client: OllamaClient = None):
        self.client = client or OllamaClient()

    def _get_requirements_text(self, requirements: List[str]) -> str:
        """Génère le texte des exigences à vérifier"""
        text_parts = []
        for req_ref in requirements:
            req = self.REQUIREMENTS_DB.get(req_ref, {})
            if req:
                text_parts.append(f"""
## {req_ref} - {req.get('title', 'N/A')}
**Exigence** : {req.get('text', 'Non défini')}
**Points de contrôle** :
{chr(10).join(f'- {c}' for c in req.get('controls', []))}
""")
            else:
                text_parts.append(f"""
## {req_ref}
**Exigence** : Vérifier la conformité à cette mesure ISO 27001:2022
""")
        return "\n".join(text_parts)

    def analyze_document(
        self,
        document_content: str,
        requirements: List[str],
        document_name: str = "Document analysé"
    ) -> ComplianceReport:
        """
        Analyse un document contre des exigences de conformité

        Args:
            document_content: Contenu du document à analyser
            requirements: Liste des références ISO à vérifier (ex: ["A.9.1.1", "A.9.2.1"])
            document_name: Nom du document pour le rapport

        Returns:
            ComplianceReport avec les résultats d'analyse
        """
        print(f"🔍 Analyse de conformité : {document_name}")
        print(f"   Exigences vérifiées : {', '.join(requirements)}")

        requirements_text = self._get_requirements_text(requirements)

        prompt = self.ANALYSIS_PROMPT.format(
            document_content=document_content[:8000],  # Limiter la taille
            requirements_text=requirements_text
        )

        response = self.client.generate(
            prompt=prompt,
            system=self.SYSTEM_PROMPT,
            task_type="analysis"
        )

        if not response.success:
            print(f"❌ Erreur d'analyse : {response.error}")
            return self._create_error_report(document_name, requirements, response.error)

        # Parser le JSON de la réponse
        try:
            # Extraire le JSON de la réponse
            content = response.content
            # Chercher le JSON dans la réponse
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                data = json.loads(json_str)
            else:
                raise ValueError("Pas de JSON trouvé dans la réponse")

            # Construire le rapport
            gaps = [
                ComplianceGap(**gap) for gap in data.get("gaps", [])
            ]

            report = ComplianceReport(
                document_name=document_name,
                analysis_date=datetime.now().isoformat(),
                requirements_analyzed=requirements,
                overall_score=data.get("overall_score", 0),
                risk_level=data.get("risk_level", "Non évalué"),
                gaps=gaps,
                summary=data.get("summary", ""),
                action_plan=data.get("action_plan", [])
            )

            print(f"✅ Analyse terminée - Score global : {report.overall_score}/5")
            return report

        except json.JSONDecodeError as e:
            print(f"⚠️  Erreur de parsing JSON : {e}")
            # Retourner un rapport avec la réponse brute
            return self._create_error_report(
                document_name, requirements,
                f"Erreur de parsing. Réponse brute:\n{response.content[:1000]}"
            )

    def _create_error_report(
        self,
        document_name: str,
        requirements: List[str],
        error: str
    ) -> ComplianceReport:
        """Crée un rapport d'erreur"""
        return ComplianceReport(
            document_name=document_name,
            analysis_date=datetime.now().isoformat(),
            requirements_analyzed=requirements,
            overall_score=0,
            risk_level="Non évalué",
            gaps=[],
            summary=f"Erreur lors de l'analyse : {error}",
            action_plan=[]
        )

    def analyze_file(
        self,
        filepath: str,
        requirements: List[str]
    ) -> ComplianceReport:
        """
        Analyse un fichier document

        Args:
            filepath: Chemin vers le fichier à analyser
            requirements: Liste des exigences à vérifier

        Returns:
            ComplianceReport
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Fichier non trouvé : {filepath}")

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        return self.analyze_document(
            document_content=content,
            requirements=requirements,
            document_name=path.name
        )

    def format_report_markdown(self, report: ComplianceReport) -> str:
        """Formate le rapport en Markdown"""
        lines = [
            f"# Rapport d'Analyse de Conformité",
            f"",
            f"## Informations générales",
            f"| Élément | Valeur |",
            f"|---------|--------|",
            f"| **Document analysé** | {report.document_name} |",
            f"| **Date d'analyse** | {report.analysis_date} |",
            f"| **Exigences vérifiées** | {', '.join(report.requirements_analyzed)} |",
            f"| **Score global** | {report.overall_score}/5 |",
            f"| **Niveau de risque** | {report.risk_level} |",
            f"",
            f"## Synthèse",
            f"{report.summary}",
            f"",
            f"## Détail des écarts",
            f""
        ]

        # Compteurs
        major_nc = sum(1 for g in report.gaps if g.gap_type == "major_nc")
        minor_nc = sum(1 for g in report.gaps if g.gap_type == "minor_nc")
        observations = sum(1 for g in report.gaps if g.gap_type == "observation")
        compliant = sum(1 for g in report.gaps if g.gap_type == "compliant")

        lines.extend([
            f"### Statistiques",
            f"- Non-conformités majeures : **{major_nc}**",
            f"- Non-conformités mineures : **{minor_nc}**",
            f"- Observations : **{observations}**",
            f"- Points conformes : **{compliant}**",
            f""
        ])

        # Détail de chaque écart
        for gap in report.gaps:
            status_emoji = {
                "major_nc": "🔴",
                "minor_nc": "🟠",
                "observation": "🟡",
                "compliant": "🟢"
            }.get(gap.gap_type, "⚪")

            lines.extend([
                f"### {status_emoji} {gap.requirement_ref}",
                f"**Exigence** : {gap.requirement_text}",
                f"",
                f"| Critère | Évaluation |",
                f"|---------|------------|",
                f"| Attendu | {gap.expected} |",
                f"| Constaté | {gap.found} |",
                f"| Score | {gap.score}/5 |",
                f"| Type | {gap.gap_type} |",
                f"| Priorité | {gap.priority} |",
                f"| Effort | {gap.effort} |",
                f"",
                f"**Recommandation** : {gap.recommendation}",
                f""
            ])

        # Plan d'action
        if report.action_plan:
            lines.extend([
                f"## Plan d'action recommandé",
                f"",
                f"| # | Action | Responsable | Échéance | Livrable |",
                f"|---|--------|-------------|----------|----------|"
            ])
            for action in report.action_plan:
                lines.append(
                    f"| {action.get('priority', '-')} | {action.get('action', '-')} | "
                    f"{action.get('responsible', '-')} | {action.get('deadline', '-')} | "
                    f"{action.get('deliverable', '-')} |"
                )

        lines.extend([
            f"",
            f"---",
            f"*Rapport généré automatiquement - À valider par un auditeur qualifié*"
        ])

        return "\n".join(lines)

    def save_report(
        self,
        report: ComplianceReport,
        output_dir: Path = None,
        format: str = "both"
    ) -> Tuple[Path, Path]:
        """
        Sauvegarde le rapport d'analyse

        Args:
            report: Rapport à sauvegarder
            output_dir: Répertoire de sortie
            format: "json", "markdown", ou "both"

        Returns:
            Tuple des chemins créés (json_path, md_path)
        """
        output_dir = output_dir or ANALYSES_DIR
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"compliance_report_{date_str}"

        json_path = None
        md_path = None

        if format in ("json", "both"):
            json_path = output_dir / f"{base_name}.json"
            # Convertir le rapport en dict serializable
            report_dict = {
                "document_name": report.document_name,
                "analysis_date": report.analysis_date,
                "requirements_analyzed": report.requirements_analyzed,
                "overall_score": report.overall_score,
                "risk_level": report.risk_level,
                "gaps": [asdict(g) for g in report.gaps],
                "summary": report.summary,
                "action_plan": report.action_plan
            }
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, indent=2, ensure_ascii=False)
            print(f"💾 Rapport JSON : {json_path}")

        if format in ("markdown", "both"):
            md_path = output_dir / f"{base_name}.md"
            md_content = self.format_report_markdown(report)
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            print(f"💾 Rapport Markdown : {md_path}")

        return json_path, md_path


# Test
if __name__ == "__main__":
    analyzer = ComplianceAnalyzer()

    # Document de test
    test_document = """
    # Politique de Contrôle d'Accès
    Version 1.0 - Janvier 2024

    ## 1. Objet
    Cette politique définit les règles de contrôle d'accès au système d'information.

    ## 2. Principes
    - Les accès sont accordés selon le principe du besoin d'en connaître
    - Chaque utilisateur dispose d'un compte nominatif

    ## 3. Gestion des accès
    Les demandes d'accès sont validées par le manager.
    Les comptes sont désactivés au départ du collaborateur.

    ## 4. Comptes à privilèges
    Les comptes administrateurs sont limités au strict nécessaire.
    """

    print("=" * 60)
    print("TEST : Analyse de conformité")
    print("=" * 60)

    report = analyzer.analyze_document(
        document_content=test_document,
        requirements=["A.9.1.1", "A.9.2.1", "A.9.2.3"],
        document_name="Politique_Controle_Acces_v1.md"
    )

    # Afficher le rapport
    print("\n" + "=" * 60)
    print("RAPPORT DE CONFORMITÉ")
    print("=" * 60)
    print(analyzer.format_report_markdown(report))

    # Sauvegarder
    analyzer.save_report(report)
