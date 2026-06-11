"""
Automatisation des Audits SMSI
Génère des rapports d'audit et des analyses de maturité à partir de la matrice de conformité
"""
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
from collections import defaultdict

sys.path.append(str(Path(__file__).parent.parent))
from config.settings import (
    AUDITS_DIR, ORGANIZATION
)
from modules.ollama_client import OllamaClient


@dataclass
class AuditMeasure:
    """Représente une mesure à auditer"""
    ref: str
    domain: str
    measure: str
    description: str
    applicable: bool
    status: str  # À créer, En cours, Validé
    priority: str
    rgpd: str = ""
    pci_dss: str = ""
    iso_22301: str = ""
    nis2: str = ""
    ai_act: str = ""
    evidence: str = ""
    maturity_score: int = 0


@dataclass
class DomainStats:
    """Statistiques par domaine"""
    domain: str
    domain_name: str
    total: int
    validated: int
    in_progress: int
    to_create: int
    compliance_rate: float
    avg_maturity: float


@dataclass
class AuditReport:
    """Rapport d'audit complet"""
    audit_date: str
    organization: str
    scope: str
    total_measures: int
    applicable_measures: int
    validated: int
    in_progress: int
    to_create: int
    overall_compliance: float
    overall_maturity: float
    risk_level: str
    domain_stats: List[DomainStats]
    critical_gaps: List[AuditMeasure]
    quick_wins: List[AuditMeasure]
    roadmap: List[Dict]
    executive_summary: str
    recommendations: List[str]


