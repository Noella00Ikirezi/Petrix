"""Audit management view."""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from typing import TYPE_CHECKING, List

from .base_view import BaseView
from secop.infrastructure.database.connection import get_db
from secop.infrastructure.database.repositories.audit_repository import AuditRepository
from secop.infrastructure.database.models import Audit, AuditType, AuditStatus

if TYPE_CHECKING:
    from ..app import SecOpApplication


class AuditView(BaseView):
    """Audit management view for AD and Google Workspace."""

    def __init__(self, parent: ttk.Frame, app: "SecOpApplication"):
        self._audits: List[Audit] = []
        super().__init__(parent, app)

    def _build_ui(self) -> None:
        """Build audit view UI."""
        # Toolbar
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill=X, pady=(0, 15))

        ttk.Button(
            toolbar,
            text="+ Audit Active Directory",
            bootstyle="success",
            command=self._new_ad_audit,
        ).pack(side=LEFT, padx=(0, 10))

        ttk.Button(
            toolbar,
            text="+ Audit Google Workspace",
            bootstyle="info",
            command=self._new_gws_audit,
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
            values=["Tous"] + [t.value for t in AuditType],
            state="readonly",
            width=15,
        )
        self._type_filter.set("Tous")
        self._type_filter.pack(side=LEFT)
        self._type_filter.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        # Main content
        content = ttk.Frame(self.frame)
        content.pack(fill=BOTH, expand=True)

        # Audit list
        self._build_audit_list(content)

        # Configuration panel
        self._build_config_panel(content)

    def _build_audit_list(self, parent: ttk.Frame) -> None:
        """Build audit list."""
        list_frame = ttk.Frame(parent)
        list_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))

        columns = [
            ("name", "Nom", 200),
            ("type", "Type", 150),
            ("status", "Statut", 100),
            ("findings", "Anomalies", 80),
            ("date", "Date", 130),
        ]

        scroll_frame = ttk.Frame(list_frame)
        scroll_frame.pack(fill=BOTH, expand=True)

        scrollbar = ttk.Scrollbar(scroll_frame, orient=VERTICAL)
        scrollbar.pack(side=RIGHT, fill=Y)

        self._audit_tree = ttk.Treeview(
            scroll_frame,
            columns=[c[0] for c in columns],
            show="headings",
            yscrollcommand=scrollbar.set,
            bootstyle="success",
        )

        for col_id, heading, width in columns:
            self._audit_tree.heading(col_id, text=heading, anchor=W)
            self._audit_tree.column(col_id, width=width, anchor=W)

        self._audit_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=self._audit_tree.yview)

        self._audit_tree.bind("<<TreeviewSelect>>", self._on_audit_select)

    def _build_config_panel(self, parent: ttk.Frame) -> None:
        """Build configuration panel."""
        config_frame = ttk.Frame(parent, width=350)
        config_frame.pack(side=RIGHT, fill=Y)
        config_frame.pack_propagate(False)

        # AD Configuration
        ad_frame = ttk.LabelFrame(config_frame, text="Active Directory")
        ad_frame.pack(fill=X, pady=(0, 15))

        ttk.Label(ad_frame, text="Serveur LDAP:", font=("Segoe UI", 9)).pack(anchor=W)
        self._ad_server = ttk.Entry(ad_frame)
        self._ad_server.pack(fill=X, pady=(0, 10))

        ttk.Label(ad_frame, text="Base DN:", font=("Segoe UI", 9)).pack(anchor=W)
        self._ad_base_dn = ttk.Entry(ad_frame)
        self._ad_base_dn.pack(fill=X, pady=(0, 10))

        self._ad_ssl = ttk.Checkbutton(
            ad_frame,
            text="Utiliser SSL (LDAPS)",
            bootstyle="round-toggle",
        )
        self._ad_ssl.pack(anchor=W, pady=(0, 10))

        ttk.Button(
            ad_frame,
            text="Tester la connexion",
            bootstyle="info-outline",
            command=self._test_ad_connection,
        ).pack(fill=X)

        # Google Workspace Configuration
        gws_frame = ttk.LabelFrame(config_frame, text="Google Workspace")
        gws_frame.pack(fill=X)

        ttk.Label(gws_frame, text="Email Admin:", font=("Segoe UI", 9)).pack(anchor=W)
        self._gws_admin = ttk.Entry(gws_frame)
        self._gws_admin.pack(fill=X, pady=(0, 10))

        ttk.Label(gws_frame, text="Fichier credentials:", font=("Segoe UI", 9)).pack(anchor=W)

        cred_frame = ttk.Frame(gws_frame)
        cred_frame.pack(fill=X, pady=(0, 10))

        self._gws_creds = ttk.Entry(cred_frame)
        self._gws_creds.pack(side=LEFT, fill=X, expand=True)

        ttk.Button(
            cred_frame,
            text="...",
            bootstyle="secondary",
            width=3,
            command=self._browse_credentials,
        ).pack(side=LEFT, padx=(5, 0))

        ttk.Button(
            gws_frame,
            text="Tester la connexion",
            bootstyle="info-outline",
            command=self._test_gws_connection,
        ).pack(fill=X)

    def on_show(self) -> None:
        """Load audits."""
        self.refresh()

    def refresh(self) -> None:
        """Refresh audit list."""
        self.set_status("Chargement des audits...")
        self.run_async(self._load_audits, self._update_audit_list)

    def _load_audits(self) -> List[Audit]:
        """Load audits from database."""
        db = get_db()

        with db.get_session() as session:
            repo = AuditRepository(session)

            audit_type = None
            type_val = self._type_filter.get()
            if type_val != "Tous":
                audit_type = AuditType(type_val)

            audits = repo.find_by_criteria(
                audit_type=audit_type,
                limit=100,
            )

            session.expunge_all()
            return audits

    def _update_audit_list(self, audits) -> None:
        """Update audit list."""
        if isinstance(audits, Exception):
            self.set_status(f"Erreur: {audits}")
            return

        self._audits = audits

        self._audit_tree.delete(*self._audit_tree.get_children())

        for audit in audits:
            date_str = audit.created_at.strftime("%d/%m/%Y %H:%M") if audit.created_at else "-"
            self._audit_tree.insert("", END, iid=str(audit.id), values=(
                audit.name,
                audit.audit_type.value if audit.audit_type else "-",
                audit.status.value if audit.status else "-",
                audit.findings_count,
                date_str,
            ))

        self.set_status(f"{len(audits)} audits chargés")

    def _on_audit_select(self, event) -> None:
        """Handle audit selection."""
        pass

    def _new_ad_audit(self) -> None:
        """Create new AD audit."""
        Messagebox.show_info(
            "L'audit Active Directory sera disponible dans une prochaine version.\n\n"
            "Fonctionnalités prévues:\n"
            "- Liste des utilisateurs et groupes\n"
            "- Comptes privilégiés (Domain Admins)\n"
            "- Comptes inactifs\n"
            "- Politique de mots de passe\n"
            "- Trusts inter-domaines",
            "Audit Active Directory",
            parent=self.app.root
        )

    def _new_gws_audit(self) -> None:
        """Create new Google Workspace audit."""
        Messagebox.show_info(
            "L'audit Google Workspace sera disponible dans une prochaine version.\n\n"
            "Fonctionnalités prévues:\n"
            "- Liste des utilisateurs et admins\n"
            "- Apps OAuth tierces\n"
            "- Partages Drive externes\n"
            "- Règles de transfert email\n"
            "- Paramètres de sécurité",
            "Audit Google Workspace",
            parent=self.app.root
        )

    def _test_ad_connection(self) -> None:
        """Test AD connection."""
        server = self._ad_server.get()
        if not server:
            Messagebox.show_warning(
                "Veuillez entrer l'adresse du serveur LDAP.",
                "Configuration requise",
                parent=self.app.root
            )
            return

        Messagebox.show_info(
            "Le test de connexion AD sera disponible dans une prochaine version.",
            "Test de connexion",
            parent=self.app.root
        )

    def _test_gws_connection(self) -> None:
        """Test Google Workspace connection."""
        admin = self._gws_admin.get()
        creds = self._gws_creds.get()

        if not admin or not creds:
            Messagebox.show_warning(
                "Veuillez configurer l'email admin et le fichier credentials.",
                "Configuration requise",
                parent=self.app.root
            )
            return

        Messagebox.show_info(
            "Le test de connexion Google Workspace sera disponible dans une prochaine version.",
            "Test de connexion",
            parent=self.app.root
        )

    def _browse_credentials(self) -> None:
        """Browse for credentials file."""
        from tkinter import filedialog

        filepath = filedialog.askopenfilename(
            title="Sélectionner le fichier credentials",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            parent=self.app.root
        )

        if filepath:
            self._gws_creds.delete(0, END)
            self._gws_creds.insert(0, filepath)
