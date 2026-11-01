"""Reusable CustomTkinter widgets and application screens."""

from tkinter import END, messagebox, ttk
from typing import Callable

import customtkinter as ctk

from database import DatabaseError, DatabaseManager


class DataTable(ctk.CTkFrame):
    """A themed Treeview that displays database rows."""

    def __init__(self, master: ctk.CTkBaseClass, **kwargs: object) -> None:
        super().__init__(master, **kwargs)
        self.tree = ttk.Treeview(self, show="headings")
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def set_rows(self, columns: list[str], rows: list[tuple[object, ...]]) -> None:
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = columns
        for column in columns:
            self.tree.heading(column, text=column.replace("_", " ").title())
            self.tree.column(column, width=125, minwidth=80, anchor="w")
        for row in rows:
            self.tree.insert("", END, values=[str(value) if value is not None else "" for value in row])

    def selected_values(self) -> tuple[str, ...] | None:
        selected = self.tree.selection()
        if not selected:
            return None
        return tuple(str(value) for value in self.tree.item(selected[0], "values"))


class BaseScreen(ctk.CTkFrame):
    """Base class for dashboard content screens."""

    def __init__(self, master: ctk.CTkBaseClass, db: DatabaseManager, title: str) -> None:
        super().__init__(master, fg_color="transparent")
        self.db = db
        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=25, weight="bold")).pack(
            anchor="w", padx=24, pady=(20, 12)
        )

    def error(self, exc: Exception) -> None:
        messagebox.showerror("AutoLease Peru", str(exc), parent=self)

    def info(self, message: str) -> None:
        messagebox.showinfo("AutoLease Peru", message, parent=self)


