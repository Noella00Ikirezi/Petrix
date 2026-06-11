#!/usr/bin/env python3
"""
SMSI-Ollama : Suite d'outils IA pour la gestion SMSI
====================================================

Outils disponibles :
- Generateur de documentation (politiques, procedures, checklists)
- Analyseur de conformite
- Assistant SMSI interactif
- Automatisation d'audit

Usage :
    python main.py [commande] [options]

Exemples :
    python main.py assistant              # Lance l'assistant interactif
    python main.py generate --help        # Aide sur la generation
    python main.py audit matrix.csv       # Analyse une matrice
"""

import argparse
import sys
from pathlib import Path

# Ajouter le repertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import ORGANIZATION, OLLAMA_HOST, MODELS
from modules.ollama_client import OllamaClient
from modules.doc_generator import DocumentGenerator
from modules.compliance_analyzer import ComplianceAnalyzer
from modules.smsi_assistant import SMSIAssistant
from modules.audit_automation import AuditAutomation


def print_banner():
    """Affiche la banniere"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   ███████╗███╗   ███╗███████╗██╗      ██████╗ ██╗     ██╗     ║
    ║   ██╔════╝████╗ ████║██╔════╝██║     ██╔═══██╗██║     ██║     ║
    ║   ███████╗██╔████╔██║███████╗██║     ██║   ██║██║     ██║     ║
    ║   ╚════██║██║╚██╔╝██║╚════██║██║     ██║   ██║██║     ██║     ║
    ║   ███████║██║ ╚═╝ ██║███████║██║     ╚██████╔╝███████╗██║     ║
    ║   ╚══════╝╚═╝     ╚═╝╚══════╝╚═╝      ╚═════╝ ╚══════╝╚═╝     ║
    ║                                                               ║
    ║   Suite d'outils IA pour la gestion SMSI                      ║
    ║   Propulse par Ollama                                         ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_ollama():
    """Verifie la connexion Ollama"""
    try:
        client = OllamaClient()
        models = client.list_models()
        if models:
            print(f"[OK] Ollama connecte ({OLLAMA_HOST})")
            print(f"     Modeles disponibles : {', '.join(models[:5])}")
            return True
        else:
            print("[!] Ollama connecte mais aucun modele trouve")
            print("    Installez un modele : ollama pull mistral")
            return False
    except Exception as e:
        print(f"[X] Impossible de se connecter a Ollama : {e}")
        print("    Lancez Ollama : ollama serve")
        return False


def cmd_status(args):
    """Affiche le statut du systeme"""
    print_banner()
    print("\n[STATUS] Statut du systeme\n")

    print("[CONFIG] Configuration :")
    print(f"   Organisation : {ORGANIZATION.get('name', 'Non defini')}")
    print(f"   Secteur : {ORGANIZATION.get('sector', 'Non defini')}")
    print(f"   Referentiels : {', '.join(ORGANIZATION.get('frameworks', []))}")

    print("\n[OLLAMA] Connexion Ollama :")
    check_ollama()

    print("\n[MODELS] Modeles configures :")
    for task, model in MODELS.items():
        print(f"   {task}: {model}")


def cmd_assistant(args):
    """Lance l'assistant interactif"""
    if not check_ollama():
        return

    assistant = SMSIAssistant()

    if args.question:
        response = assistant.ask(args.question)
        print(response)
    else:
        assistant.start_chat()


def cmd_generate(args):
    """Genere un document"""
    if not check_ollama():
        return

    generator = DocumentGenerator()

    doc_type = args.type.upper()
    if doc_type not in ["POL", "PRO", "CHK"]:
        print(f"[X] Type de document invalide : {doc_type}")
        print("    Types valides : POL (Politique), PRO (Procedure), CHK (Checklist)")
        return

    print(f"\n[GEN] Generation d'un document {doc_type} pour {args.ref}")
    print(f"      Mesure : {args.measure}")

    content = generator.generate(
        ref_iso=args.ref,
        measure_name=args.measure,
        doc_type=doc_type,
        additional_context=args.context or ""
    )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\n[SAVE] Document sauvegarde : {output_path}")
    else:
        print("\n" + "=" * 60)
        print("DOCUMENT GENERE :")
        print("=" * 60)
        print(content)


def cmd_analyze(args):
    """Analyse un document"""
    if not check_ollama():
        return

    analyzer = ComplianceAnalyzer()

    filepath = Path(args.file)
    if not filepath.exists():
        print(f"[X] Fichier non trouve : {filepath}")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    requirements = [r.strip() for r in args.requirements.split(',')]

    print(f"\n[ANALYZE] Analyse de conformite : {filepath.name}")
    print(f"          Exigences : {', '.join(requirements)}")

    report = analyzer.analyze_document(
        document_content=content,
        requirements=requirements,
        document_name=filepath.name
    )

    if args.output:
        analyzer.save_report(report, Path(args.output).parent)
    else:
        print("\n" + analyzer.format_report_markdown(report))


