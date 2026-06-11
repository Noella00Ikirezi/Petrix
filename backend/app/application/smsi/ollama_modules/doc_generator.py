"""
Générateur de Documentation SMSI
Génère automatiquement des politiques, procédures et autres documents de conformité
"""
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass

sys.path.append(str(Path(__file__).parent.parent))
from config.settings import (
    ORGANIZATION, DOCUMENTS_DIR, DOC_CLASSIFICATION,
    MODELS
)
from modules.ollama_client import OllamaClient


@dataclass
class DocumentRequest:
    """Requête de génération de document"""
    ref_iso: str                    # Ex: A.9.1.1
    measure_name: str               # Ex: Politique de contrôle d'accès
    doc_type: str                   # POL, PRO, GUI, etc.
    classification: str = "internal"
    additional_context: str = ""
    frameworks: List[str] = None


class DocumentGenerator:
    """
    Générateur de documents SMSI

    Usage:
        generator = DocumentGenerator()
        doc = generator.generate_policy("A.9.1.1", "Politique de contrôle d'accès")
        generator.save_document(doc, "POL-SEC-001")
    """

    SYSTEM_PROMPT = """# RÔLE ET IDENTITÉ
Tu es un consultant senior en sécurité de l'information avec 15 ans d'expérience, certifié :
- ISO 27001 Lead Implementer & Lead Auditor
- ISO 22301 Lead Implementer
- CISSP, CISM, DPO certifié

# CONTEXTE ORGANISATIONNEL
Organisation : {org_name}
Secteur : {org_sector}
Taille : {org_size}
Périmètre SMSI : {org_scope}
Référentiels applicables : {frameworks}

# RÈGLES DE RÉDACTION OBLIGATOIRES

1. **Structure documentaire stricte** avec sections numérotées
2. **Langue** : Français professionnel, vouvoiement
3. **Verbes modaux normalisés** :
   - "DOIT" = obligation absolue
   - "DEVRAIT" = recommandation forte
   - "PEUT" = option autorisée
   - "NE DOIT PAS" = interdiction absolue

4. **Traçabilité** : Chaque exigence majeure doit référencer [ISO 27001:2022 A.X.X] [RGPD Art. XX] etc.

5. **Format** : Markdown structuré avec numérotation hiérarchique

6. **Qualité des règles** :
   ❌ MAUVAIS : "Les accès doivent être sécurisés"
   ✅ BON : "[R-ACC-001] Tout accès au SI DOIT être authentifié par un mécanisme à deux facteurs minimum pour les ressources classifiées Confidentiel ou supérieur. [ISO 27001:2022 A.5.17] [RGPD Art. 32]"
"""

    POLICY_TEMPLATE = """# TÂCHE
Rédige une POLITIQUE complète pour la mesure {ref_iso} - {measure_name}

# STRUCTURE OBLIGATOIRE DU DOCUMENT

## EN-TÊTE
- Titre : Politique de [sujet]
- Référence : POL-SEC-XXX
- Version : 1.0
- Date : {date}
- Classification : {classification}
- Propriétaire : [À définir]
- Approbateur : Direction Générale

## 1. OBJET ET DOMAINE D'APPLICATION
- Objectif de la politique (2-3 paragraphes)
- Périmètre (entités, systèmes, personnes concernées)
- Exclusions éventuelles

## 2. DOCUMENTS DE RÉFÉRENCE
- ISO 27001:2022 et mesures Annexe A concernées
- Réglementations (RGPD, NIS2, etc.)
- Documents internes liés

## 3. DÉFINITIONS ET ACRONYMES
Table des termes techniques utilisés

## 4. RÔLES ET RESPONSABILITÉS
Matrice RACI : Qui est Responsable, Accountable, Consulté, Informé

## 5. PRINCIPES DIRECTEURS
5-10 principes numérotés avec justification

## 6. RÈGLES ET EXIGENCES
Règles numérotées [R-XXX-001] avec :
- L'exigence précise
- Les conditions d'application
- Les références normatives [ISO...] [RGPD...]

## 7. EXCEPTIONS ET DÉROGATIONS
Processus pour demander une exception

## 8. INDICATEURS DE SUIVI
3-5 KPIs avec formule de calcul et seuils

## 9. CONTRÔLE ET AUDIT
Fréquence et méthodes de contrôle

## 10. SANCTIONS
Référence au règlement intérieur

## 11. RÉVISION
Fréquence de révision et déclencheurs

---
{additional_context}

Génère maintenant le document complet en Markdown :"""

    PROCEDURE_TEMPLATE = """# TÂCHE
Rédige une PROCÉDURE opérationnelle détaillée pour la mesure {ref_iso} - {measure_name}

# STRUCTURE OBLIGATOIRE

## EN-TÊTE
- Titre : Procédure de [action]
- Référence : PRO-SEC-XXX
- Version : 1.0
- Date : {date}
- Classification : {classification}

## 1. OBJET
But de la procédure

## 2. DOMAINE D'APPLICATION
Quand et par qui cette procédure s'applique

## 3. DOCUMENTS DE RÉFÉRENCE
- Politique parente
- Normes applicables

## 4. DÉFINITIONS

## 5. RÔLES ET RESPONSABILITÉS
Qui fait quoi dans cette procédure

## 6. LOGIGRAMME
Description textuelle du flux :
```
[Déclencheur] → [Étape 1] → [Décision ?]
                              ↓ Oui      ↓ Non
                          [Étape 2]   [Étape 3]
                              ↓
                          [Fin]
```

## 7. DESCRIPTION DÉTAILLÉE DES ÉTAPES

### Étape 1 : [Titre]
| Élément | Description |
|---------|-------------|
| **Déclencheur** | Ce qui initie cette étape |
| **Responsable** | Rôle qui exécute |
| **Action** | Description détaillée de l'action |
| **Entrées** | Documents/informations nécessaires |
| **Sorties** | Résultats/livrables produits |
| **Délai** | Temps maximum pour réaliser |
| **Outil** | Application/système utilisé |
| **Point de contrôle** | Vérification à effectuer |

[Répéter pour chaque étape]

## 8. ENREGISTREMENTS
Documents à conserver et durée de rétention

## 9. ANNEXES
- Formulaires
- Checklists
- Modèles

---
{additional_context}

Génère maintenant la procédure complète en Markdown :"""

    CHECKLIST_TEMPLATE = """# TÂCHE
Crée une CHECKLIST opérationnelle pour la mesure {ref_iso} - {measure_name}

# FORMAT ATTENDU

## Checklist : [Titre]
**Référence** : CHK-SEC-XXX
**Version** : 1.0
**Date** : {date}

### Informations de contrôle
| Champ | Valeur |
|-------|--------|
| Date du contrôle | ___/___/______ |
| Contrôleur | ________________ |
| Périmètre contrôlé | ________________ |

### Points de contrôle

| # | Point de vérification | Conforme | Non-conforme | N/A | Observations |
|---|----------------------|:--------:|:------------:|:---:|--------------|
| 1 | [Point détaillé avec critère mesurable] | ☐ | ☐ | ☐ | |
| 2 | ... | ☐ | ☐ | ☐ | |

### Synthèse
- Points conformes : ___
- Points non-conformes : ___
- Points N/A : ___
- Taux de conformité : ___%

### Actions correctives identifiées
| # | Non-conformité | Action corrective | Responsable | Échéance |
|---|---------------|-------------------|-------------|----------|
| 1 | | | | |

### Signatures
| Rôle | Nom | Signature | Date |
|------|-----|-----------|------|
| Contrôleur | | | |
| Valideur | | | |

---
{additional_context}

Génère maintenant la checklist complète avec au moins 15-20 points de contrôle pertinents :"""

    def __init__(self, client: OllamaClient = None):
        self.client = client or OllamaClient()
        self.templates = {
            "POL": self.POLICY_TEMPLATE,
            "PRO": self.PROCEDURE_TEMPLATE,
            "CHK": self.CHECKLIST_TEMPLATE,
        }

    def _build_system_prompt(self, frameworks: List[str] = None) -> str:
        """Construit le system prompt avec le contexte organisationnel"""
        frameworks = frameworks or ORGANIZATION.get("frameworks", ["ISO 27001:2022"])
        return self.SYSTEM_PROMPT.format(
            org_name=ORGANIZATION.get("name", "Organisation"),
            org_sector=ORGANIZATION.get("sector", "Non défini"),
            org_size=ORGANIZATION.get("size", "Non défini"),
            org_scope=ORGANIZATION.get("scope", "SI principal"),
            frameworks=", ".join(frameworks)
        )

    def generate(
        self,
        ref_iso: str,
        measure_name: str,
        doc_type: str = "POL",
        classification: str = "internal",
        additional_context: str = "",
        frameworks: List[str] = None
    ) -> str:
        """
        Génère un document SMSI

        Args:
            ref_iso: Référence ISO (ex: A.9.1.1)
            measure_name: Nom de la mesure
            doc_type: Type de document (POL, PRO, CHK)
            classification: Niveau de classification
            additional_context: Contexte additionnel
            frameworks: Référentiels applicables

        Returns:
            Document généré en Markdown
        """
        template = self.templates.get(doc_type, self.POLICY_TEMPLATE)

        prompt = template.format(
            ref_iso=ref_iso,
            measure_name=measure_name,
            date=datetime.now().strftime("%d/%m/%Y"),
            classification=DOC_CLASSIFICATION.get(classification, "Interne"),
            additional_context=additional_context
        )

        system_prompt = self._build_system_prompt(frameworks)

        print(f"🔄 Génération du document {doc_type} pour {ref_iso}...")
        print(f"   Modèle utilisé : {MODELS.get('documentation', 'mistral')}")

        response = self.client.generate(
            prompt=prompt,
            system=system_prompt,
            task_type="documentation"
        )

        if response.success:
            print(f"✅ Document généré ({response.eval_count} tokens)")
            return response.content
        else:
            print(f"❌ Erreur : {response.error}")
            return f"# Erreur de génération\n\n{response.error}"

    def generate_policy(self, ref_iso: str, measure_name: str, **kwargs) -> str:
        """Raccourci pour générer une politique"""
        return self.generate(ref_iso, measure_name, doc_type="POL", **kwargs)

    def generate_procedure(self, ref_iso: str, measure_name: str, **kwargs) -> str:
        """Raccourci pour générer une procédure"""
        return self.generate(ref_iso, measure_name, doc_type="PRO", **kwargs)

    def generate_checklist(self, ref_iso: str, measure_name: str, **kwargs) -> str:
        """Raccourci pour générer une checklist"""
        return self.generate(ref_iso, measure_name, doc_type="CHK", **kwargs)

    def save_document(
        self,
        content: str,
        reference: str,
        output_dir: Path = None
    ) -> Path:
        """
        Sauvegarde un document généré

        Args:
            content: Contenu du document
            reference: Référence documentaire (ex: POL-SEC-001)
            output_dir: Répertoire de sortie

        Returns:
            Chemin du fichier créé
        """
        output_dir = output_dir or DOCUMENTS_DIR
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"{reference}_{date_str}.md"
        filepath = output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"💾 Document sauvegardé : {filepath}")
        return filepath

    def batch_generate(
        self,
        measures: List[Dict],
        doc_type: str = "POL"
    ) -> List[Path]:
        """
        Génère plusieurs documents en batch

        Args:
            measures: Liste de dict avec 'ref' et 'name'
            doc_type: Type de document

        Returns:
            Liste des chemins de fichiers créés
        """
        created_files = []
        total = len(measures)

        for i, measure in enumerate(measures, 1):
            print(f"\n[{i}/{total}] Traitement de {measure['ref']}...")

            content = self.generate(
                ref_iso=measure['ref'],
                measure_name=measure['name'],
                doc_type=doc_type
            )

            # Générer référence documentaire
            ref_num = str(i).zfill(3)
            doc_ref = f"{doc_type}-SEC-{ref_num}"

            filepath = self.save_document(content, doc_ref)
            created_files.append(filepath)

        print(f"\n✅ {len(created_files)} documents générés")
        return created_files


# Test
if __name__ == "__main__":
    generator = DocumentGenerator()

    # Test génération d'une politique
    print("=" * 60)
    print("TEST : Génération d'une politique de contrôle d'accès")
    print("=" * 60)

    policy = generator.generate_policy(
        ref_iso="A.9.1.1",
        measure_name="Politique de contrôle d'accès",
        additional_context="L'organisation utilise Active Directory et Azure AD."
    )

    print("\n" + "=" * 60)
    print("APERÇU DU DOCUMENT GÉNÉRÉ :")
    print("=" * 60)
    print(policy[:2000] + "\n..." if len(policy) > 2000 else policy)

    # Sauvegarder
    generator.save_document(policy, "POL-SEC-001")