class LoginScreen(ctk.CTkFrame):
    """Initial authentication screen."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        db: DatabaseManager,
        on_login: Callable[[], None],
        on_exit: Callable[[], None],
    ) -> None:
        super().__init__(master, fg_color="#111827")
        self.db, self.on_login, self.on_exit = db, on_login, on_exit
        self.windows_auth = ctk.BooleanVar(value=False)
        card = ctk.CTkFrame(self, width=410, height=390, corner_radius=18)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.grid_propagate(False)
        ctk.CTkLabel(card, text="AutoLease Peru", font=ctk.CTkFont(size=30, weight="bold")).pack(
            pady=(42, 4)
        )
        ctk.CTkLabel(card, text="Acceso al sistema de leasing vehicular", text_color="#9ca3af").pack(
            pady=(0, 25)
        )
        self.username = ctk.CTkEntry(card, width=300, placeholder_text="Usuario SQL Server")
        self.username.pack(pady=8)
        self.password = ctk.CTkEntry(card, width=300, placeholder_text="Contraseña", show="*")
        self.password.pack(pady=8)
        ctk.CTkCheckBox(
            card,
            text="Usar Windows Authentication",
            variable=self.windows_auth,
            command=self._toggle_credentials,
        ).pack(pady=(4, 2))
        self.password.bind("<Return>", lambda _event: self.login())
        ctk.CTkButton(card, text="Iniciar sesión", width=300, command=self.login).pack(pady=(20, 8))
        ctk.CTkButton(
            card, text="Salir", width=300, fg_color="transparent",
            border_width=1, command=self.on_exit
        ).pack()

    def _toggle_credentials(self) -> None:
        state = "disabled" if self.windows_auth.get() else "normal"
        self.username.configure(state=state)
        self.password.configure(state=state)

    def login(self) -> None:
        try:
            if self.windows_auth.get():
                self.db.use_windows_session()
            else:
                self.db.authenticate(self.username.get().strip(), self.password.get())
        except DatabaseError as exc:
            self.error(exc)
            return
        self.on_login()

    def error(self, exc: Exception) -> None:
        messagebox.showerror("Inicio de sesión", str(exc), parent=self)


class ClientScreen(BaseScreen):
    """CRUD screen using dbo.cliente."""

    def __init__(self, master: ctk.CTkBaseClass, db: DatabaseManager) -> None:
        super().__init__(master, db, "Gestión de clientes")
        self.selected_id: int | None = None
        self.entries: dict[str, ctk.CTkEntry] = {}
        self._build_form()
        self.table = DataTable(self)
        self.table.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        self.table.tree.bind("<<TreeviewSelect>>", self._select_row)
        self.refresh()

    def _build_form(self) -> None:
        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=24, pady=(0, 12))
        fields = [
            ("dni", "DNI"), ("nombre", "Nombre"), ("email", "Email"),
            ("telefono", "Teléfono"), ("direccion", "Dirección"),
            ("tipo_canal", "Tipo Canal"),
        ]
        for index, (key, label) in enumerate(fields):
            ctk.CTkLabel(form, text=label).grid(row=index // 3 * 2, column=index % 3, padx=10, pady=(10, 2), sticky="w")
            entry = ctk.CTkEntry(form, width=190)
            entry.grid(row=index // 3 * 2 + 1, column=index % 3, padx=10, pady=(0, 8))
            self.entries[key] = entry
        buttons = ctk.CTkFrame(form, fg_color="transparent")
        buttons.grid(row=4, column=0, columnspan=3, pady=8)
        for text, command in [
            ("Nuevo", self.new_record), ("Guardar", self.save),
            ("Actualizar", self.update), ("Eliminar", self.delete),
            ("Buscar", self.search), ("Mostrar todos", self.show_all),
        ]:
            ctk.CTkButton(buttons, text=text, width=110, command=command).pack(side="left", padx=4)

    def new_record(self) -> None:
        self.selected_id = None
        for entry in self.entries.values():
            entry.delete(0, END)

    def values(self) -> tuple[str, ...]:
        return tuple(entry.get().strip() for entry in self.entries.values())

    def _validate_values(self, values: tuple[str, ...]) -> bool:
        required = {
            "DNI": values[0],
            "Nombre": values[1],
            "Tipo Canal": values[5],
        }
        missing = [label for label, value in required.items() if not value]
        if missing:
            self.info(f"Complete los campos obligatorios: {', '.join(missing)}.")
            return False
        return True

    def save(self) -> None:
        values = self.values()
        if not self._validate_values(values):
            return
        try:
            self.db.insert(
                """INSERT INTO dbo.cliente
                   (dni,nombre,email,telefono,direccion,tipo_canal,fecha_registro)
                   VALUES (?,?,?,?,?,?,CAST(GETDATE() AS date))""", values
            )
            self.refresh()
            self.new_record()
        except DatabaseError as exc:
            self.error(exc)

    def update(self) -> None:
        if self.selected_id is None:
            self.info("Seleccione un cliente en la tabla.")
            return
        values = self.values()
        if not self._validate_values(values):
            return
        try:
            self.db.update(
                """UPDATE dbo.cliente SET dni=?,nombre=?,email=?,telefono=?,
                   direccion=?,tipo_canal=? WHERE cliente_id=?""",
                values + (self.selected_id,),
            )
            self.refresh()
        except DatabaseError as exc:
            self.error(exc)

    def delete(self) -> None:
        if self.selected_id is None:
            self.info("Seleccione un cliente en la tabla.")
            return
        if not messagebox.askyesno("Confirmar", "¿Eliminar el cliente seleccionado?", parent=self):
            return
        try:
            self.db.update(
                "UPDATE dbo.cliente SET conyuge_id=NULL WHERE conyuge_id=?",
                (self.selected_id,),
            )
            _, contracts = self.db.select(
                "SELECT contrato_id FROM dbo.contrato_leasing WHERE cliente_id=?",
                (self.selected_id,),
            )
            if contracts:
                self.info("No se puede eliminar el cliente porque tiene contratos asociados.")
                return
            self.db.delete("DELETE FROM dbo.cliente WHERE cliente_id=?", (self.selected_id,))
            self.refresh()
            self.new_record()
        except DatabaseError as exc:
            self.error(exc)

    def refresh(self) -> None:
        try:
            columns, rows = self.db.select(
                """SELECT cliente_id,dni,nombre,email,telefono,direccion,tipo_canal,
                          fecha_registro
                   FROM dbo.cliente ORDER BY cliente_id"""
            )
            self.table.set_rows(columns, rows)
        except DatabaseError as exc:
            self.error(exc)

    def search(self) -> None:
        filter_fields = (
            ("dni", "DNI"),
            ("nombre", "Nombre"),
            ("email", "Email"),
            ("telefono", "Telefono"),
            ("direccion", "Direccion"),
            ("tipo_canal", "Tipo Canal"),
        )
        values = self.values()
        conditions = []
        parameters: list[str] = []
        for (column, _label), value in zip(filter_fields, values):
            if value:
                conditions.append(f"{column} LIKE ?")
                parameters.append(f"%{value}%")

        query = """SELECT cliente_id,dni,nombre,email,telefono,direccion,tipo_canal,
                          fecha_registro
                   FROM dbo.cliente"""
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY cliente_id"

        try:
            columns, rows = self.db.select(query, parameters)
            self.table.set_rows(columns, rows)
            if not rows:
                self.info("No se encontraron clientes.")
        except DatabaseError as exc:
            self.error(exc)

    def show_all(self) -> None:
        self.new_record()
        self.refresh()

    def _select_row(self, _event: object) -> None:
        values = self.table.selected_values()
        if not values:
            return
        self.selected_id = int(values[0])
        for entry, value in zip(self.entries.values(), values[1:]):
            entry.delete(0, END)
            entry.insert(0, value)


class VehicleScreen(BaseScreen):
    """CRUD screen using dbo.vehiculo."""

    def __init__(self, master: ctk.CTkBaseClass, db: DatabaseManager) -> None:
        super().__init__(master, db, "Gestión de vehículos")
        self.selected_id: int | None = None
        self.entries: dict[str, ctk.CTkEntry] = {}
        self._build_form()
        self.table = DataTable(self)
        self.table.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        self.table.tree.bind("<<TreeviewSelect>>", self._select_row)
        self.refresh()

    def _build_form(self) -> None:
        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=24, pady=(0, 12))
        fields = [("marca", "Marca"), ("modelo", "Modelo"), ("anio", "Año"),
                  ("precio", "Precio"), ("color", "Color"), ("kilometraje_actual", "Kilometraje Actual")]
        for index, (key, label) in enumerate(fields):
            ctk.CTkLabel(form, text=label).grid(row=index // 3 * 2, column=index % 3, padx=10, pady=(10, 2), sticky="w")
            entry = ctk.CTkEntry(form, width=190)
            entry.grid(row=index // 3 * 2 + 1, column=index % 3, padx=10, pady=(0, 8))
            self.entries[key] = entry
        buttons = ctk.CTkFrame(form, fg_color="transparent")
        buttons.grid(row=4, column=0, columnspan=3, pady=8)
        for text, command in [("Nuevo", self.new_record), ("Guardar", self.save),
                              ("Actualizar", self.update), ("Eliminar", self.delete),
                              ("Buscar", self.search), ("Mostrar todos", self.show_all)]:
            ctk.CTkButton(buttons, text=text, width=110, command=command).pack(side="left", padx=4)

    def new_record(self) -> None:
        self.selected_id = None
        for entry in self.entries.values():
            entry.delete(0, END)

    def values(self) -> tuple[str, ...]:
        return tuple(entry.get().strip() for entry in self.entries.values())

    def save(self) -> None:
        try:
            self.db.insert(
                """INSERT INTO dbo.vehiculo
                   (marca,modelo,anio,precio,color,kilometraje_actual)
                   VALUES (?,?,?,?,?,?)""", self.values()
            )
            self.refresh()
            self.new_record()
        except DatabaseError as exc:
            self.error(exc)

    def update(self) -> None:
        if self.selected_id is None:
            self.info("Seleccione un vehículo en la tabla.")
            return
        try:
            self.db.update(
                """UPDATE dbo.vehiculo SET marca=?,modelo=?,anio=?,precio=?,color=?,
                   kilometraje_actual=? WHERE vehiculo_id=?""",
                self.values() + (self.selected_id,),
            )
            self.refresh()
        except DatabaseError as exc:
            self.error(exc)

    def delete(self) -> None:
        if self.selected_id is None:
            self.info("Seleccione un vehículo en la tabla.")
            return
        if not messagebox.askyesno("Confirmar", "¿Eliminar el vehículo seleccionado?", parent=self):
            return
        try:
            _, contracts = self.db.select(
                "SELECT COUNT(*) FROM dbo.contrato_leasing WHERE vehiculo_id=?",
                (self.selected_id,),
            )
            if contracts and contracts[0][0] > 0:
                self.info("No se puede eliminar el vehículo porque tiene contratos asociados.")
                return
            self.db.delete("DELETE FROM dbo.vehiculo WHERE vehiculo_id=?", (self.selected_id,))
            self.refresh()
            self.new_record()
        except DatabaseError as exc:
            self.error(exc)

    def refresh(self) -> None:
        try:
            columns, rows = self.db.select(
                """SELECT vehiculo_id,marca,modelo,anio,precio,color,kilometraje_actual
                   FROM dbo.vehiculo ORDER BY vehiculo_id"""
            )
            self.table.set_rows(columns, rows)
        except DatabaseError as exc:
            self.error(exc)

    def search(self) -> None:
        filter_fields = (
            ("marca", "Marca"),
            ("modelo", "Modelo"),
            ("anio", "Año"),
            ("precio", "Precio"),
            ("color", "Color"),
            ("kilometraje_actual", "Kilometraje Actual"),
        )
        values = self.values()
        conditions = []
        parameters: list[str] = []
        for (column, _label), value in zip(filter_fields, values):
            if value:
                searchable_column = (
                    f"CAST({column} AS VARCHAR(50))"
                    if column in {"anio", "precio", "kilometraje_actual"}
                    else column
                )
                conditions.append(f"{searchable_column} LIKE ?")
                parameters.append(f"%{value}%")

        query = """SELECT vehiculo_id,marca,modelo,anio,precio,color,kilometraje_actual
                   FROM dbo.vehiculo"""
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY vehiculo_id"

        try:
            columns, rows = self.db.select(query, parameters)
            self.table.set_rows(columns, rows)
            if not rows:
                self.info("No se encontraron vehículos.")
        except DatabaseError as exc:
            self.error(exc)

    def show_all(self) -> None:
        self.new_record()
        self.refresh()


    def _select_row(self, _event: object) -> None:
        values = self.table.selected_values()
        if not values:
            return
        self.selected_id = int(values[0])
        for entry, value in zip(self.entries.values(), values[1:]):
            entry.delete(0, END)
            entry.insert(0, value)


class ContractScreen(BaseScreen):
    """Contract management using cliente, vehiculo and empleado."""

    def __init__(self, master: ctk.CTkBaseClass, db: DatabaseManager) -> None:
        super().__init__(master, db, "Gestión de contratos de leasing")
        self.selected_id: int | None = None
        self.combos: dict[str, ctk.CTkComboBox] = {}
        self.entries: dict[str, ctk.CTkEntry] = {}
        self.lookup_ids: dict[str, dict[str, int]] = {}
        self._build_form()
        self.table = DataTable(self)
        self.table.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        self.table.tree.bind("<<TreeviewSelect>>", self._select_row)
        self.refresh()

    def _build_form(self) -> None:
        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=24, pady=(0, 12))
        for index, (key, label, query) in enumerate([
            ("cliente", "Cliente", "SELECT cliente_id,nombre FROM dbo.cliente ORDER BY nombre"),
            ("vehiculo", "Vehículo", "SELECT vehiculo_id,CONCAT(marca,' ',modelo) FROM dbo.vehiculo ORDER BY marca,modelo"),
            ("empleado", "Empleado", "SELECT empleado_id,nombre FROM dbo.empleado ORDER BY nombre"),
        ]):
            ctk.CTkLabel(form, text=label).grid(row=0, column=index, padx=10, pady=(10, 2), sticky="w")
            combo = ctk.CTkComboBox(form, width=190, values=[])
            combo.grid(row=1, column=index, padx=10, pady=(0, 8))
            self.combos[key] = combo
            self.lookup_ids[key] = {}
            self._load_combo(key, query)
        for index, (key, label) in enumerate([
            ("fecha_inicio", "Fecha Inicio"), ("fecha_fin", "Fecha Fin"),
            ("cuota_mensual", "Cuota Mensual"), ("kilometraje_permitido", "Km Permitido"),
        ]):
            ctk.CTkLabel(form, text=label).grid(row=2, column=index, padx=10, pady=(5, 2), sticky="w")
            entry = ctk.CTkEntry(form, width=190)
            entry.grid(row=3, column=index, padx=10, pady=(0, 8))
            self.entries[key] = entry
        buttons = ctk.CTkFrame(form, fg_color="transparent")
        buttons.grid(row=4, column=0, columnspan=4, pady=8)
        for text, command in [("Crear Contrato", self.save), ("Actualizar", self.update),
                              ("Eliminar", self.delete), ("Buscar", self.refresh)]:
            ctk.CTkButton(buttons, text=text, width=135, command=command).pack(side="left", padx=4)

    def _load_combo(self, key: str, query: str) -> None:
        try:
            _, rows = self.db.select(query)
            self.lookup_ids[key] = {str(row[1]): int(row[0]) for row in rows}
            self.combos[key].configure(values=list(self.lookup_ids[key]))
        except DatabaseError as exc:
            self.error(exc)

    def _selected_id(self, key: str) -> int:
        value = self.lookup_ids[key].get(self.combos[key].get())
        if value is None:
            raise ValueError(f"Seleccione un {key}.")
        return value

    def save(self) -> None:
        try:
            self.db.insert(
                """INSERT INTO dbo.contrato_leasing
                   (cliente_id,vehiculo_id,empleado_id,fecha_inicio,fecha_fin,
                    cuota_mensual,kilometraje_permitido) VALUES (?,?,?,?,?,?,?)""",
                (self._selected_id("cliente"), self._selected_id("vehiculo"),
                 self._selected_id("empleado"), *(entry.get().strip() for entry in self.entries.values())),
            )
            self.refresh()
        except (DatabaseError, ValueError) as exc:
            self.error(exc)

    def update(self) -> None:
        if self.selected_id is None:
            self.info("Seleccione un contrato en la tabla.")
            return
        try:
            self.db.update(
                """UPDATE dbo.contrato_leasing SET cliente_id=?,vehiculo_id=?,empleado_id=?,
                   fecha_inicio=?,fecha_fin=?,cuota_mensual=?,kilometraje_permitido=?
                   WHERE contrato_id=?""",
                (self._selected_id("cliente"), self._selected_id("vehiculo"),
                 self._selected_id("empleado"), *(entry.get().strip() for entry in self.entries.values()),
                 self.selected_id),
            )
            self.refresh()
        except (DatabaseError, ValueError) as exc:
            self.error(exc)

    def delete(self) -> None:
        if self.selected_id is None:
            self.info("Seleccione un contrato en la tabla.")
            return
        try:
            self.db.delete("DELETE FROM dbo.contrato_leasing WHERE contrato_id=?", (self.selected_id,))
            self.refresh()
        except DatabaseError as exc:
            self.error(exc)

    def refresh(self) -> None:
        try:
            columns, rows = self.db.select(
                """SELECT c.contrato_id,cl.nombre AS cliente,
                   CONCAT(v.marca,' ',v.modelo) AS vehiculo,e.nombre AS empleado,
                   c.fecha_inicio,c.fecha_fin,c.cuota_mensual,c.kilometraje_permitido
                   FROM dbo.contrato_leasing c
                   JOIN dbo.cliente cl ON cl.cliente_id=c.cliente_id
                   JOIN dbo.vehiculo v ON v.vehiculo_id=c.vehiculo_id
                   JOIN dbo.empleado e ON e.empleado_id=c.empleado_id
                   ORDER BY c.contrato_id"""
            )
            self.table.set_rows(columns, rows)
        except DatabaseError as exc:
            self.error(exc)

    def _select_row(self, _event: object) -> None:
        values = self.table.selected_values()
        if not values:
            return
        self.selected_id = int(values[0])
        for key, value in [("cliente", values[1]), ("vehiculo", values[2]), ("empleado", values[3])]:
            self.combos[key].set(value)
        for entry, value in zip(self.entries.values(), values[4:]):
            entry.delete(0, END)
            entry.insert(0, value)


class PaymentScreen(BaseScreen):
    """Payment management using dbo.pago and dbo.contrato_leasing."""

    def __init__(self, master: ctk.CTkBaseClass, db: DatabaseManager) -> None:
        super().__init__(master, db, "Gestión de pagos")
        self.selected_id: int | None = None
        self.contract_ids: dict[str, int] = {}
        self.contract_combo: ctk.CTkComboBox
        self.entries: dict[str, ctk.CTkEntry] = {}
        self._build_form()
        self.table = DataTable(self)
        self.table.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        self.table.tree.bind("<<TreeviewSelect>>", self._select_row)
        self.refresh()

    def _build_form(self) -> None:
        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=24, pady=(0, 12))
        ctk.CTkLabel(form, text="Contrato").grid(row=0, column=0, padx=10, pady=(10, 2), sticky="w")
        self.contract_combo = ctk.CTkComboBox(form, width=190, values=[])
        self.contract_combo.grid(row=1, column=0, padx=10, pady=(0, 8))
        self._load_contracts()
        fields = [("monto", "Monto"), ("fecha_pago", "Fecha Pago"), ("metodo_pago", "Método Pago"), ("estado", "Estado")]
        for index, (key, label) in enumerate(fields, start=1):
            ctk.CTkLabel(form, text=label).grid(row=0, column=index, padx=10, pady=(10, 2), sticky="w")
            entry = ctk.CTkEntry(form, width=160)
            entry.grid(row=1, column=index, padx=10, pady=(0, 8))
            self.entries[key] = entry
        buttons = ctk.CTkFrame(form, fg_color="transparent")
        buttons.grid(row=2, column=0, columnspan=5, pady=8)
        for text, command in [("Registrar Pago", self.save), ("Actualizar", self.update),
                              ("Eliminar", self.delete), ("Buscar", self.refresh)]:
            ctk.CTkButton(buttons, text=text, width=135, command=command).pack(side="left", padx=4)

    def _load_contracts(self) -> None:
        try:
            _, rows = self.db.select(
                """SELECT c.contrato_id, CONCAT(c.contrato_id,' - ',cl.nombre)
                   FROM dbo.contrato_leasing c JOIN dbo.cliente cl ON cl.cliente_id=c.cliente_id"""
            )
            self.contract_ids = {str(row[1]): int(row[0]) for row in rows}
            self.contract_combo.configure(values=list(self.contract_ids))
        except DatabaseError as exc:
            self.error(exc)

    def _contract_id(self) -> int:
        value = self.contract_ids.get(self.contract_combo.get())
        if value is None:
            raise ValueError("Seleccione un contrato.")
        return value

    def save(self) -> None:
        try:
            self.db.insert(
                """INSERT INTO dbo.pago (contrato_id,monto,fecha_pago,metodo_pago,estado)
                   VALUES (?,?,?,?,?)""",
                (self._contract_id(), *(entry.get().strip() for entry in self.entries.values())),
            )
            self.refresh()
        except (DatabaseError, ValueError) as exc:
            self.error(exc)

    def update(self) -> None:
        if self.selected_id is None:
            self.info("Seleccione un pago en la tabla.")
            return
        try:
            self.db.update(
                """UPDATE dbo.pago SET contrato_id=?,monto=?,fecha_pago=?,metodo_pago=?,estado=?
                   WHERE pago_id=?""",
                (self._contract_id(), *(entry.get().strip() for entry in self.entries.values()), self.selected_id),
            )
            self.refresh()
        except (DatabaseError, ValueError) as exc:
            self.error(exc)

    def delete(self) -> None:
        if self.selected_id is None:
            self.info("Seleccione un pago en la tabla.")
            return
        try:
            self.db.delete("DELETE FROM dbo.pago WHERE pago_id=?", (self.selected_id,))
            self.refresh()
        except DatabaseError as exc:
            self.error(exc)

    def refresh(self) -> None:
        try:
            columns, rows = self.db.select(
                """SELECT p.pago_id,p.contrato_id,cl.nombre AS cliente,p.monto,
                   p.fecha_pago,p.metodo_pago,p.estado
                   FROM dbo.pago p JOIN dbo.contrato_leasing c ON c.contrato_id=p.contrato_id
                   JOIN dbo.cliente cl ON cl.cliente_id=c.cliente_id ORDER BY p.fecha_pago DESC"""
            )
            self.table.set_rows(columns, rows)
        except DatabaseError as exc:
            self.error(exc)

    def _select_row(self, _event: object) -> None:
        values = self.table.selected_values()
        if not values:
            return
        self.selected_id = int(values[0])
        contract = next((name for name, value in self.contract_ids.items() if str(value) == values[1]), "")
        self.contract_combo.set(contract)
        for entry, value in zip(self.entries.values(), values[3:]):
            entry.delete(0, END)
            entry.insert(0, value)


class MaintenanceScreen(BaseScreen):
    """Read-only maintenance screen using dbo.mantenimiento and dbo.proveedor."""

    def __init__(self, master: ctk.CTkBaseClass, db: DatabaseManager) -> None:
        super().__init__(master, db, "Mantenimientos")
        ctk.CTkButton(self, text="Actualizar", width=120, command=self.refresh).pack(
            anchor="w", padx=24, pady=(0, 12)
        )
        self.table = DataTable(self)
        self.table.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        self.refresh()

    def refresh(self) -> None:
        try:
            columns, rows = self.db.select(
                """SELECT m.mantenimiento_id,CONCAT(v.marca,' ',v.modelo) AS vehiculo,
                   pr.nombre_empresa AS proveedor,m.tipo_servicio,m.fecha,m.costo,m.estado
                   FROM dbo.mantenimiento m JOIN dbo.vehiculo v ON v.vehiculo_id=m.vehiculo_id
                   JOIN dbo.proveedor pr ON pr.proveedor_id=m.proveedor_id ORDER BY m.fecha DESC"""
            )
            self.table.set_rows(columns, rows)
        except DatabaseError as exc:
            self.error(exc)


class ReportsScreen(BaseScreen):
    """Displays the four reporting views created in the SQL script."""

    def __init__(self, master: ctk.CTkBaseClass, db: DatabaseManager) -> None:
        super().__init__(master, db, "Reportes")
        self.view_name = ctk.StringVar(value="vw_clientes_contratos")
        self.selector = ctk.CTkComboBox(
            self, width=260, variable=self.view_name,
            values=["vw_clientes_contratos", "vw_vehiculos_seguros",
                    "vw_historial_mantenimiento", "vw_resumen_pagos"],
            command=lambda _value: self.refresh(),
        )
        self.selector.pack(anchor="w", padx=24, pady=(0, 12))
        ctk.CTkButton(self, text="Actualizar reporte", width=150, command=self.refresh).pack(
            anchor="w", padx=24, pady=(0, 12)
        )
        self.table = DataTable(self)
        self.table.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        self.refresh()

    def refresh(self) -> None:
        try:
            columns, rows = self.db.select(
                f"SELECT * FROM dbo.{self.view_name.get()}"
            )
            self.table.set_rows(columns, rows)
        except DatabaseError as exc:
            self.error(exc)