class AuditAutomation:
    """
    Automatisation des audits SMSI

    Usage:
        audit = AuditAutomation()
        report = audit.analyze_matrix("path/to/matrix.csv")
        audit.generate_report(report)
    """

    SYSTEM_PROMPT = """# RÔLE
Tu es un directeur d'audit certifié ISO 27001 Lead Auditor avec 15 ans d'expérience.
Tu analyses les données de conformité SMSI pour produire des rapports d'audit stratégiques.

# MISSION
Analyser les statistiques de conformité fournies et produire :
1. Une synthèse exécutive claire et impactante
2. Des recommandations stratégiques priorisées
3. Une analyse des risques business

# STYLE
- Professionnel et factuel
- Orienté décision pour la direction
- Quantifié avec des métriques précises
- Français soutenu"""

    ANALYSIS_PROMPT = """# DONNÉES D'AUDIT

## Statistiques globales
- Organisation : {organization}
- Périmètre : {scope}
- Date d'audit : {audit_date}
- Mesures totales : {total_measures}
- Mesures applicables : {applicable_measures}
- Mesures validées : {validated} ({validated_pct:.1f}%)
- Mesures en cours : {in_progress} ({in_progress_pct:.1f}%)
- Mesures à créer : {to_create} ({to_create_pct:.1f}%)
- Taux de conformité global : {compliance_rate:.1f}%
- Maturité moyenne : {maturity:.1f}/5

## Conformité par domaine
{domain_details}

## Écarts critiques (priorité haute, non validés)
{critical_gaps}

## Quick wins identifiés (effort faible, impact élevé)
{quick_wins}

# TÂCHE

Génère un rapport d'audit structuré avec :

1. **SYNTHÈSE EXÉCUTIVE** (3-4 paragraphes)
   - État actuel de la conformité
   - Risques majeurs identifiés
   - Message clé pour la direction

2. **ANALYSE DES RISQUES**
   - Risque de non-conformité réglementaire (RGPD, NIS2)
   - Risque opérationnel
   - Impact business potentiel

3. **RECOMMANDATIONS STRATÉGIQUES** (5-7 recommandations)
   Pour chaque recommandation :
   - Titre court
   - Justification
   - Actions clés
   - Bénéfice attendu
   - Priorité (1-5)

4. **ROADMAP SUGGÉRÉE**
   - Phase 1 (0-3 mois) : Actions urgentes
   - Phase 2 (3-6 mois) : Consolidation
   - Phase 3 (6-12 mois) : Optimisation

Réponds en JSON structuré :
```json
{{
  "executive_summary": "...",
  "risk_analysis": {{
    "regulatory_risk": "Critique/Élevé/Modéré/Faible",
    "operational_risk": "...",
    "business_impact": "..."
  }},
  "recommendations": [
    {{
      "title": "...",
      "justification": "...",
      "actions": ["...", "..."],
      "benefit": "...",
      "priority": 1
    }}
  ],
  "roadmap": {{
    "phase1": ["...", "..."],
    "phase2": ["...", "..."],
    "phase3": ["...", "..."]
  }}
}}
```"""

    # Mapping des domaines ISO 27001:2022
    DOMAIN_NAMES = {
        "A.5": "Mesures organisationnelles",
        "A.6": "Mesures relatives aux personnes",
        "A.7": "Mesures physiques",
        "A.8": "Mesures technologiques",
        # Legacy ISO 27001:2013
        "A.5 ": "Politiques de sécurité",
        "A.6 ": "Organisation de la sécurité",
        "A.7 ": "Sécurité des ressources humaines",
        "A.8 ": "Gestion des actifs",
        "A.9": "Contrôle d'accès",
        "A.10": "Cryptographie",
        "A.11": "Sécurité physique",
        "A.12": "Sécurité d'exploitation",
        "A.13": "Sécurité des communications",
        "A.14": "Acquisition et développement",
        "A.15": "Relations fournisseurs",
        "A.16": "Gestion des incidents",
        "A.17": "Continuité d'activité",
        "A.18": "Conformité",
    }

    def __init__(self, client: OllamaClient = None):
        self.client = client or OllamaClient()

    def load_matrix_csv(self, filepath: str) -> List[AuditMeasure]:
        """
        Charge la matrice de conformité depuis un fichier CSV

        Args:
            filepath: Chemin vers le fichier CSV

        Returns:
            Liste des mesures à auditer
        """
        measures = []
        path = Path(filepath)

        if not path.exists():
            raise FileNotFoundError(f"Fichier non trouvé : {filepath}")

        with open(path, 'r', encoding='utf-8') as f:
            # Détecter le délimiteur
            sample = f.read(1024)
            f.seek(0)
            delimiter = ';' if ';' in sample else ','

            reader = csv.DictReader(f, delimiter=delimiter)

            for row in reader:
                # Ignorer les lignes de titre de domaine (pas de mesure)
                ref = row.get('Ref', row.get('ref', '')).strip()
                if not ref or ref in self.DOMAIN_NAMES:
                    continue

                # Parser le statut
                status_raw = row.get('Statut', row.get('statut', 'À créer')).strip().lower()
                if 'valid' in status_raw:
                    status = 'Validé'
                elif 'cours' in status_raw:
                    status = 'En cours'
                else:
                    status = 'À créer'

                # Parser applicable
                applicable_raw = row.get('Applicable', row.get('applicable', 'Oui')).strip().lower()
                applicable = applicable_raw in ('oui', 'yes', 'o', 'y', '1', 'true')

                measure = AuditMeasure(
                    ref=ref,
                    domain=self._extract_domain(ref),
                    measure=row.get('Mesure ISO 27001:2013', row.get('Domaine / Mesure', row.get('mesure', ''))).strip(),
                    description=row.get('Description', row.get('description', '')).strip(),
                    applicable=applicable,
                    status=status,
                    priority=row.get('Priorité', row.get('Priorite', row.get('priorite', 'Moyenne'))).strip(),
                    rgpd=row.get('RGPD', ''),
                    pci_dss=row.get('PCI-DSS v4', row.get('PCI-DSS', '')),
                    iso_22301=row.get('ISO 22301', ''),
                    nis2=row.get('NIS2', ''),
                    ai_act=row.get('AI Act', ''),
                    evidence=row.get('Preuves', row.get('preuves', '')),
                    maturity_score=self._parse_maturity(row.get('Maturité', row.get('maturite', '0')))
                )
                measures.append(measure)

        print(f"📊 {len(measures)} mesures chargées depuis {filepath}")
        return measures

    def _extract_domain(self, ref: str) -> str:
        """Extrait le domaine d'une référence (A.5.1.1 -> A.5)"""
        parts = ref.split('.')
        if len(parts) >= 2:
            return f"{parts[0]}.{parts[1]}"
        return ref

    def _parse_maturity(self, value: str) -> int:
        """Parse une valeur de maturité"""
        try:
            return int(float(value.strip()))
        except (ValueError, AttributeError):
            return 0

    def calculate_statistics(self, measures: List[AuditMeasure]) -> AuditReport:
        """
        Calcule les statistiques d'audit

        Args:
            measures: Liste des mesures

        Returns:
            AuditReport avec les statistiques
        """
        # Filtrer les mesures applicables
        applicable = [m for m in measures if m.applicable]

        # Stats globales
        total = len(measures)
        total_applicable = len(applicable)
        validated = sum(1 for m in applicable if m.status == 'Validé')
        in_progress = sum(1 for m in applicable if m.status == 'En cours')
        to_create = sum(1 for m in applicable if m.status == 'À créer')

        compliance_rate = (validated / total_applicable * 100) if total_applicable > 0 else 0

        # Maturité moyenne
        maturity_scores = [m.maturity_score for m in applicable if m.maturity_score > 0]
        avg_maturity = sum(maturity_scores) / len(maturity_scores) if maturity_scores else 0

        # Stats par domaine
        domain_measures = defaultdict(list)
        for m in applicable:
            domain_measures[m.domain].append(m)

        domain_stats = []
        for domain, domain_list in sorted(domain_measures.items()):
            d_validated = sum(1 for m in domain_list if m.status == 'Validé')
            d_in_progress = sum(1 for m in domain_list if m.status == 'En cours')
            d_to_create = sum(1 for m in domain_list if m.status == 'À créer')
            d_total = len(domain_list)
            d_compliance = (d_validated / d_total * 100) if d_total > 0 else 0
            d_maturity_scores = [m.maturity_score for m in domain_list if m.maturity_score > 0]
            d_avg_maturity = sum(d_maturity_scores) / len(d_maturity_scores) if d_maturity_scores else 0

            domain_stats.append(DomainStats(
                domain=domain,
                domain_name=self.DOMAIN_NAMES.get(domain, domain),
                total=d_total,
                validated=d_validated,
                in_progress=d_in_progress,
                to_create=d_to_create,
                compliance_rate=d_compliance,
                avg_maturity=d_avg_maturity
            ))

        # Écarts critiques (haute priorité, non validés)
        critical_gaps = [
            m for m in applicable
            if m.status != 'Validé' and m.priority.lower() in ('haute', 'high', 'critique', 'critical')
        ]

        # Quick wins (priorité haute ou moyenne, mais faciles)
        quick_wins = [
            m for m in applicable
            if m.status == 'À créer' and m.priority.lower() in ('moyenne', 'medium', 'basse', 'low')
        ][:10]  # Limiter à 10

        # Niveau de risque
        if compliance_rate < 30:
            risk_level = "Critique"
        elif compliance_rate < 50:
            risk_level = "Élevé"
        elif compliance_rate < 70:
            risk_level = "Modéré"
        else:
            risk_level = "Faible"

        return AuditReport(
            audit_date=datetime.now().strftime("%d/%m/%Y"),
            organization=ORGANIZATION.get("name", "Non défini"),
            scope=ORGANIZATION.get("scope", "SMSI"),
            total_measures=total,
            applicable_measures=total_applicable,
            validated=validated,
            in_progress=in_progress,
            to_create=to_create,
            overall_compliance=compliance_rate,
            overall_maturity=avg_maturity,
            risk_level=risk_level,
            domain_stats=domain_stats,
            critical_gaps=critical_gaps,
            quick_wins=quick_wins,
            roadmap=[],
            executive_summary="",
            recommendations=[]
        )

    def generate_ai_analysis(self, report: AuditReport) -> AuditReport:
        """
        Enrichit le rapport avec une analyse IA

        Args:
            report: Rapport avec statistiques

        Returns:
            Rapport enrichi avec synthèse et recommandations
        """
        # Préparer les données pour le prompt
        domain_details = "\n".join([
            f"- **{d.domain} - {d.domain_name}** : {d.compliance_rate:.0f}% "
            f"({d.validated}/{d.total} validé, {d.to_create} à créer)"
            for d in report.domain_stats
        ])

        critical_gaps_text = "\n".join([
            f"- {m.ref} : {m.measure} [Priorité: {m.priority}]"
            for m in report.critical_gaps[:15]
        ]) or "Aucun écart critique identifié"

        quick_wins_text = "\n".join([
            f"- {m.ref} : {m.measure}"
            for m in report.quick_wins[:10]
        ]) or "Aucun quick win identifié"

        prompt = self.ANALYSIS_PROMPT.format(
            organization=report.organization,
            scope=report.scope,
            audit_date=report.audit_date,
            total_measures=report.total_measures,
            applicable_measures=report.applicable_measures,
            validated=report.validated,
            validated_pct=(report.validated / report.applicable_measures * 100) if report.applicable_measures else 0,
            in_progress=report.in_progress,
            in_progress_pct=(report.in_progress / report.applicable_measures * 100) if report.applicable_measures else 0,
            to_create=report.to_create,
            to_create_pct=(report.to_create / report.applicable_measures * 100) if report.applicable_measures else 0,
            compliance_rate=report.overall_compliance,
            maturity=report.overall_maturity,
            domain_details=domain_details,
            critical_gaps=critical_gaps_text,
            quick_wins=quick_wins_text
        )

        print("🤖 Génération de l'analyse IA...")

        response = self.client.generate(
            prompt=prompt,
            system=self.SYSTEM_PROMPT,
            task_type="audit"
        )

        if response.success:
            try:
                # Extraire le JSON
                content = response.content
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                    data = json.loads(json_str)

                    report.executive_summary = data.get("executive_summary", "")
                    report.recommendations = [
                        f"**{r.get('title', '')}** (Priorité {r.get('priority', '-')})\n"
                        f"  - Justification : {r.get('justification', '')}\n"
                        f"  - Bénéfice : {r.get('benefit', '')}"
                        for r in data.get("recommendations", [])
                    ]

                    roadmap = data.get("roadmap", {})
                    report.roadmap = [
                        {"phase": "Phase 1 (0-3 mois)", "actions": roadmap.get("phase1", [])},
                        {"phase": "Phase 2 (3-6 mois)", "actions": roadmap.get("phase2", [])},
                        {"phase": "Phase 3 (6-12 mois)", "actions": roadmap.get("phase3", [])}
                    ]

                    print("✅ Analyse IA terminée")

            except (json.JSONDecodeError, KeyError) as e:
                print(f"⚠️  Erreur parsing IA : {e}")
                report.executive_summary = response.content[:1000]

        return report

    def format_report_markdown(self, report: AuditReport) -> str:
        """Formate le rapport en Markdown"""
        # Barre de progression textuelle
        def progress_bar(pct):
            filled = int(pct / 10)
            return f"[{'█' * filled}{'░' * (10 - filled)}] {pct:.0f}%"

        lines = [
            f"# Rapport d'Audit SMSI",
            f"",
            f"## Informations générales",
            f"",
            f"| Élément | Valeur |",
            f"|---------|--------|",
            f"| **Organisation** | {report.organization} |",
            f"| **Périmètre** | {report.scope} |",
            f"| **Date d'audit** | {report.audit_date} |",
            f"| **Niveau de risque** | **{report.risk_level}** |",
            f"",
            f"---",
            f"",
            f"## 1. Synthèse Exécutive",
            f"",
            report.executive_summary or "*Synthèse non générée*",
            f"",
            f"---",
            f"",
            f"## 2. Dashboard de Conformité",
            f"",
            f"### 2.1 Vue d'ensemble",
            f"",
            f"| Indicateur | Valeur |",
            f"|------------|--------|",
            f"| Mesures totales | {report.total_measures} |",
            f"| Mesures applicables | {report.applicable_measures} |",
            f"| **Taux de conformité** | **{report.overall_compliance:.1f}%** |",
            f"| Maturité moyenne | {report.overall_maturity:.1f}/5 |",
            f"",
            f"### 2.2 Répartition des statuts",
            f"",
            f"```",
            f"Validé     {progress_bar(report.validated / report.applicable_measures * 100 if report.applicable_measures else 0)} ({report.validated})",
            f"En cours   {progress_bar(report.in_progress / report.applicable_measures * 100 if report.applicable_measures else 0)} ({report.in_progress})",
            f"À créer    {progress_bar(report.to_create / report.applicable_measures * 100 if report.applicable_measures else 0)} ({report.to_create})",
            f"```",
            f"",
            f"### 2.3 Conformité par domaine",
            f"",
            f"| Domaine | Nom | Conformité | Validé | En cours | À créer |",
            f"|---------|-----|------------|--------|----------|---------|"
        ]

        for d in report.domain_stats:
            lines.append(
                f"| {d.domain} | {d.domain_name} | {progress_bar(d.compliance_rate)} | "
                f"{d.validated} | {d.in_progress} | {d.to_create} |"
            )

        lines.extend([
            f"",
            f"---",
            f"",
            f"## 3. Écarts Critiques",
            f"",
            f"Les mesures suivantes présentent un risque élevé et nécessitent une attention immédiate :",
            f"",
            f"| Réf. | Mesure | Priorité | Mapping réglementaire |",
            f"|------|--------|----------|----------------------|"
        ])

        for gap in report.critical_gaps[:20]:
            mapping = []
            if gap.rgpd:
                mapping.append(f"RGPD {gap.rgpd}")
            if gap.nis2:
                mapping.append(f"NIS2 {gap.nis2}")
            if gap.pci_dss:
                mapping.append(f"PCI-DSS {gap.pci_dss}")
            mapping_str = ", ".join(mapping) or "-"
            lines.append(f"| {gap.ref} | {gap.measure[:50]}... | {gap.priority} | {mapping_str} |")

        lines.extend([
            f"",
            f"---",
            f"",
            f"## 4. Quick Wins",
            f"",
            f"Actions à fort impact et faible effort :",
            f""
        ])

        for i, qw in enumerate(report.quick_wins[:10], 1):
            lines.append(f"{i}. **{qw.ref}** - {qw.measure}")

        lines.extend([
            f"",
            f"---",
            f"",
            f"## 5. Recommandations Stratégiques",
            f""
        ])

        for i, rec in enumerate(report.recommendations, 1):
            lines.append(f"### Recommandation {i}")
            lines.append(rec)
            lines.append("")

        lines.extend([
            f"---",
            f"",
            f"## 6. Roadmap de Mise en Conformité",
            f""
        ])

        for phase in report.roadmap:
            lines.append(f"### {phase.get('phase', 'Phase')}")
            for action in phase.get('actions', []):
                lines.append(f"- [ ] {action}")
            lines.append("")

        lines.extend([
            f"---",
            f"",
            f"*Rapport généré automatiquement le {datetime.now().strftime('%d/%m/%Y à %H:%M')}*",
            f"",
            f"*Ce rapport doit être validé par un auditeur qualifié.*"
        ])

        return "\n".join(lines)

    def analyze_matrix(
        self,
        matrix_path: str,
        generate_ai: bool = True
    ) -> AuditReport:
        """
        Analyse complète d'une matrice de conformité

        Args:
            matrix_path: Chemin vers le fichier CSV
            generate_ai: Générer l'analyse IA (recommandations, synthèse)

        Returns:
            AuditReport complet
        """
        # Charger les données
        measures = self.load_matrix_csv(matrix_path)

        # Calculer les statistiques
        report = self.calculate_statistics(measures)

        # Enrichir avec l'IA si demandé
        if generate_ai:
            report = self.generate_ai_analysis(report)

        return report

    def save_report(
        self,
        report: AuditReport,
        output_dir: Path = None
    ) -> Tuple[Path, Path]:
        """
        Sauvegarde le rapport d'audit

        Args:
            report: Rapport à sauvegarder
            output_dir: Répertoire de sortie

        Returns:
            Tuple (chemin_md, chemin_json)
        """
        output_dir = output_dir or AUDITS_DIR
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"audit_report_{date_str}"

        # Markdown
        md_path = output_dir / f"{base_name}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(self.format_report_markdown(report))
        print(f"💾 Rapport Markdown : {md_path}")

        # JSON
        json_path = output_dir / f"{base_name}.json"
        report_dict = {
            "audit_date": report.audit_date,
            "organization": report.organization,
            "scope": report.scope,
            "total_measures": report.total_measures,
            "applicable_measures": report.applicable_measures,
            "validated": report.validated,
            "in_progress": report.in_progress,
            "to_create": report.to_create,
            "overall_compliance": report.overall_compliance,
            "overall_maturity": report.overall_maturity,
            "risk_level": report.risk_level,
            "domain_stats": [
                {
                    "domain": d.domain,
                    "domain_name": d.domain_name,
                    "total": d.total,
                    "validated": d.validated,
                    "compliance_rate": d.compliance_rate
                }
                for d in report.domain_stats
            ],
            "executive_summary": report.executive_summary,
            "recommendations": report.recommendations,
            "roadmap": report.roadmap
        }
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        print(f"💾 Rapport JSON : {json_path}")

        return md_path, json_path


# Test
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Automatisation d'audit SMSI")
    parser.add_argument("matrix", nargs="?", help="Chemin vers la matrice CSV")
    parser.add_argument("--no-ai", action="store_true", help="Désactiver l'analyse IA")

    args = parser.parse_args()

    audit = AuditAutomation()

    if args.matrix:
        report = audit.analyze_matrix(args.matrix, generate_ai=not args.no_ai)
        audit.save_report(report)
    else:
        # Utiliser la matrice par défaut si elle existe
        default_matrix = Path(__file__).parent.parent.parent / "Matrice_MultiNormes_SMSI.csv"
        if default_matrix.exists():
            print(f"Utilisation de la matrice par défaut : {default_matrix}")
            report = audit.analyze_matrix(str(default_matrix))
            audit.save_report(report)
        else:
            print("Usage : python audit_automation.py <chemin_vers_matrice.csv>")
            print("Ou placez une matrice 'Matrice_MultiNormes_SMSI.csv' dans le dossier parent")
