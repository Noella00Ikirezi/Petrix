"""Settings view."""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from typing import TYPE_CHECKING

from .base_view import BaseView
from secop.config.settings import get_settings
from secop.auth.authorization import get_auth_service, Permission
from secop.infrastructure.database.connection import get_db

if TYPE_CHECKING:
    from ..app import SecOpApplication


class SettingsView(BaseView):
    """Application settings view."""

    def __init__(self, parent: ttk.Frame, app: "SecOpApplication"):
        super().__init__(parent, app)

    def _build_ui(self) -> None:
        """Build settings view UI."""
        # Create notebook for tabbed interface
        notebook = ttk.Notebook(self.frame, bootstyle="primary")
        notebook.pack(fill=BOTH, expand=True)

        # General settings tab
        general_frame = ttk.Frame(notebook)
        general_inner = ttk.Frame(general_frame)
        general_inner.pack(fill=BOTH, expand=True, padx=20, pady=20)
        notebook.add(general_frame, text="Général")
        self._build_general_settings(general_inner)

        # Security settings tab
        security_frame = ttk.Frame(notebook)
        security_inner = ttk.Frame(security_frame)
        security_inner.pack(fill=BOTH, expand=True, padx=20, pady=20)
        notebook.add(security_frame, text="Sécurité")
        self._build_security_settings(security_inner)

        # Scanners settings tab
        scanners_frame = ttk.Frame(notebook)
        scanners_inner = ttk.Frame(scanners_frame)
        scanners_inner.pack(fill=BOTH, expand=True, padx=20, pady=20)
        notebook.add(scanners_frame, text="Scanners")
        self._build_scanner_settings(scanners_inner)

        # Users management tab (admin only)
        auth = get_auth_service()
        if auth.is_authenticated() and auth.get_context().has_permission(Permission.USER_VIEW):
            users_frame = ttk.Frame(notebook)
            users_inner = ttk.Frame(users_frame)
            users_inner.pack(fill=BOTH, expand=True, padx=20, pady=20)
            notebook.add(users_frame, text="Utilisateurs")
            self._build_users_settings(users_inner)

        # Database tab
        db_frame = ttk.Frame(notebook)
        db_inner = ttk.Frame(db_frame)
        db_inner.pack(fill=BOTH, expand=True, padx=20, pady=20)
        notebook.add(db_frame, text="Base de données")
        self._build_database_settings(db_inner)

    def _build_general_settings(self, parent: ttk.Frame) -> None:
        """Build general settings tab."""
        settings = get_settings()

        # Application info
        info_frame = ttk.LabelFrame(parent, text="Informations")
        info_frame.pack(fill=X, pady=(0, 20))
        info_inner = ttk.Frame(info_frame)
        info_inner.pack(fill=X, padx=15, pady=15)

        info_items = [
            ("Application:", settings.app_name),
            ("Version:", settings.app_version),
            ("Thème:", settings.ui.theme),
        ]

        for label, value in info_items:
            row = ttk.Frame(info_inner)
            row.pack(fill=X, pady=3)
            ttk.Label(row, text=label, width=15).pack(side=LEFT)
            ttk.Label(row, text=value).pack(side=LEFT)

        # UI Settings
        ui_frame = ttk.LabelFrame(parent, text="Interface")
        ui_frame.pack(fill=X, pady=(0, 20))
        ui_inner = ttk.Frame(ui_frame)
        ui_inner.pack(fill=X, padx=15, pady=15)

        # Theme selection
        theme_row = ttk.Frame(ui_inner)
        theme_row.pack(fill=X, pady=5)
        ttk.Label(theme_row, text="Thème:", width=15).pack(side=LEFT)

        self._theme_combo = ttk.Combobox(
            theme_row,
            values=["darkly", "superhero", "cyborg", "solar", "cosmo", "flatly"],
            state="readonly",
            width=20,
        )
        self._theme_combo.set(settings.ui.theme)
        self._theme_combo.pack(side=LEFT)

        ttk.Button(
            theme_row,
            text="Appliquer",
            bootstyle="info-outline",
            command=self._apply_theme,
        ).pack(side=LEFT, padx=10)

        # Logging settings
        log_frame = ttk.LabelFrame(parent, text="Journalisation")
        log_frame.pack(fill=X)
        log_inner = ttk.Frame(log_frame)
        log_inner.pack(fill=X, padx=15, pady=15)

        log_row = ttk.Frame(log_inner)
        log_row.pack(fill=X, pady=5)
        ttk.Label(log_row, text="Niveau de log:", width=15).pack(side=LEFT)

        self._log_combo = ttk.Combobox(
            log_row,
            values=["DEBUG", "INFO", "WARNING", "ERROR"],
            state="readonly",
            width=20,
        )
        self._log_combo.set(settings.log_level)
        self._log_combo.pack(side=LEFT)

    def _build_security_settings(self, parent: ttk.Frame) -> None:
        """Build security settings tab."""
        settings = get_settings()

        # Session settings
        session_frame = ttk.LabelFrame(parent, text="Sessions")
        session_frame.pack(fill=X, pady=(0, 20))
        session_inner = ttk.Frame(session_frame)
        session_inner.pack(fill=X, padx=15, pady=15)

        # Session timeout
        timeout_row = ttk.Frame(session_inner)
        timeout_row.pack(fill=X, pady=5)
        ttk.Label(timeout_row, text="Timeout session (min):", width=20).pack(side=LEFT)

        self._timeout_spin = ttk.Spinbox(
            timeout_row,
            from_=5,
            to=120,
            width=10,
        )
        self._timeout_spin.set(settings.security.session_timeout_minutes)
        self._timeout_spin.pack(side=LEFT)

        # Login security
        login_frame = ttk.LabelFrame(parent, text="Connexion")
        login_frame.pack(fill=X, pady=(0, 20))
        login_inner = ttk.Frame(login_frame)
        login_inner.pack(fill=X, padx=15, pady=15)

        # Max attempts
        attempts_row = ttk.Frame(login_inner)
        attempts_row.pack(fill=X, pady=5)
        ttk.Label(attempts_row, text="Tentatives max:", width=20).pack(side=LEFT)

        self._attempts_spin = ttk.Spinbox(
            attempts_row,
            from_=3,
            to=10,
            width=10,
        )
        self._attempts_spin.set(settings.security.max_login_attempts)
        self._attempts_spin.pack(side=LEFT)

        # Lockout duration
        lockout_row = ttk.Frame(login_inner)
        lockout_row.pack(fill=X, pady=5)
        ttk.Label(lockout_row, text="Durée verrouillage (min):", width=20).pack(side=LEFT)

        self._lockout_spin = ttk.Spinbox(
            lockout_row,
            from_=5,
            to=60,
            width=10,
        )
        self._lockout_spin.set(settings.security.lockout_duration_minutes)
        self._lockout_spin.pack(side=LEFT)

        # Password policy info
        policy_frame = ttk.LabelFrame(parent, text="Politique de mot de passe")
        policy_frame.pack(fill=X)
        policy_inner = ttk.Frame(policy_frame)
        policy_inner.pack(fill=X, padx=15, pady=15)

        policies = [
            "Minimum 8 caractères",
            "Au moins une majuscule",
            "Au moins une minuscule",
            "Au moins un chiffre",
            "Au moins un caractère spécial",
        ]

        for policy in policies:
            ttk.Label(policy_inner, text=f"• {policy}").pack(anchor=W, pady=2)

    def _build_scanner_settings(self, parent: ttk.Frame) -> None:
        """Build scanner settings tab."""
        settings = get_settings()

        # Nmap settings
        nmap_frame = ttk.LabelFrame(parent, text="Nmap")
        nmap_frame.pack(fill=X, pady=(0, 20))
        nmap_inner = ttk.Frame(nmap_frame)
        nmap_inner.pack(fill=X, padx=15, pady=15)

        nmap_path_row = ttk.Frame(nmap_inner)
        nmap_path_row.pack(fill=X, pady=5)
        ttk.Label(nmap_path_row, text="Chemin Nmap:", width=15).pack(side=LEFT)
        self._nmap_path = ttk.Entry(nmap_path_row, width=40)
        self._nmap_path.insert(0, settings.scanner.nmap_path or "")
        self._nmap_path.pack(side=LEFT)

        ttk.Button(
            nmap_path_row,
            text="Détecter",
            bootstyle="info-outline",
            command=self._detect_nmap,
        ).pack(side=LEFT, padx=10)

        # OpenVAS settings
        openvas_frame = ttk.LabelFrame(parent, text="OpenVAS / Greenbone")
        openvas_frame.pack(fill=X, pady=(0, 20))
        openvas_inner = ttk.Frame(openvas_frame)
        openvas_inner.pack(fill=X, padx=15, pady=15)

        fields = [
            ("host", "Hôte:", settings.scanner.openvas_host),
            ("port", "Port:", str(settings.scanner.openvas_port)),
            ("user", "Utilisateur:", settings.scanner.openvas_username),
        ]

        self._openvas_fields = {}
        for key, label, value in fields:
            row = ttk.Frame(openvas_inner)
            row.pack(fill=X, pady=5)
            ttk.Label(row, text=label, width=15).pack(side=LEFT)
            entry = ttk.Entry(row, width=30)
            entry.insert(0, value)
            entry.pack(side=LEFT)
            self._openvas_fields[key] = entry

        ttk.Button(
            openvas_inner,
            text="Tester la connexion",
            bootstyle="info-outline",
            command=self._test_openvas,
        ).pack(anchor=W, pady=(10, 0))

        # Nuclei settings
        nuclei_frame = ttk.LabelFrame(parent, text="Nuclei")
        nuclei_frame.pack(fill=X)
        nuclei_inner = ttk.Frame(nuclei_frame)
        nuclei_inner.pack(fill=X, padx=15, pady=15)

        nuclei_path_row = ttk.Frame(nuclei_inner)
        nuclei_path_row.pack(fill=X, pady=5)
        ttk.Label(nuclei_path_row, text="Chemin Nuclei:", width=15).pack(side=LEFT)
        self._nuclei_path = ttk.Entry(nuclei_path_row, width=40)
        self._nuclei_path.insert(0, settings.scanner.nuclei_path or "")
        self._nuclei_path.pack(side=LEFT)

        templates_row = ttk.Frame(nuclei_inner)
        templates_row.pack(fill=X, pady=5)
        ttk.Label(templates_row, text="Templates:", width=15).pack(side=LEFT)
        self._templates_path = ttk.Entry(templates_row, width=40)
        self._templates_path.insert(0, settings.scanner.nuclei_templates_path or "")
        self._templates_path.pack(side=LEFT)

    def _build_users_settings(self, parent: ttk.Frame) -> None:
        """Build users management tab."""
        # Toolbar
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=X, pady=(0, 15))

        ttk.Button(
            toolbar,
            text="+ Nouvel utilisateur",
            bootstyle="success",
            command=self._new_user,
        ).pack(side=LEFT)

        # Users list
        columns = [
            ("username", "Utilisateur", 150),
            ("email", "Email", 200),
            ("role", "Rôle", 100),
            ("status", "Statut", 80),
            ("last_login", "Dernière connexion", 150),
        ]

        scroll_frame = ttk.Frame(parent)
        scroll_frame.pack(fill=BOTH, expand=True)

        scrollbar = ttk.Scrollbar(scroll_frame, orient=VERTICAL)
        scrollbar.pack(side=RIGHT, fill=Y)

        self._users_tree = ttk.Treeview(
            scroll_frame,
            columns=[c[0] for c in columns],
            show="headings",
            yscrollcommand=scrollbar.set,
        )

        for col_id, heading, width in columns:
            self._users_tree.heading(col_id, text=heading, anchor=W)
            self._users_tree.column(col_id, width=width, anchor=W)

        self._users_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=self._users_tree.yview)

        # Load users
        self._load_users()

    def _build_database_settings(self, parent: ttk.Frame) -> None:
        """Build database settings tab."""
        # Database info
        info_frame = ttk.LabelFrame(parent, text="Informations")
        info_frame.pack(fill=X, pady=(0, 20))
        info_inner = ttk.Frame(info_frame)
        info_inner.pack(fill=X, padx=15, pady=15)

        db = get_db()
        stats = db.get_stats()

        info_items = [
            ("Chemin:", stats["path"]),
            ("Taille:", f"{stats['size_bytes'] / 1024 / 1024:.2f} MB"),
            ("Mode journal:", stats["journal_mode"]),
            ("Pages:", str(stats["page_count"])),
        ]

        for label, value in info_items:
            row = ttk.Frame(info_inner)
            row.pack(fill=X, pady=3)
            ttk.Label(row, text=label, width=15).pack(side=LEFT)
            ttk.Label(row, text=value).pack(side=LEFT)

        # Maintenance
        maint_frame = ttk.LabelFrame(parent, text="Maintenance")
        maint_frame.pack(fill=X, pady=(0, 20))
        maint_inner = ttk.Frame(maint_frame)
        maint_inner.pack(fill=X, padx=15, pady=15)

        ttk.Button(
            maint_inner,
            text="Sauvegarder la base",
            bootstyle="info",
            command=self._backup_database,
        ).pack(side=LEFT, padx=(0, 10))

        ttk.Button(
            maint_inner,
            text="Optimiser (VACUUM)",
            bootstyle="secondary",
            command=self._vacuum_database,
        ).pack(side=LEFT, padx=10)

        ttk.Button(
            maint_inner,
            text="Nettoyer les sessions expirées",
            bootstyle="warning-outline",
            command=self._cleanup_sessions,
        ).pack(side=LEFT, padx=10)

    def _apply_theme(self) -> None:
        """Apply selected theme."""
        theme = self._theme_combo.get()
        Messagebox.show_info(
            f"Le thème '{theme}' sera appliqué au prochain redémarrage.",
            "Changement de thème",
            parent=self.app.root
        )

    def _detect_nmap(self) -> None:
        """Detect Nmap installation."""
        import shutil
        nmap_path = shutil.which("nmap")
        if nmap_path:
            self._nmap_path.delete(0, END)
            self._nmap_path.insert(0, nmap_path)
            Messagebox.show_info(f"Nmap détecté: {nmap_path}", "Nmap", parent=self.app.root)
        else:
            Messagebox.show_warning("Nmap non trouvé dans le PATH.", "Nmap", parent=self.app.root)

    def _test_openvas(self) -> None:
        """Test OpenVAS connection."""
        Messagebox.show_info(
            "Le test de connexion OpenVAS sera disponible dans une prochaine version.",
            "OpenVAS",
            parent=self.app.root
        )

    def _new_user(self) -> None:
        """Create new user."""
        Messagebox.show_info(
            "La création d'utilisateur sera disponible dans une prochaine version.",
            "Nouvel utilisateur",
            parent=self.app.root
        )

    def _load_users(self) -> None:
        """Load users list."""
        from secop.infrastructure.database.repositories.user_repository import UserRepository

        db = get_db()
        with db.get_session() as session:
            repo = UserRepository(session)
            users = repo.get_all()

            self._users_tree.delete(*self._users_tree.get_children())

            for user in users:
                last_login = user.last_login.strftime("%d/%m/%Y %H:%M") if user.last_login else "-"
                status = "Actif" if user.is_active else "Inactif"

                self._users_tree.insert("", END, values=(
                    user.username,
                    user.email,
                    user.role.value if user.role else "-",
                    status,
                    last_login,
                ))

    def _backup_database(self) -> None:
        """Backup database."""
        from tkinter import filedialog
        from datetime import datetime

        filepath = filedialog.asksaveasfilename(
            title="Sauvegarder la base de données",
            defaultextension=".db",
            initialfile=f"secop_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            filetypes=[("SQLite files", "*.db")],
            parent=self.app.root
        )

        if filepath:
            db = get_db()
            db.backup(filepath)
            Messagebox.show_info(
                f"Base de données sauvegardée:\n{filepath}",
                "Sauvegarde",
                parent=self.app.root
            )

    def _vacuum_database(self) -> None:
        """Vacuum database."""
        db = get_db()
        db.execute_raw("VACUUM")
        Messagebox.show_info(
            "Base de données optimisée.",
            "Optimisation",
            parent=self.app.root
        )

    def _cleanup_sessions(self) -> None:
        """Cleanup expired sessions."""
        from secop.auth.authentication import AuthenticationService

        auth = AuthenticationService()
        count = auth.cleanup_expired_sessions()
        Messagebox.show_info(
            f"{count} session(s) expirée(s) supprimée(s).",
            "Nettoyage",
            parent=self.app.root
        )
