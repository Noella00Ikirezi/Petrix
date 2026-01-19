"""Base view class for all views."""

from abc import ABC, abstractmethod
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from typing import TYPE_CHECKING, Any, Callable, Optional

if TYPE_CHECKING:
    from ..app import SecOpApplication


class BaseView(ABC):
    """
    Abstract base class for all views.

    Provides common functionality for view lifecycle management,
    event handling, and UI building.
    """

    def __init__(self, parent: ttk.Frame, app: "SecOpApplication"):
        """
        Initialize the view.

        Args:
            parent: Parent frame to contain this view
            app: Reference to main application
        """
        self.parent = parent
        self.app = app
        self.frame = ttk.Frame(parent)

        # Event callbacks
        self._data_changed_callbacks: list[Callable[[Any], None]] = []
        self._error_callbacks: list[Callable[[Exception], None]] = []

        # Build UI
        self._build_ui()

    @abstractmethod
    def _build_ui(self) -> None:
        """Build the view's UI components. Must be implemented by subclasses."""
        pass

    def show(self) -> None:
        """Show the view."""
        self.frame.pack(fill=BOTH, expand=True)
        self.on_show()

    def hide(self) -> None:
        """Hide the view."""
        self.frame.pack_forget()
        self.on_hide()

    def on_show(self) -> None:
        """Called when view becomes visible. Override to load data."""
        pass

    def on_hide(self) -> None:
        """Called when view is hidden. Override for cleanup."""
        pass

    def refresh(self) -> None:
        """Refresh view data. Override to reload data."""
        pass

    def on_data_changed(self, callback: Callable[[Any], None]) -> None:
        """Register callback for data changes."""
        self._data_changed_callbacks.append(callback)

    def on_error(self, callback: Callable[[Exception], None]) -> None:
        """Register callback for errors."""
        self._error_callbacks.append(callback)

    def _notify_data_changed(self, data: Any) -> None:
        """Notify all data change callbacks."""
        for callback in self._data_changed_callbacks:
            try:
                callback(data)
            except Exception as e:
                self._notify_error(e)

    def _notify_error(self, error: Exception) -> None:
        """Notify all error callbacks."""
        for callback in self._error_callbacks:
            try:
                callback(error)
            except Exception:
                pass

    def _create_header_section(
        self,
        title: str,
        subtitle: Optional[str] = None,
        action_buttons: Optional[list[tuple[str, str, Callable]]] = None,
    ) -> ttk.Frame:
        """
        Create a header section with title and optional action buttons.

        Args:
            title: Section title
            subtitle: Optional subtitle
            action_buttons: List of (text, bootstyle, callback) tuples

        Returns:
            Header frame
        """
        header = ttk.Frame(self.frame)
        header.pack(fill=X, pady=(0, 20))

        # Title
        title_frame = ttk.Frame(header)
        title_frame.pack(side=LEFT)

        ttk.Label(
            title_frame,
            text=title,
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor=W)

        if subtitle:
            ttk.Label(
                title_frame,
                text=subtitle,
                font=("Segoe UI", 10),
                bootstyle="secondary",
            ).pack(anchor=W)

        # Action buttons
        if action_buttons:
            btn_frame = ttk.Frame(header)
            btn_frame.pack(side=RIGHT)

            for text, style, callback in action_buttons:
                ttk.Button(
                    btn_frame,
                    text=text,
                    bootstyle=style,
                    command=callback,
                ).pack(side=LEFT, padx=5)

        return header

    def _create_card(
        self,
        parent: ttk.Frame,
        title: str,
        value: str,
        subtitle: Optional[str] = None,
        bootstyle: str = "default",
    ) -> ttk.Frame:
        """
        Create a dashboard-style card widget.

        Args:
            parent: Parent frame
            title: Card title
            value: Main value to display
            subtitle: Optional subtitle
            bootstyle: Bootstrap style

        Returns:
            Card frame
        """
        card = ttk.Frame(parent, bootstyle=f"{bootstyle}")
        card.pack(side=LEFT, fill=BOTH, expand=True, padx=5)

        inner = ttk.Frame(card)
        inner.pack(fill=BOTH, expand=True, padx=15, pady=15)

        ttk.Label(
            inner,
            text=title,
            font=("Segoe UI", 10),
            bootstyle="secondary",
        ).pack(anchor=W)

        ttk.Label(
            inner,
            text=value,
            font=("Segoe UI", 28, "bold"),
        ).pack(anchor=W, pady=(5, 0))

        if subtitle:
            ttk.Label(
                inner,
                text=subtitle,
                font=("Segoe UI", 9),
                bootstyle="secondary",
            ).pack(anchor=W)

        return card

    def _create_table(
        self,
        parent: ttk.Frame,
        columns: list[tuple[str, str, int]],
        height: int = 15,
    ) -> ttk.Treeview:
        """
        Create a table (Treeview) widget.

        Args:
            parent: Parent frame
            columns: List of (id, heading, width) tuples
            height: Number of visible rows

        Returns:
            Treeview widget
        """
        # Container with scrollbar
        container = ttk.Frame(parent)
        container.pack(fill=BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(container, orient=VERTICAL)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Treeview
        column_ids = [col[0] for col in columns]
        tree = ttk.Treeview(
            container,
            columns=column_ids,
            show="headings",
            height=height,
            yscrollcommand=scrollbar.set,
            bootstyle="primary",
        )

        for col_id, heading, width in columns:
            tree.heading(col_id, text=heading, anchor=W)
            tree.column(col_id, width=width, anchor=W)

        tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=tree.yview)

        return tree

    def _create_form_field(
        self,
        parent: ttk.Frame,
        label: str,
        widget_type: str = "entry",
        values: Optional[list] = None,
        **kwargs,
    ) -> tuple[ttk.Frame, Any]:
        """
        Create a form field with label.

        Args:
            parent: Parent frame
            label: Field label
            widget_type: Type of widget (entry, combobox, text)
            values: Values for combobox
            **kwargs: Additional widget arguments

        Returns:
            Tuple of (frame, widget)
        """
        frame = ttk.Frame(parent)
        frame.pack(fill=X, pady=5)

        ttk.Label(
            frame,
            text=label,
            font=("Segoe UI", 10),
            width=15,
            anchor=W,
        ).pack(side=LEFT)

        if widget_type == "entry":
            widget = ttk.Entry(frame, **kwargs)
        elif widget_type == "combobox":
            widget = ttk.Combobox(frame, values=values or [], state="readonly", **kwargs)
        elif widget_type == "text":
            widget = ttk.Text(frame, height=kwargs.pop("height", 4), **kwargs)
        else:
            widget = ttk.Entry(frame, **kwargs)

        widget.pack(side=LEFT, fill=X, expand=True)

        return frame, widget

    def run_async(self, task: Callable, callback: Optional[Callable] = None) -> None:
        """Run a task asynchronously using app's thread pool."""
        self.app.run_background_task(task, callback)

    def set_status(self, message: str) -> None:
        """Update application status bar."""
        self.app.set_status(message)
