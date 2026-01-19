"""Login dialog for user authentication."""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from typing import Optional, Tuple

from secop.auth.authentication import AuthenticationService
from secop.auth.authorization import AuthContext
from secop.core.exceptions import AuthenticationError


class LoginDialog:
    """
    Login dialog for user authentication.

    Modal dialog that handles user login with username/password.
    """

    def __init__(self, parent: ttk.Window, auth_service: AuthenticationService):
        """
        Initialize login dialog.

        Args:
            parent: Parent window
            auth_service: Authentication service instance
        """
        self.parent = parent
        self.auth_service = auth_service
        self.result: Optional[Tuple[AuthContext, str]] = None

        # Create dialog
        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("Connexion - SecOp Audit")
        self.dialog.resizable(False, False)

        # Make modal
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center dialog
        self._center_dialog(400, 350)

        # Build UI
        self._build_ui()

        # Focus username field
        self.dialog.after(100, lambda: self._username_entry.focus_set())

    def _center_dialog(self, width: int, height: int) -> None:
        """Center dialog on parent window."""
        self.dialog.geometry(f"{width}x{height}")

        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (width // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (height // 2)

        self.dialog.geometry(f"+{x}+{y}")

    def _build_ui(self) -> None:
        """Build dialog UI."""
        # Main container
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=BOTH, expand=True, padx=30, pady=30)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=X, pady=(0, 30))

        ttk.Label(
            header_frame,
            text="SecOp Audit",
            font=("Segoe UI", 24, "bold"),
            bootstyle="primary",
        ).pack()

        ttk.Label(
            header_frame,
            text="Connectez-vous pour continuer",
            font=("Segoe UI", 10),
            bootstyle="secondary",
        ).pack(pady=(5, 0))

        # Form
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=X)

        # Username
        ttk.Label(
            form_frame,
            text="Nom d'utilisateur",
            font=("Segoe UI", 10),
        ).pack(anchor=W, pady=(0, 5))

        self._username_entry = ttk.Entry(
            form_frame,
            font=("Segoe UI", 11),
            width=40,
        )
        self._username_entry.pack(fill=X, pady=(0, 15))
        self._username_entry.bind("<Return>", lambda e: self._password_entry.focus_set())

        # Password
        ttk.Label(
            form_frame,
            text="Mot de passe",
            font=("Segoe UI", 10),
        ).pack(anchor=W, pady=(0, 5))

        self._password_entry = ttk.Entry(
            form_frame,
            font=("Segoe UI", 11),
            show="*",
            width=40,
        )
        self._password_entry.pack(fill=X, pady=(0, 10))
        self._password_entry.bind("<Return>", lambda e: self._login())

        # Error label
        self._error_label = ttk.Label(
            form_frame,
            text="",
            font=("Segoe UI", 9),
            bootstyle="danger",
            wraplength=340,
        )
        self._error_label.pack(fill=X, pady=(5, 10))

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=X, pady=(20, 0))

        self._login_btn = ttk.Button(
            btn_frame,
            text="Se connecter",
            bootstyle="primary",
            command=self._login,
            width=20,
        )
        self._login_btn.pack(side=RIGHT)

        ttk.Button(
            btn_frame,
            text="Quitter",
            bootstyle="secondary-outline",
            command=self._quit,
            width=10,
        ).pack(side=RIGHT, padx=(0, 10))

    def _login(self) -> None:
        """Handle login button click."""
        username = self._username_entry.get().strip()
        password = self._password_entry.get()

        # Validation
        if not username:
            self._show_error("Veuillez entrer un nom d'utilisateur")
            self._username_entry.focus_set()
            return

        if not password:
            self._show_error("Veuillez entrer un mot de passe")
            self._password_entry.focus_set()
            return

        # Clear error
        self._error_label.configure(text="")

        # Disable button during login
        self._login_btn.configure(state=DISABLED, text="Connexion...")

        try:
            # Attempt login
            context, token = self.auth_service.login(username, password)
            self.result = (context, token)
            self.dialog.destroy()

        except AuthenticationError as e:
            self._show_error(str(e))
            self._password_entry.delete(0, END)
            self._password_entry.focus_set()

        except Exception as e:
            self._show_error(f"Erreur de connexion: {e}")

        finally:
            # Only reconfigure if dialog still exists
            if self.dialog.winfo_exists() and self._login_btn.winfo_exists():
                self._login_btn.configure(state=NORMAL, text="Se connecter")

    def _show_error(self, message: str) -> None:
        """Show error message."""
        self._error_label.configure(text=message)

    def _quit(self) -> None:
        """Handle quit button click."""
        self.result = None
        self.dialog.destroy()
        self.parent.destroy()
