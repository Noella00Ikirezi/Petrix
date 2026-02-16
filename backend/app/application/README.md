# Application — Services métier

Services de logique métier de la Petrix.

## Structure

```
application/
├── smsi/                    # Générateur de documentation SMSI
│   ├── __init__.py
│   ├── ai_service.py        # Service IA pour génération de contenu
│   ├── document_service.py  # CRUD documents SMSI
│   ├── document_generator.py # Génération automatique de documents
│   ├── fast_generator.py    # Génération rapide (templates pré-remplis)
│   ├── document_packs.py    # Packs de documents par framework
│   ├── export_service.py    # Export documents (PDF, DOCX)
│   ├── template_library.py  # Bibliothèque de templates
│   ├── templates_complete.py # Templates ISO 27001 complets
│   └── pssig_templates.py   # Templates PSSIG spécifiques
└── compliance/
    ├── __init__.py
    └── remediation_service.py # Service de remédiation conformité
```

## Module SMSI

Générateur automatique de documentation pour les Systèmes de Management de la Sécurité de l'Information (SMSI) conformes ISO 27001.

**Fonctionnalités** :
- Génération de politiques de sécurité, procédures, analyses de risques
- Templates complets ISO 27001 pré-remplis
- Packs de documents groupés par framework de conformité
- Export multi-format (HTML, PDF, DOCX)
- Assistance IA pour la rédaction via Ollama

## Module Compliance

Service de remédiation pour les exigences de conformité client. Génère des recommandations de mise en conformité.
