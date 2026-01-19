"""Asset creation/edit dialog."""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from typing import Optional

from secop.infrastructure.database.connection import get_db
from secop.infrastructure.database.repositories.asset_repository import AssetRepository
from secop.infrastructure.database.models import Asset, AssetType, AssetStatus, Criticality
from secop.auth.authorization import get_auth_service, Permission


class AssetDialog:
    """Dialog for creating or editing an asset."""

    def __init__(self, parent: ttk.Window, asset: Optional[Asset] = None):
        """
        Initialize dialog.

        Args:
            parent: Parent window
            asset: Asset to edit (None for new asset)
        """
        self.parent = parent
        self.asset = asset
        self.result: Optional[Asset] = None
        self.is_edit = asset is not None

        # Create dialog
        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("Modifier l'actif" if self.is_edit else "Nouvel actif")
        self.dialog.resizable(False, False)

        # Make modal
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center
        self._center_dialog(500, 600)

        # Build UI
        self._build_ui()

        # Fill data if editing
        if self.is_edit:
            self._fill_data()

    def _center_dialog(self, width: int, height: int) -> None:
        """Center dialog on parent."""
        self.dialog.geometry(f"{width}x{height}")
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (width // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (height // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def _build_ui(self) -> None:
        """Build dialog UI."""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)

        # Form fields
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=BOTH, expand=True)

        self._fields = {}

        # Name
        self._create_field(form_frame, "name", "Nom *", "entry")

        # Type
        self._create_field(
            form_frame, "type", "Type *", "combobox",
            values=[t.value for t in AssetType]
        )

        # IP Address
        self._create_field(form_frame, "ip_address", "Adresse IP", "entry")

        # MAC Address
        self._create_field(form_frame, "mac_address", "Adresse MAC", "entry")

        # Hostname
        self._create_field(form_frame, "hostname", "Hostname", "entry")

        # OS
        self._create_field(form_frame, "os", "Système d'exploitation", "entry")

        # OS Version
        self._create_field(form_frame, "os_version", "Version OS", "entry")

        # Location
        self._create_field(form_frame, "location", "Localisation", "entry")

        # Department
        self._create_field(form_frame, "department", "Département", "entry")

        # Owner
        self._create_field(form_frame, "owner", "Propriétaire", "entry")

        # Criticality
        self._create_field(
            form_frame, "criticality", "Criticité", "combobox",
            values=[c.value for c in Criticality]
        )

        # Status
        self._create_field(
            form_frame, "status", "Statut", "combobox",
            values=[s.value for s in AssetStatus]
        )

        # Notes
        notes_frame = ttk.Frame(form_frame)
        notes_frame.pack(fill=X, pady=5)
        ttk.Label(notes_frame, text="Notes:", width=15, anchor=W).pack(side=LEFT, anchor=N)
        self._notes = ttk.Text(notes_frame, height=3, width=40)
        self._notes.pack(side=LEFT, fill=X, expand=True)

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=X, pady=(20, 0))

        ttk.Button(
            btn_frame,
            text="Annuler",
            bootstyle="secondary-outline",
            command=self._cancel,
        ).pack(side=RIGHT, padx=(10, 0))

        ttk.Button(
            btn_frame,
            text="Enregistrer",
            bootstyle="success",
            command=self._save,
        ).pack(side=RIGHT)

    def _create_field(
        self,
        parent: ttk.Frame,
        key: str,
        label: str,
        field_type: str,
        values: Optional[list] = None
    ) -> None:
        """Create a form field."""
        frame = ttk.Frame(parent)
        frame.pack(fill=X, pady=5)

        ttk.Label(frame, text=label, width=15, anchor=W).pack(side=LEFT)

        if field_type == "entry":
            widget = ttk.Entry(frame, width=40)
        elif field_type == "combobox":
            widget = ttk.Combobox(frame, values=values or [], state="readonly", width=37)
        else:
            widget = ttk.Entry(frame, width=40)

        widget.pack(side=LEFT, fill=X, expand=True)
        self._fields[key] = widget

    def _fill_data(self) -> None:
        """Fill form with asset data."""
        if not self.asset:
            return

        self._fields["name"].insert(0, self.asset.name or "")
        self._fields["type"].set(self.asset.asset_type.value if self.asset.asset_type else "")
        self._fields["ip_address"].insert(0, self.asset.ip_address or "")
        self._fields["mac_address"].insert(0, self.asset.mac_address or "")
        self._fields["hostname"].insert(0, self.asset.hostname or "")
        self._fields["os"].insert(0, self.asset.os or "")
        self._fields["os_version"].insert(0, self.asset.os_version or "")
        self._fields["location"].insert(0, self.asset.location or "")
        self._fields["department"].insert(0, self.asset.department or "")
        self._fields["owner"].insert(0, self.asset.owner or "")
        self._fields["criticality"].set(
            self.asset.criticality.value if self.asset.criticality else ""
        )
        self._fields["status"].set(self.asset.status.value if self.asset.status else "")
        self._notes.insert("1.0", self.asset.notes or "")

    def _validate(self) -> bool:
        """Validate form data."""
        name = self._fields["name"].get().strip()
        if not name:
            Messagebox.show_warning(
                "Le nom est obligatoire.",
                "Validation",
                parent=self.dialog
            )
            return False

        asset_type = self._fields["type"].get()
        if not asset_type:
            Messagebox.show_warning(
                "Le type est obligatoire.",
                "Validation",
                parent=self.dialog
            )
            return False

        return True

    def _save(self) -> None:
        """Save asset."""
        if not self._validate():
            return

        # Check permission
        auth = get_auth_service()
        required_perm = Permission.ASSET_EDIT if self.is_edit else Permission.ASSET_CREATE
        if not auth.get_context().has_permission(required_perm):
            Messagebox.show_error(
                "Vous n'avez pas la permission d'effectuer cette action.",
                "Permission refusée",
                parent=self.dialog
            )
            return

        db = get_db()

        with db.get_session() as session:
            repo = AssetRepository(session)

            if self.is_edit:
                asset = repo.get_by_id(self.asset.id)
            else:
                asset = Asset()

            # Update fields
            asset.name = self._fields["name"].get().strip()
            asset.asset_type = AssetType(self._fields["type"].get())
            asset.ip_address = self._fields["ip_address"].get().strip() or None
            asset.mac_address = self._fields["mac_address"].get().strip() or None
            asset.hostname = self._fields["hostname"].get().strip() or None
            asset.os = self._fields["os"].get().strip() or None
            asset.os_version = self._fields["os_version"].get().strip() or None
            asset.location = self._fields["location"].get().strip() or None
            asset.department = self._fields["department"].get().strip() or None
            asset.owner = self._fields["owner"].get().strip() or None

            criticality = self._fields["criticality"].get()
            asset.criticality = Criticality(criticality) if criticality else Criticality.MEDIUM

            status = self._fields["status"].get()
            asset.status = AssetStatus(status) if status else AssetStatus.ACTIVE

            asset.notes = self._notes.get("1.0", END).strip() or None

            if self.is_edit:
                repo.update(asset)
            else:
                repo.add(asset)

            self.result = asset

        self.dialog.destroy()

    def _cancel(self) -> None:
        """Cancel dialog."""
        self.result = None
        self.dialog.destroy()
