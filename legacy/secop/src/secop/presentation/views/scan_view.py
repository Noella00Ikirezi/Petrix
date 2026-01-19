"""Vulnerability scan view."""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from typing import TYPE_CHECKING, Optional, List

from .base_view import BaseView
from secop.infrastructure.database.connection import get_db
from secop.infrastructure.database.repositories.scan_repository import ScanRepository
from secop.infrastructure.database.models import Scan, ScanStatus, ScannerType

if TYPE_CHECKING:
    from ..app import SecOpApplication


class ScanView(BaseView):
    """Vulnerability scan management view."""

    def __init__(self, parent: ttk.Frame, app: "SecOpApplication"):
        self._scans: List[Scan] = []
        super().__init__(parent, app)

    def _build_ui(self) -> None:
        """Build scan view UI."""
        # Toolbar
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill=X, pady=(0, 15))

        ttk.Button(
            toolbar,
            text="+ Nouveau Scan",
            bootstyle="success",
            command=self._new_scan,
        ).pack(side=LEFT, padx=(0, 10))

        ttk.Button(
            toolbar,
            text="Actualiser",
            bootstyle="secondary-outline",
            command=self.refresh,
        ).pack(side=LEFT)

        # Filters
        filter_frame = ttk.Frame(toolbar)
        filter_frame.pack(side=RIGHT)

        ttk.Label(filter_frame, text="Type:").pack(side=LEFT, padx=(0, 5))
        self._type_filter = ttk.Combobox(
            filter_frame,
            values=["Tous"] + [t.value for t in ScannerType],
            state="readonly",
            width=12,
        )
        self._type_filter.set("Tous")
        self._type_filter.pack(side=LEFT)
        self._type_filter.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        ttk.Label(filter_frame, text="Statut:").pack(side=LEFT, padx=(15, 5))
        self._status_filter = ttk.Combobox(
            filter_frame,
            values=["Tous"] + [s.value for s in ScanStatus],
            state="readonly",
            width=12,
        )
        self._status_filter.set("Tous")
        self._status_filter.pack(side=LEFT)
        self._status_filter.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        # Main content
        content = ttk.Frame(self.frame)
        content.pack(fill=BOTH, expand=True)

        # Scan list
        self._build_scan_list(content)

        # Detail panel
        self._build_detail_panel(content)

    def _build_scan_list(self, parent: ttk.Frame) -> None:
        """Build scan list."""
        list_frame = ttk.Frame(parent)
        list_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))

        columns = [
            ("name", "Nom", 180),
            ("type", "Scanner", 100),
            ("status", "Statut", 100),
            ("progress", "Progression", 80),
            ("findings", "Résultats", 80),
            ("date", "Date", 130),
        ]

        scroll_frame = ttk.Frame(list_frame)
        scroll_frame.pack(fill=BOTH, expand=True)

        scrollbar = ttk.Scrollbar(scroll_frame, orient=VERTICAL)
        scrollbar.pack(side=RIGHT, fill=Y)

        self._scan_tree = ttk.Treeview(
            scroll_frame,
            columns=[c[0] for c in columns],
            show="headings",
            yscrollcommand=scrollbar.set,
            bootstyle="info",
        )

        for col_id, heading, width in columns:
            self._scan_tree.heading(col_id, text=heading, anchor=W)
            self._scan_tree.column(col_id, width=width, anchor=W)

        self._scan_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=self._scan_tree.yview)

        self._scan_tree.bind("<<TreeviewSelect>>", self._on_scan_select)

    def _build_detail_panel(self, parent: ttk.Frame) -> None:
        """Build scan detail panel."""
        detail_frame = ttk.LabelFrame(parent, text="Détails du scan", width=350)
        detail_frame.pack(side=RIGHT, fill=Y)
        detail_frame.pack_propagate(False)

        inner = ttk.Frame(detail_frame)
        inner.pack(fill=BOTH, expand=True, padx=15, pady=15)

        # Info fields
        self._detail_fields = {}
        fields = [
            ("name", "Nom"),
            ("scanner_type", "Type"),
            ("targets", "Cibles"),
            ("status", "Statut"),
            ("progress", "Progression"),
            ("findings", "Résultats"),
            ("started", "Démarré"),
            ("completed", "Terminé"),
        ]

        for field_id, label in fields:
            frame = ttk.Frame(inner)
            frame.pack(fill=X, pady=3)

            ttk.Label(frame, text=f"{label}:", width=12, anchor=W).pack(side=LEFT)
            value_label = ttk.Label(frame, text="-", anchor=W)
            value_label.pack(side=LEFT, fill=X, expand=True)
            self._detail_fields[field_id] = value_label

        # Progress bar
        ttk.Label(inner, text="Progression:").pack(anchor=W, pady=(15, 5))
        self._progress_bar = ttk.Progressbar(
            inner,
            value=0,
            bootstyle="success-striped",
        )
        self._progress_bar.pack(fill=X)

        # Action buttons
        btn_frame = ttk.Frame(inner)
        btn_frame.pack(fill=X, pady=(20, 0))

        self._start_btn = ttk.Button(
            btn_frame,
            text="Démarrer",
            bootstyle="success",
            command=self._start_scan,
            state=DISABLED,
        )
        self._start_btn.pack(side=LEFT, padx=(0, 5))

        self._stop_btn = ttk.Button(
            btn_frame,
            text="Arrêter",
            bootstyle="danger-outline",
            command=self._stop_scan,
            state=DISABLED,
        )
        self._stop_btn.pack(side=LEFT, padx=5)

        self._view_results_btn = ttk.Button(
            btn_frame,
            text="Voir résultats",
            bootstyle="info",
            command=self._view_results,
            state=DISABLED,
        )
        self._view_results_btn.pack(side=LEFT, padx=5)

    def on_show(self) -> None:
        """Load scans when view is shown."""
        self.refresh()

    def refresh(self) -> None:
        """Refresh scan list."""
        self.set_status("Chargement des scans...")
        self.run_async(self._load_scans, self._update_scan_list)

    def _load_scans(self) -> List[Scan]:
        """Load scans from database."""
        db = get_db()

        with db.get_session() as session:
            repo = ScanRepository(session)

            scanner_type = None
            status = None

            type_val = self._type_filter.get()
            if type_val != "Tous":
                scanner_type = ScannerType(type_val)

            status_val = self._status_filter.get()
            if status_val != "Tous":
                status = ScanStatus(status_val)

            scans = repo.find_by_criteria(
                scanner_type=scanner_type,
                status=status,
                limit=100,
            )

            session.expunge_all()
            return scans

    def _update_scan_list(self, scans) -> None:
        """Update scan list."""
        if isinstance(scans, Exception):
            self.set_status(f"Erreur: {scans}")
            return

        self._scans = scans

        self._scan_tree.delete(*self._scan_tree.get_children())

        for scan in scans:
            date_str = scan.created_at.strftime("%d/%m/%Y %H:%M") if scan.created_at else "-"
            self._scan_tree.insert("", END, iid=str(scan.id), values=(
                scan.name,
                scan.scanner_type.value if scan.scanner_type else "-",
                scan.status.value if scan.status else "-",
                f"{scan.progress}%",
                scan.findings_count,
                date_str,
            ))

        self.set_status(f"{len(scans)} scans chargés")

    def _on_scan_select(self, event) -> None:
        """Handle scan selection."""
        selection = self._scan_tree.selection()
        if not selection:
            return

        scan_id = int(selection[0])
        scan = next((s for s in self._scans if s.id == scan_id), None)

        if scan:
            self._show_scan_detail(scan)

    def _show_scan_detail(self, scan: Scan) -> None:
        """Display scan details."""
        self._detail_fields["name"].configure(text=scan.name or "-")
        self._detail_fields["scanner_type"].configure(
            text=scan.scanner_type.value if scan.scanner_type else "-"
        )
        self._detail_fields["targets"].configure(text=scan.targets[:50] if scan.targets else "-")
        self._detail_fields["status"].configure(
            text=scan.status.value if scan.status else "-"
        )
        self._detail_fields["progress"].configure(text=f"{scan.progress}%")
        self._detail_fields["findings"].configure(text=str(scan.findings_count))
        self._detail_fields["started"].configure(
            text=scan.started_at.strftime("%d/%m/%Y %H:%M") if scan.started_at else "-"
        )
        self._detail_fields["completed"].configure(
            text=scan.completed_at.strftime("%d/%m/%Y %H:%M") if scan.completed_at else "-"
        )

        self._progress_bar.configure(value=scan.progress)

        # Update button states
        if scan.status == ScanStatus.PENDING:
            self._start_btn.configure(state=NORMAL)
            self._stop_btn.configure(state=DISABLED)
        elif scan.status == ScanStatus.RUNNING:
            self._start_btn.configure(state=DISABLED)
            self._stop_btn.configure(state=NORMAL)
        else:
            self._start_btn.configure(state=DISABLED)
            self._stop_btn.configure(state=DISABLED)

        if scan.status == ScanStatus.COMPLETED and scan.findings_count > 0:
            self._view_results_btn.configure(state=NORMAL)
        else:
            self._view_results_btn.configure(state=DISABLED)

    def _new_scan(self) -> None:
        """Create new scan."""
        Messagebox.show_info(
            "La création de scan sera disponible dans une prochaine version.\n\n"
            "Fonctionnalités prévues:\n"
            "- Scan Nmap (ports, services, OS)\n"
            "- Scan OpenVAS (vulnérabilités)\n"
            "- Scan Nuclei (templates)",
            "Nouveau Scan",
            parent=self.app.root
        )

    def _start_scan(self) -> None:
        """Start selected scan."""
        Messagebox.show_info(
            "Le démarrage de scan sera disponible dans une prochaine version.",
            "Démarrer le scan",
            parent=self.app.root
        )

    def _stop_scan(self) -> None:
        """Stop selected scan."""
        Messagebox.show_info(
            "L'arrêt de scan sera disponible dans une prochaine version.",
            "Arrêter le scan",
            parent=self.app.root
        )

    def _view_results(self) -> None:
        """View scan results."""
        Messagebox.show_info(
            "La visualisation des résultats sera disponible dans une prochaine version.",
            "Résultats du scan",
            parent=self.app.root
        )
