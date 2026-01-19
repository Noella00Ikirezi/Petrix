"""Main application window with navigation."""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from typing import Optional, Dict, Type, Callable
from queue import Queue
import threading
from loguru import logger

from secop.config.settings import get_settings
from secop.auth.authorization import get_auth_service, AuthContext
from secop.auth.authentication import AuthenticationService
from secop.core.events import EventBus, Event, EventType

from .views.base_view import BaseView
from .dialogs.login_dialog import LoginDialog


class SecOpApplication:
    """
    Main application class with navigation and view management.

    Implements lazy loading of views and thread-safe background task execution.
    """

    def __init__(self):
        self._settings = get_settings()
        self._event_bus = EventBus()
        self._auth_service = AuthenticationService()

        # Create main window
        self.root = ttk.Window(
            title=self._settings.app_name,
            themename=self._settings.ui.theme,
            size=(self._settings.ui.window_width, self._settings.ui.window_height),
            minsize=(1024, 700),
        )

        # Center window on screen
        self._center_window()

        # Task queues for background operations
        self._task_queue: Queue = Queue()
        self._result_queue: Queue = Queue()

        # View management
        self._views: Dict[str, BaseView] = {}
        self._current_view: Optional[BaseView] = None
        self._view_classes: Dict[str, Type[BaseView]] = {}

        # Session management
        self._session_token: Optional[str] = None
        self._auth_context: Optional[AuthContext] = None

        # Build UI
        self._setup_styles()
        self._build_ui()
        self._setup_event_handlers()

        # Start result polling
        self._poll_results()

        logger.info("SecOp Application initialized")

    def _center_window(self) -> None:
        """Center window on screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"+{x}+{y}")

    def _setup_styles(self) -> None:
        """Configure custom styles."""
        style = ttk.Style()

        # Navigation button style
        style.configure(
            "Nav.TButton",
            font=("Segoe UI", 10),
            padding=(15, 10),
        )

        # Active navigation button
        style.configure(
            "NavActive.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(15, 10),
        )

        # Header style
        style.configure(
            "Header.TLabel",
            font=("Segoe UI", 24, "bold"),
        )

        # Subheader style
        style.configure(
            "Subheader.TLabel",
            font=("Segoe UI", 12),
        )

    def _build_ui(self) -> None:
        """Build the main UI structure."""
        # Main container
        self._main_frame = ttk.Frame(self.root)
        self._main_frame.pack(fill=BOTH, expand=True)

        # Build navigation sidebar
        self._build_navigation()

        # Build content area
        self._build_content_area()

        # Build status bar
        self._build_status_bar()

    def _build_navigation(self) -> None:
        """Build navigation sidebar."""
        # Navigation frame
        self._nav_frame = ttk.Frame(self._main_frame, width=220)
        self._nav_frame.pack(side=LEFT, fill=Y)
        self._nav_frame.pack_propagate(False)

        # App logo/title
        title_frame = ttk.Frame(self._nav_frame)
        title_frame.pack(fill=X, pady=20, padx=10)

        ttk.Label(
            title_frame,
            text="SecOp",
            font=("Segoe UI", 20, "bold"),
            bootstyle="inverse-primary",
        ).pack()

        ttk.Label(
            title_frame,
            text="Audit Tool",
            font=("Segoe UI", 10),
            bootstyle="secondary",
        ).pack()

        # Separator
        ttk.Separator(self._nav_frame, orient=HORIZONTAL).pack(fill=X, padx=10)

        # Navigation buttons container
        self._nav_buttons_frame = ttk.Frame(self._nav_frame)
        self._nav_buttons_frame.pack(fill=BOTH, expand=True, pady=10)

        # Navigation items
        self._nav_items = [
            ("dashboard", "Dashboard", "speedometer2"),
            ("assets", "Inventaire", "hdd-stack"),
            ("scans", "Scans", "shield-check"),
            ("vulnerabilities", "Vulnérabilités", "bug"),
            ("audits", "Audits", "clipboard-check"),
            ("reports", "Rapports", "file-earmark-text"),
            ("settings", "Paramètres", "gear"),
        ]

        self._nav_buttons: Dict[str, ttk.Button] = {}

        for view_name, label, icon in self._nav_items:
            btn = ttk.Button(
                self._nav_buttons_frame,
                text=f"  {label}",
                style="Nav.TButton",
                bootstyle="dark-outline",
                command=lambda v=view_name: self._show_view(v),
                width=25,
            )
            btn.pack(fill=X, padx=10, pady=2)
            self._nav_buttons[view_name] = btn

        # Bottom section (user info, logout)
        bottom_frame = ttk.Frame(self._nav_frame)
        bottom_frame.pack(side=BOTTOM, fill=X, pady=10, padx=10)

        ttk.Separator(self._nav_frame, orient=HORIZONTAL).pack(
            side=BOTTOM, fill=X, padx=10
        )

        # User info label
        self._user_label = ttk.Label(
            bottom_frame,
            text="Non connecté",
            font=("Segoe UI", 9),
            bootstyle="secondary",
        )
        self._user_label.pack(pady=(0, 5))

        # Logout button
        self._logout_btn = ttk.Button(
            bottom_frame,
            text="Déconnexion",
            bootstyle="danger-outline",
            command=self._logout,
            width=25,
        )
        self._logout_btn.pack(fill=X)

    def _build_content_area(self) -> None:
        """Build main content area."""
        # Content container
        self._content_frame = ttk.Frame(self._main_frame)
        self._content_frame.pack(side=LEFT, fill=BOTH, expand=True)

        # Header bar
        self._header_frame = ttk.Frame(self._content_frame, height=60)
        self._header_frame.pack(fill=X, padx=20, pady=(20, 10))
        self._header_frame.pack_propagate(False)

        self._page_title = ttk.Label(
            self._header_frame,
            text="Dashboard",
            style="Header.TLabel",
        )
        self._page_title.pack(side=LEFT)

        # View container
        self._view_container = ttk.Frame(self._content_frame)
        self._view_container.pack(fill=BOTH, expand=True, padx=20, pady=10)

    def _build_status_bar(self) -> None:
        """Build status bar at bottom."""
        self._status_frame = ttk.Frame(self.root, height=25)
        self._status_frame.pack(side=BOTTOM, fill=X)

        self._status_label = ttk.Label(
            self._status_frame,
            text="Prêt",
            font=("Segoe UI", 9),
            bootstyle="secondary",
        )
        self._status_label.pack(side=LEFT, padx=10)

        # Version label
        version_label = ttk.Label(
            self._status_frame,
            text=f"v{self._settings.app_version}",
            font=("Segoe UI", 9),
            bootstyle="secondary",
        )
        version_label.pack(side=RIGHT, padx=10)

    def _setup_event_handlers(self) -> None:
        """Setup global event handlers."""
        # Subscribe to events
        self._event_bus.subscribe(EventType.USER_LOGIN, self._on_user_login)
        self._event_bus.subscribe(EventType.USER_LOGOUT, self._on_user_logout)

        # Window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _show_view(self, view_name: str) -> None:
        """Show a specific view."""
        # Check authentication
        if not get_auth_service().is_authenticated():
            self._show_login()
            return

        # Update navigation buttons
        for name, btn in self._nav_buttons.items():
            if name == view_name:
                btn.configure(bootstyle="primary")
            else:
                btn.configure(bootstyle="dark-outline")

        # Update page title
        titles = {
            "dashboard": "Dashboard",
            "assets": "Inventaire des Actifs",
            "scans": "Scans de Vulnérabilités",
            "vulnerabilities": "Vulnérabilités",
            "audits": "Audits",
            "reports": "Rapports",
            "settings": "Paramètres",
        }
        self._page_title.configure(text=titles.get(view_name, view_name.title()))

        # Hide current view
        if self._current_view:
            self._current_view.hide()

        # Show or create view
        if view_name not in self._views:
            self._create_view(view_name)

        if view_name in self._views:
            self._current_view = self._views[view_name]
            self._current_view.show()

    def _create_view(self, view_name: str) -> None:
        """Create a view instance (lazy loading)."""
        # Import views here to avoid circular imports
        from .views.dashboard_view import DashboardView
        from .views.asset_view import AssetView
        from .views.scan_view import ScanView
        from .views.vulnerability_view import VulnerabilityView
        from .views.audit_view import AuditView
        from .views.report_view import ReportView
        from .views.settings_view import SettingsView

        view_classes = {
            "dashboard": DashboardView,
            "assets": AssetView,
            "scans": ScanView,
            "vulnerabilities": VulnerabilityView,
            "audits": AuditView,
            "reports": ReportView,
            "settings": SettingsView,
        }

        view_class = view_classes.get(view_name)
        if view_class:
            try:
                self._views[view_name] = view_class(self._view_container, self)
                logger.debug(f"View created: {view_name}")
            except Exception as e:
                logger.error(f"Failed to create view {view_name}: {e}")
                self._show_error(f"Erreur lors du chargement de la vue: {e}")

    def _show_login(self) -> None:
        """Show login dialog."""
        dialog = LoginDialog(self.root, self._auth_service)
        self.root.wait_window(dialog.dialog)

        if dialog.result:
            self._session_token = dialog.result[1]
            self._auth_context = dialog.result[0]
            self._update_user_info()
            self._show_view("dashboard")

    def _logout(self) -> None:
        """Logout current user."""
        if self._session_token:
            try:
                self._auth_service.logout(self._session_token)
            except Exception as e:
                logger.error(f"Logout error: {e}")

        self._session_token = None
        self._auth_context = None
        self._user_label.configure(text="Non connecté")

        # Clear views
        if self._current_view:
            self._current_view.hide()
            self._current_view = None

        self._views.clear()

        # Show login
        self._show_login()

    def _update_user_info(self) -> None:
        """Update user info in navigation."""
        if self._auth_context:
            self._user_label.configure(
                text=f"{self._auth_context.username}\n({self._auth_context.role.name})"
            )

    def _on_user_login(self, event: Event) -> None:
        """Handle user login event."""
        logger.info(f"User logged in: {event.data.get('username')}")

    def _on_user_logout(self, event: Event) -> None:
        """Handle user logout event."""
        logger.info("User logged out")

    def _poll_results(self) -> None:
        """Poll for background task results."""
        try:
            while not self._result_queue.empty():
                callback, result = self._result_queue.get_nowait()
                if callback:
                    callback(result)
        except Exception as e:
            logger.error(f"Result polling error: {e}")
        finally:
            self.root.after(100, self._poll_results)

    def run_background_task(
        self, task_func: Callable, callback: Optional[Callable] = None, *args, **kwargs
    ) -> None:
        """
        Run a task in background thread.

        Args:
            task_func: Function to execute
            callback: Function to call with result
            *args, **kwargs: Arguments for task_func
        """

        def wrapper():
            try:
                result = task_func(*args, **kwargs)
                self._result_queue.put((callback, result))
            except Exception as e:
                logger.error(f"Background task error: {e}")
                self._result_queue.put((callback, e))

        thread = threading.Thread(target=wrapper, daemon=True)
        thread.start()

    def set_status(self, message: str) -> None:
        """Update status bar message."""
        self._status_label.configure(text=message)

    def _show_error(self, message: str) -> None:
        """Show error message dialog."""
        Messagebox.show_error(message, "Erreur", parent=self.root)

    def _show_info(self, message: str) -> None:
        """Show info message dialog."""
        Messagebox.show_info(message, "Information", parent=self.root)

    def _on_close(self) -> None:
        """Handle window close."""
        if self._session_token:
            try:
                self._auth_service.logout(self._session_token)
            except Exception:
                pass

        logger.info("Application closing")
        self.root.destroy()

    def run(self) -> None:
        """Start the application."""
        # Show login first
        self.root.after(100, self._show_login)

        # Start main loop
        logger.info("Starting SecOp Application")
        self.root.mainloop()
