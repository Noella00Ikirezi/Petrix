"""Report generation view."""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from typing import TYPE_CHECKING

from .base_view import BaseView

if TYPE_CHECKING:
    from ..app import SecOpApplication


class ReportView(BaseView):
    """Report generation and export view."""

    def __init__(self, parent: ttk.Frame, app: "SecOpApplication"):
        super().__init__(parent, app)

    def _build_ui(self) -> None:
        """Build report view UI."""
        # Report types
        types_frame = ttk.LabelFrame(self.frame, text="Types de rapports")
        types_frame.pack(fill=X, pady=(0, 20))

        report_types = [
            ("inventory", "Inventaire des actifs", "Liste complète de tous les actifs avec détails", "info"),
            ("vulnerabilities", "Vulnérabilités", "Rapport des vulnérabilités ouvertes par sévérité", "danger"),
            ("scans", "Historique des scans", "Résumé des scans effectués et résultats", "success"),
            ("compliance", "Conformité", "État de conformité et recommandations", "warning"),
            ("executive", "Rapport exécutif", "Synthèse pour la direction", "primary"),
        ]

        for i, (key, title, desc, style) in enumerate(report_types):
            card = ttk.Frame(types_frame, bootstyle=style)
            card.grid(row=i // 3, column=i % 3, padx=10, pady=10, sticky="nsew")

            ttk.Label(
                card,
                text=title,
                font=("Segoe UI", 12, "bold"),
                bootstyle=f"{style}-inverse",
            ).pack(anchor=W)

            ttk.Label(
                card,
                text=desc,
                font=("Segoe UI", 9),
                bootstyle=f"{style}-inverse",
                wraplength=200,
            ).pack(anchor=W, pady=(5, 10))

            ttk.Button(
                card,
                text="Générer",
                bootstyle=f"{style}-outline",
                command=lambda k=key: self._generate_report(k),
            ).pack(anchor=W)

        types_frame.columnconfigure(0, weight=1)
        types_frame.columnconfigure(1, weight=1)
        types_frame.columnconfigure(2, weight=1)

        # Export options
        options_frame = ttk.LabelFrame(self.frame, text="Options d'export")
        options_frame.pack(fill=X, pady=(0, 20))

        # Format selection
        format_frame = ttk.Frame(options_frame)
        format_frame.pack(fill=X, pady=(0, 15))

        ttk.Label(format_frame, text="Format:", width=15).pack(side=LEFT)

        self._format_var = ttk.StringVar(value="pdf")

        formats = [("PDF", "pdf"), ("HTML", "html"), ("CSV", "csv")]
        for text, value in formats:
            ttk.Radiobutton(
                format_frame,
                text=text,
                variable=self._format_var,
                value=value,
                bootstyle="primary-toolbutton",
            ).pack(side=LEFT, padx=5)

        # Date range
        date_frame = ttk.Frame(options_frame)
        date_frame.pack(fill=X, pady=(0, 15))

        ttk.Label(date_frame, text="Période:", width=15).pack(side=LEFT)

        self._period_var = ttk.StringVar(value="month")

        periods = [
            ("Dernière semaine", "week"),
            ("Dernier mois", "month"),
            ("3 derniers mois", "quarter"),
            ("Année", "year"),
        ]
        for text, value in periods:
            ttk.Radiobutton(
                date_frame,
                text=text,
                variable=self._period_var,
                value=value,
                bootstyle="info-toolbutton",
            ).pack(side=LEFT, padx=5)

        # Include options
        include_frame = ttk.Frame(options_frame)
        include_frame.pack(fill=X)

        ttk.Label(include_frame, text="Inclure:", width=15).pack(side=LEFT)

        self._include_charts = ttk.BooleanVar(value=True)
        ttk.Checkbutton(
            include_frame,
            text="Graphiques",
            variable=self._include_charts,
            bootstyle="round-toggle",
        ).pack(side=LEFT, padx=10)

        self._include_details = ttk.BooleanVar(value=True)
        ttk.Checkbutton(
            include_frame,
            text="Détails techniques",
            variable=self._include_details,
            bootstyle="round-toggle",
        ).pack(side=LEFT, padx=10)

        self._include_recommendations = ttk.BooleanVar(value=True)
        ttk.Checkbutton(
            include_frame,
            text="Recommandations",
            variable=self._include_recommendations,
            bootstyle="round-toggle",
        ).pack(side=LEFT, padx=10)

        # Recent reports
        recent_frame = ttk.LabelFrame(self.frame, text="Rapports récents")
        recent_frame.pack(fill=BOTH, expand=True)

        columns = [
            ("name", "Rapport", 250),
            ("type", "Type", 150),
            ("format", "Format", 80),
            ("date", "Date", 150),
        ]

        self._report_tree = ttk.Treeview(
            recent_frame,
            columns=[c[0] for c in columns],
            show="headings",
            height=8,
        )

        for col_id, heading, width in columns:
            self._report_tree.heading(col_id, text=heading, anchor=W)
            self._report_tree.column(col_id, width=width, anchor=W)

        self._report_tree.pack(fill=BOTH, expand=True)

        # Add sample data
        self._report_tree.insert("", END, values=(
            "Rapport Vulnérabilités Q4 2025",
            "Vulnérabilités",
            "PDF",
            "15/12/2025 14:30",
        ))

    def _generate_report(self, report_type: str) -> None:
        """Generate a report."""
        format_val = self._format_var.get()
        period = self._period_var.get()

        report_names = {
            "inventory": "Inventaire des actifs",
            "vulnerabilities": "Vulnérabilités",
            "scans": "Historique des scans",
            "compliance": "Conformité",
            "executive": "Rapport exécutif",
        }

        Messagebox.show_info(
            f"La génération du rapport '{report_names.get(report_type, report_type)}' "
            f"en format {format_val.upper()} sera disponible dans une prochaine version.\n\n"
            f"Période sélectionnée: {period}\n"
            f"Graphiques: {'Oui' if self._include_charts.get() else 'Non'}\n"
            f"Détails: {'Oui' if self._include_details.get() else 'Non'}\n"
            f"Recommandations: {'Oui' if self._include_recommendations.get() else 'Non'}",
            "Génération de rapport",
            parent=self.app.root
        )