def cmd_audit(args):
    """Effectue un audit de la matrice"""
    if not check_ollama():
        return

    audit = AuditAutomation()

    matrix_path = Path(args.matrix)
    if not matrix_path.exists():
        print(f"[X] Matrice non trouvee : {matrix_path}")
        return

    print(f"\n[AUDIT] Audit de la matrice : {matrix_path.name}")

    report = audit.analyze_matrix(
        str(matrix_path),
        generate_ai=not args.no_ai
    )

    if args.output:
        audit.save_report(report, Path(args.output))
    else:
        audit.save_report(report)


def cmd_batch(args):
    """Genere plusieurs documents en batch"""
    if not check_ollama():
        return

    generator = DocumentGenerator()

    priority_measures = [
        {"ref": "A.5.1", "name": "Politiques de securite de l'information"},
        {"ref": "A.5.2", "name": "Roles et responsabilites de securite"},
        {"ref": "A.9.1.1", "name": "Politique de controle d'acces"},
        {"ref": "A.9.2.1", "name": "Enregistrement et desinscription des utilisateurs"},
        {"ref": "A.9.2.3", "name": "Gestion des droits d'acces a privileges"},
        {"ref": "A.12.4.1", "name": "Journalisation des evenements"},
        {"ref": "A.16.1.1", "name": "Responsabilites et procedures de gestion des incidents"},
        {"ref": "A.18.1.1", "name": "Identification de la legislation applicable"},
    ]

    print(f"\n[BATCH] Generation batch de {len(priority_measures)} documents")
    print("        Type : Politique (POL)")

    files = generator.batch_generate(priority_measures, doc_type="POL")

    print(f"\n[OK] {len(files)} documents generes avec succes")
    for f in files:
        print(f"     - {f}")


def main():
    """Point d'entree principal"""
    parser = argparse.ArgumentParser(
        description="SMSI-Ollama : Suite d'outils IA pour la gestion SMSI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation :

  # Verifier le statut
  python main.py status

  # Lancer l'assistant interactif
  python main.py assistant

  # Poser une question unique
  python main.py assistant -q "Qu'est-ce que l'ISO 27001 ?"

  # Generer une politique
  python main.py generate -r A.9.1.1 -m "Politique de controle d'acces" -t POL

  # Analyser un document
  python main.py analyze document.md -e "A.9.1.1,A.9.2.1"

  # Auditer une matrice
  python main.py audit matrice.csv

  # Generation batch
  python main.py batch
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Commande a executer")

    # Status
    parser_status = subparsers.add_parser("status", help="Afficher le statut du systeme")
    parser_status.set_defaults(func=cmd_status)

    # Assistant
    parser_assistant = subparsers.add_parser("assistant", help="Lancer l'assistant SMSI")
    parser_assistant.add_argument("-q", "--question", help="Poser une question unique")
    parser_assistant.set_defaults(func=cmd_assistant)

    # Generate
    parser_generate = subparsers.add_parser("generate", help="Generer un document")
    parser_generate.add_argument("-r", "--ref", required=True, help="Reference ISO (ex: A.9.1.1)")
    parser_generate.add_argument("-m", "--measure", required=True, help="Nom de la mesure")
    parser_generate.add_argument("-t", "--type", default="POL", help="Type: POL, PRO, CHK")
    parser_generate.add_argument("-c", "--context", help="Contexte additionnel")
    parser_generate.add_argument("-o", "--output", help="Fichier de sortie")
    parser_generate.set_defaults(func=cmd_generate)

    # Analyze
    parser_analyze = subparsers.add_parser("analyze", help="Analyser un document")
    parser_analyze.add_argument("file", help="Fichier a analyser")
    parser_analyze.add_argument("-e", "--requirements", required=True,
                                help="Exigences a verifier (separees par des virgules)")
    parser_analyze.add_argument("-o", "--output", help="Repertoire de sortie")
    parser_analyze.set_defaults(func=cmd_analyze)

    # Audit
    parser_audit = subparsers.add_parser("audit", help="Auditer une matrice de conformite")
    parser_audit.add_argument("matrix", help="Fichier CSV de la matrice")
    parser_audit.add_argument("--no-ai", action="store_true", help="Desactiver l'analyse IA")
    parser_audit.add_argument("-o", "--output", help="Repertoire de sortie")
    parser_audit.set_defaults(func=cmd_audit)

    # Batch
    parser_batch = subparsers.add_parser("batch", help="Generer plusieurs documents")
    parser_batch.set_defaults(func=cmd_batch)

    args = parser.parse_args()

    if args.command is None:
        print_banner()
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
