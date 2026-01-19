"""Dashboard view with KPIs and overview."""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from typing import TYPE_CHECKING
from datetime import datetime

from .base_view import BaseView
from secop.infrastructure.database.connection import get_db
from secop.infrastructure.database.repositories.asset_repository import AssetRepository
from secop.infrastructure.database.repositories.vulnerability_repository import VulnerabilityRepository
from secop.infrastructure.database.repositories.scan_repository import ScanRepository
from secop.infrastructure.database.repositories.audit_repository import AuditRepository
from secop.infrastructure.database.models import Criticality, VulnerabilityStatus, ScanStatus

if TYPE_CHECKING:
    from ..app import SecOpApplication


class DashboardView(BaseView):
    """Dashboard view with key metrics and recent activity."""

    def __init__(self, parent: ttk.Frame, app: "SecOpApplication"):
        super().__init__(parent, app)

    def _build_ui(self) -> None:
        """Build dashboard UI."""
        # Scrollable container
        canvas = ttk.Canvas(self.frame)
        scrollbar = ttk.Scrollbar(self.frame, orient=VERTICAL, command=canvas.yview)
        self._scrollable_frame = ttk.Frame(canvas)

        self._scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self._scrollable_frame, anchor=NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # KPI Cards Row
        self._build_kpi_section()

        # Charts Row
        self._build_charts_section()

        # Recent Activity
        self._build_activity_section()

    def _build_kpi_section(self) -> None:
        """Build KPI cards section."""
        kpi_frame = ttk.Frame(self._scrollable_frame)
        kpi_frame.pack(fill=X, pady=(0, 20))

        # KPI Cards container
        cards_frame = ttk.Frame(kpi_frame)
        cards_frame.pack(fill=X)

        # Create card frames for grid
        self._kpi_cards = {}

        cards_data = [
            ("assets", "Actifs", "0", "Total inventorié", "info"),
            ("vulns", "Vulnérabilités", "0", "Ouvertes", "danger"),
            ("critical", "Critiques", "0", "À traiter en priorité", "warning"),
            ("scans", "Scans", "0", "Derniers 7 jours", "success"),
        ]

        for i, (key, title, value, subtitle, style) in enumerate(cards_data):
            card = self._create_kpi_card(cards_frame, title, value, subtitle, style)
            card.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")
            self._kpi_cards[key] = card
            cards_frame.columnconfigure(i, weight=1)

    def _create_kpi_card(
        self,
        parent: ttk.Frame,
        title: str,
        value: str,
        subtitle: str,
        style: str
    ) -> ttk.Frame:
        """Create a KPI card widget."""
        card = ttk.Frame(parent, bootstyle=style)
        inner = ttk.Frame(card)
        inner.pack(padx=20, pady=20)

        ttk.Label(
            inner,
            text=title,
            font=("Segoe UI", 11),
            bootstyle=f"{style}-inverse",
        ).pack(anchor=W)

        self._value_label = ttk.Label(
            inner,
            text=value,
            font=("Segoe UI", 32, "bold"),
            bootstyle=f"{style}-inverse",
        )
        self._value_label.pack(anchor=W, pady=(5, 0))

        ttk.Label(
            inner,
            text=subtitle,
            font=("Segoe UI", 9),
            bootstyle=f"{style}-inverse",
        ).pack(anchor=W)

        # Store value label reference
        card._value_label = self._value_label

        return card

    def _build_charts_section(self) -> None:
        """Build charts section."""
        charts_frame = ttk.Frame(self._scrollable_frame)
        charts_frame.pack(fill=X, pady=20)

        # Left chart - Vulnerabilities by severity
        left_frame = ttk.LabelFrame(charts_frame, text="Vulnérabilités par sévérité")
        left_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))

        self._vuln_chart_frame = ttk.Frame(left_frame)
        self._vuln_chart_frame.pack(fill=BOTH, expand=True, padx=15, pady=15)

        # Right chart - Assets by type
        right_frame = ttk.LabelFrame(charts_frame, text="Actifs par type")
        right_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(10, 0))

        self._asset_chart_frame = ttk.Frame(right_frame)
        self._asset_chart_frame.pack(fill=BOTH, expand=True, padx=15, pady=15)

    def _build_activity_section(self) -> None:
        """Build recent activity section."""
        activity_frame = ttk.LabelFrame(
            self._scrollable_frame,
            text="Activité récente",
        )
        activity_frame.pack(fill=BOTH, expand=True, pady=20)

        inner_activity = ttk.Frame(activity_frame)
        inner_activity.pack(fill=BOTH, expand=True, padx=15, pady=15)

        # Recent scans
        scans_frame = ttk.Frame(inner_activity)
        scans_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))

        ttk.Label(
            scans_frame,
            text="Derniers Scans",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor=W, pady=(0, 10))

        self._scans_tree = ttk.Treeview(
            scans_frame,
            columns=("name", "status", "date"),
            show="headings",
            height=5,
            bootstyle="info",
        )
        self._scans_tree.heading("name", text="Nom", anchor=W)
        self._scans_tree.heading("status", text="Statut", anchor=W)
        self._scans_tree.heading("date", text="Date", anchor=W)
        self._scans_tree.column("name", width=150)
        self._scans_tree.column("status", width=100)
        self._scans_tree.column("date", width=120)
        self._scans_tree.pack(fill=BOTH, expand=True)

        # Recent vulnerabilities
        vulns_frame = ttk.Frame(inner_activity)
        vulns_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(10, 0))

        ttk.Label(
            vulns_frame,
            text="Dernières Vulnérabilités",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor=W, pady=(0, 10))

        self._vulns_tree = ttk.Treeview(
            vulns_frame,
            columns=("name", "severity", "asset"),
            show="headings",
            height=5,
            bootstyle="danger",
        )
        self._vulns_tree.heading("name", text="Nom", anchor=W)
        self._vulns_tree.heading("severity", text="Sévérité", anchor=W)
        self._vulns_tree.heading("asset", text="Actif", anchor=W)
        self._vulns_tree.column("name", width=150)
        self._vulns_tree.column("severity", width=80)
        self._vulns_tree.column("asset", width=120)
        self._vulns_tree.pack(fill=BOTH, expand=True)

    def on_show(self) -> None:
        """Load dashboard data when view is shown."""
        self.refresh()

    def refresh(self) -> None:
        """Refresh dashboard data."""
        self.set_status("Chargement du tableau de bord...")
        self.run_async(self._load_data, self._update_ui)

    def _load_data(self) -> dict:
        """Load all dashboard data."""
        db = get_db()
        data = {}

        with db.get_session() as session:
            asset_repo = AssetRepository(session)
            vuln_repo = VulnerabilityRepository(session)
            scan_repo = ScanRepository(session)

            # KPI data
            data["asset_count"] = asset_repo.count()
            data["vuln_open_count"] = len(vuln_repo.find_open())
            data["vuln_critical_count"] = len(vuln_repo.find_critical_open())
            data["scan_recent_count"] = len(scan_repo.find_recent(days=7))

            # Chart data
            data["vuln_by_severity"] = vuln_repo.count_open_by_severity()
            data["asset_by_type"] = asset_repo.count_by_type()

            # Recent activity
            data["recent_scans"] = scan_repo.find_recent(days=7)[:5]
            data["recent_vulns"] = vuln_repo.find_recent(days=7)[:5]

        return data

    def _update_ui(self, data: dict) -> None:
        """Update UI with loaded data."""
        if isinstance(data, Exception):
            self.set_status(f"Erreur: {data}")
            return

        # Update KPIs
        kpi_values = [
            ("assets", str(data.get("asset_count", 0))),
            ("vulns", str(data.get("vuln_open_count", 0))),
            ("critical", str(data.get("vuln_critical_count", 0))),
            ("scans", str(data.get("scan_recent_count", 0))),
        ]

        for key, value in kpi_values:
            if key in self._kpi_cards:
                card = self._kpi_cards[key]
                if hasattr(card, "_value_label"):
                    card._value_label.configure(text=value)

        # Update vulnerability chart (simple bar representation)
        self._update_vuln_chart(data.get("vuln_by_severity", {}))

        # Update asset chart
        self._update_asset_chart(data.get("asset_by_type", {}))

        # Update recent scans
        self._scans_tree.delete(*self._scans_tree.get_children())
        for scan in data.get("recent_scans", []):
            date_str = scan.created_at.strftime("%d/%m/%Y %H:%M") if scan.created_at else "-"
            self._scans_tree.insert("", END, values=(
                scan.name[:30],
                scan.status.value,
                date_str,
            ))

        # Update recent vulns
        self._vulns_tree.delete(*self._vulns_tree.get_children())
        for vuln in data.get("recent_vulns", []):
            asset_name = vuln.asset.name[:20] if vuln.asset else "-"
            self._vulns_tree.insert("", END, values=(
                vuln.name[:30],
                vuln.severity.value,
                asset_name,
            ))

        self.set_status("Tableau de bord mis à jour")

    def _update_vuln_chart(self, vuln_data: dict) -> None:
        """Update vulnerability severity chart."""
        # Clear existing
        for widget in self._vuln_chart_frame.winfo_children():
            widget.destroy()

        severity_colors = {
            Criticality.CRITICAL: "danger",
            Criticality.HIGH: "warning",
            Criticality.MEDIUM: "info",
            Criticality.LOW: "success",
            Criticality.INFO: "secondary",
        }

        severity_labels = {
            Criticality.CRITICAL: "Critique",
            Criticality.HIGH: "Haute",
            Criticality.MEDIUM: "Moyenne",
            Criticality.LOW: "Basse",
            Criticality.INFO: "Info",
        }

        total = sum(vuln_data.values()) or 1

        for severity in [Criticality.CRITICAL, Criticality.HIGH, Criticality.MEDIUM, Criticality.LOW]:
            count = vuln_data.get(severity, 0)
            pct = int((count / total) * 100) if total > 0 else 0

            row = ttk.Frame(self._vuln_chart_frame)
            row.pack(fill=X, pady=3)

            ttk.Label(
                row,
                text=severity_labels.get(severity, severity.value),
                width=10,
            ).pack(side=LEFT)

            bar = ttk.Progressbar(
                row,
                value=pct,
                bootstyle=severity_colors.get(severity, "primary"),
                length=150,
            )
            bar.pack(side=LEFT, padx=10)

            ttk.Label(
                row,
                text=str(count),
                width=5,
            ).pack(side=LEFT)

    def _update_asset_chart(self, asset_data: dict) -> None:
        """Update asset type chart."""
        # Clear existing
        for widget in self._asset_chart_frame.winfo_children():
            widget.destroy()

        total = sum(asset_data.values()) or 1

        for asset_type, count in sorted(asset_data.items(), key=lambda x: x[1], reverse=True)[:6]:
            pct = int((count / total) * 100) if total > 0 else 0

            row = ttk.Frame(self._asset_chart_frame)
            row.pack(fill=X, pady=3)

            ttk.Label(
                row,
                text=asset_type.value[:12],
                width=12,
            ).pack(side=LEFT)

            bar = ttk.Progressbar(
                row,
                value=pct,
                bootstyle="info",
                length=150,
            )
            bar.pack(side=LEFT, padx=10)

            ttk.Label(
                row,
                text=str(count),
                width=5,
            ).pack(side=LEFT)
