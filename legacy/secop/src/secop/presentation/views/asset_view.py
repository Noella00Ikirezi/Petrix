"""Asset inventory view."""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox, Querybox
from typing import TYPE_CHECKING, Optional, List
from datetime import datetime

from .base_view import BaseView
from secop.infrastructure.database.connection import get_db
from secop.infrastructure.database.repositories.asset_repository import AssetRepository
from secop.infrastructure.database.models import Asset, AssetType, AssetStatus, Criticality
from secop.auth.authorization import get_auth_service, Permission

if TYPE_CHECKING:
    from ..app import SecOpApplication


class AssetView(BaseView):
    """Asset inventory management view."""

    def __init__(self, parent: ttk.Frame, app: "SecOpApplication"):
        self._selected_asset: Optional[Asset] = None
        self._assets: List[Asset] = []
        super().__init__(parent, app)

    def _build_ui(self) -> None:
        """Build asset view UI."""
        # Toolbar
        self._build_toolbar()

        # Main content area
        content = ttk.Frame(self.frame)
        content.pack(fill=BOTH, expand=True)

        # Left panel - Asset list
        self._build_asset_list(content)

        # Right panel - Asset details
        self._build_detail_panel(content)

    def _build_toolbar(self) -> None:
        """Build toolbar with actions."""
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill=X, pady=(0, 15))

        # Left side - Actions
        left_frame = ttk.Frame(toolbar)
        left_frame.pack(side=LEFT)

        ttk.Button(
            left_frame,
            text="+ Nouvel Actif",
            bootstyle="success",
            command=self._new_asset,
        ).pack(side=LEFT, padx=(0, 5))

        ttk.Button(
            left_frame,
            text="Importer CSV",
            bootstyle="info-outline",
            command=self._import_csv,
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            left_frame,
            text="Exporter",
            bootstyle="secondary-outline",
            command=self._export_csv,
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            left_frame,
            text="Actualiser",
            bootstyle="secondary-outline",
            command=self.refresh,
        ).pack(side=LEFT, padx=5)

        # Right side - Search and filters
        right_frame = ttk.Frame(toolbar)
        right_frame.pack(side=RIGHT)

        # Search
        self._search_var = ttk.StringVar()
        search_entry = ttk.Entry(
            right_frame,
            textvariable=self._search_var,
            width=25,
        )
        search_entry.pack(side=LEFT, padx=5)
        search_entry.bind("<Return>", lambda e: self._search())

        ttk.Button(
            right_frame,
            text="Rechercher",
            bootstyle="primary",
            command=self._search,
        ).pack(side=LEFT)

        # Filter by type
        ttk.Label(right_frame, text="Type:").pack(side=LEFT, padx=(15, 5))
        self._type_filter = ttk.Combobox(
            right_frame,
            values=["Tous"] + [t.value for t in AssetType],
            state="readonly",
            width=12,
        )
        self._type_filter.set("Tous")
        self._type_filter.pack(side=LEFT)
        self._type_filter.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())

        # Filter by status
        ttk.Label(right_frame, text="Statut:").pack(side=LEFT, padx=(10, 5))
        self._status_filter = ttk.Combobox(
            right_frame,
            values=["Tous"] + [s.value for s in AssetStatus],
            state="readonly",
            width=12,
        )
        self._status_filter.set("Tous")
        self._status_filter.pack(side=LEFT)
        self._status_filter.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())

    def _build_asset_list(self, parent: ttk.Frame) -> None:
        """Build asset list panel."""
        list_frame = ttk.Frame(parent)
        list_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))

        # Stats bar
        stats_frame = ttk.Frame(list_frame)
        stats_frame.pack(fill=X, pady=(0, 10))

        self._stats_label = ttk.Label(
            stats_frame,
            text="0 actifs",
            font=("Segoe UI", 10),
            bootstyle="secondary",
        )
        self._stats_label.pack(side=LEFT)

        # Asset table
        columns = [
            ("name", "Nom", 150),
            ("type", "Type", 100),
            ("ip", "IP", 120),
            ("os", "OS", 120),
            ("status", "Statut", 80),
            ("criticality", "Criticité", 80),
        ]

        # Scrollbar
        scroll_frame = ttk.Frame(list_frame)
        scroll_frame.pack(fill=BOTH, expand=True)

        scrollbar = ttk.Scrollbar(scroll_frame, orient=VERTICAL)
        scrollbar.pack(side=RIGHT, fill=Y)

        self._asset_tree = ttk.Treeview(
            scroll_frame,
            columns=[c[0] for c in columns],
            show="headings",
            yscrollcommand=scrollbar.set,
            bootstyle="primary",
        )

        for col_id, heading, width in columns:
            self._asset_tree.heading(col_id, text=heading, anchor=W)
            self._asset_tree.column(col_id, width=width, anchor=W)

        self._asset_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=self._asset_tree.yview)

        # Bind selection event
        self._asset_tree.bind("<<TreeviewSelect>>", self._on_asset_select)
        self._asset_tree.bind("<Double-1>", lambda e: self._edit_asset())

    def _build_detail_panel(self, parent: ttk.Frame) -> None:
        """Build asset detail panel."""
        detail_frame = ttk.LabelFrame(parent, text="Détails de l'actif", width=350)
        detail_frame.pack(side=RIGHT, fill=Y)
        detail_frame.pack_propagate(False)

        inner_detail = ttk.Frame(detail_frame)
        inner_detail.pack(fill=BOTH, expand=True, padx=15, pady=15)

        # Form fields
        self._detail_fields = {}

        fields = [
            ("name", "Nom"),
            ("type", "Type"),
            ("ip_address", "Adresse IP"),
            ("mac_address", "Adresse MAC"),
            ("hostname", "Hostname"),
            ("os", "Système"),
            ("os_version", "Version OS"),
            ("location", "Localisation"),
            ("department", "Département"),
            ("owner", "Propriétaire"),
            ("criticality", "Criticité"),
            ("status", "Statut"),
        ]

        for field_id, label in fields:
            frame = ttk.Frame(inner_detail)
            frame.pack(fill=X, pady=3)

            ttk.Label(
                frame,
                text=f"{label}:",
                width=12,
                anchor=W,
            ).pack(side=LEFT)

            value_label = ttk.Label(
                frame,
                text="-",
                anchor=W,
            )
            value_label.pack(side=LEFT, fill=X, expand=True)

            self._detail_fields[field_id] = value_label

        # Notes section
        ttk.Label(inner_detail, text="Notes:").pack(anchor=W, pady=(15, 5))
        self._notes_text = ttk.Text(inner_detail, height=4, state=DISABLED)
        self._notes_text.pack(fill=X)

        # Action buttons
        btn_frame = ttk.Frame(inner_detail)
        btn_frame.pack(fill=X, pady=(20, 0))

        self._edit_btn = ttk.Button(
            btn_frame,
            text="Modifier",
            bootstyle="info",
            command=self._edit_asset,
            state=DISABLED,
        )
        self._edit_btn.pack(side=LEFT, padx=(0, 5))

        self._delete_btn = ttk.Button(
            btn_frame,
            text="Supprimer",
            bootstyle="danger-outline",
            command=self._delete_asset,
            state=DISABLED,
        )
        self._delete_btn.pack(side=LEFT)

    def on_show(self) -> None:
        """Load assets when view is shown."""
        self.refresh()

    def refresh(self) -> None:
        """Refresh asset list."""
        self.set_status("Chargement des actifs...")
        self.run_async(self._load_assets, self._update_asset_list)

    def _load_assets(self) -> List[Asset]:
        """Load assets from database."""
        db = get_db()

        with db.get_session() as session:
            repo = AssetRepository(session)

            # Apply filters
            asset_type = None
            status = None

            type_val = self._type_filter.get()
            if type_val != "Tous":
                asset_type = AssetType(type_val)

            status_val = self._status_filter.get()
            if status_val != "Tous":
                status = AssetStatus(status_val)

            search = self._search_var.get().strip() or None

            assets = repo.find_by_criteria(
                asset_type=asset_type,
                status=status,
                search=search,
                limit=500,
            )

            # Detach from session for thread safety
            session.expunge_all()
            return assets

    def _update_asset_list(self, assets) -> None:
        """Update asset list with loaded data."""
        if isinstance(assets, Exception):
            self.set_status(f"Erreur: {assets}")
            return

        self._assets = assets

        # Clear tree
        self._asset_tree.delete(*self._asset_tree.get_children())

        # Insert assets
        for asset in assets:
            self._asset_tree.insert("", END, iid=str(asset.id), values=(
                asset.name,
                asset.asset_type.value if asset.asset_type else "-",
                asset.ip_address or "-",
                asset.os or "-",
                asset.status.value if asset.status else "-",
                asset.criticality.value if asset.criticality else "-",
            ))

        # Update stats
        self._stats_label.configure(text=f"{len(assets)} actif(s)")
        self.set_status(f"{len(assets)} actifs chargés")

    def _on_asset_select(self, event) -> None:
        """Handle asset selection."""
        selection = self._asset_tree.selection()
        if not selection:
            self._clear_detail()
            return

        asset_id = int(selection[0])
        asset = next((a for a in self._assets if a.id == asset_id), None)

        if asset:
            self._selected_asset = asset
            self._show_asset_detail(asset)

    def _show_asset_detail(self, asset: Asset) -> None:
        """Display asset details."""
        self._detail_fields["name"].configure(text=asset.name or "-")
        self._detail_fields["type"].configure(
            text=asset.asset_type.value if asset.asset_type else "-"
        )
        self._detail_fields["ip_address"].configure(text=asset.ip_address or "-")
        self._detail_fields["mac_address"].configure(text=asset.mac_address or "-")
        self._detail_fields["hostname"].configure(text=asset.hostname or "-")
        self._detail_fields["os"].configure(text=asset.os or "-")
        self._detail_fields["os_version"].configure(text=asset.os_version or "-")
        self._detail_fields["location"].configure(text=asset.location or "-")
        self._detail_fields["department"].configure(text=asset.department or "-")
        self._detail_fields["owner"].configure(text=asset.owner or "-")
        self._detail_fields["criticality"].configure(
            text=asset.criticality.value if asset.criticality else "-"
        )
        self._detail_fields["status"].configure(
            text=asset.status.value if asset.status else "-"
        )

        # Notes
        self._notes_text.configure(state=NORMAL)
        self._notes_text.delete("1.0", END)
        self._notes_text.insert("1.0", asset.notes or "")
        self._notes_text.configure(state=DISABLED)

        # Enable buttons
        self._edit_btn.configure(state=NORMAL)
        self._delete_btn.configure(state=NORMAL)

    def _clear_detail(self) -> None:
        """Clear detail panel."""
        self._selected_asset = None
        for field in self._detail_fields.values():
            field.configure(text="-")

        self._notes_text.configure(state=NORMAL)
        self._notes_text.delete("1.0", END)
        self._notes_text.configure(state=DISABLED)

        self._edit_btn.configure(state=DISABLED)
        self._delete_btn.configure(state=DISABLED)

    def _search(self) -> None:
        """Execute search."""
        self.refresh()

    def _apply_filters(self) -> None:
        """Apply filters."""
        self.refresh()

    def _new_asset(self) -> None:
        """Open new asset dialog."""
        from ..dialogs.asset_dialog import AssetDialog

        dialog = AssetDialog(self.app.root, None)
        self.app.root.wait_window(dialog.dialog)

        if dialog.result:
            self.refresh()

    def _edit_asset(self) -> None:
        """Edit selected asset."""
        if not self._selected_asset:
            return

        from ..dialogs.asset_dialog import AssetDialog

        dialog = AssetDialog(self.app.root, self._selected_asset)
        self.app.root.wait_window(dialog.dialog)

        if dialog.result:
            self.refresh()

    def _delete_asset(self) -> None:
        """Delete selected asset."""
        if not self._selected_asset:
            return

        # Check permission
        auth = get_auth_service()
        if not auth.get_context().has_permission(Permission.ASSET_DELETE):
            Messagebox.show_error(
                "Vous n'avez pas la permission de supprimer des actifs.",
                "Permission refusée",
                parent=self.app.root
            )
            return

        # Confirm
        result = Messagebox.yesno(
            f"Voulez-vous vraiment supprimer l'actif '{self._selected_asset.name}' ?",
            "Confirmer la suppression",
            parent=self.app.root
        )

        if result == "Yes":
            db = get_db()
            with db.get_session() as session:
                repo = AssetRepository(session)
                repo.delete_by_id(self._selected_asset.id)

            self._clear_detail()
            self.refresh()
            self.set_status("Actif supprimé")

    def _import_csv(self) -> None:
        """Import assets from CSV."""
        from tkinter import filedialog

        filepath = filedialog.askopenfilename(
            title="Importer des actifs",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            parent=self.app.root
        )

        if filepath:
            # TODO: Implement CSV import
            Messagebox.show_info(
                "L'import CSV sera disponible dans une prochaine version.",
                "Import CSV",
                parent=self.app.root
            )

    def _export_csv(self) -> None:
        """Export assets to CSV."""
        from tkinter import filedialog

        filepath = filedialog.asksaveasfilename(
            title="Exporter les actifs",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            parent=self.app.root
        )

        if filepath:
            # TODO: Implement CSV export
            Messagebox.show_info(
                "L'export CSV sera disponible dans une prochaine version.",
                "Export CSV",
                parent=self.app.root
            )
