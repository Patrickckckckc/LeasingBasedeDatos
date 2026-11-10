"""Reusable CustomTkinter widgets and application screens."""

import csv
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from tkinter import END, filedialog, messagebox, ttk
from typing import Callable

import customtkinter as ctk

from database import DatabaseError, DatabaseManager
from maintenance_schedule import quarterly_dates
from payment_schedule import Contract, Payment, PaymentRow, build_payment_rows, paid_total


class DataTable(ctk.CTkFrame):
    """A themed Treeview that displays database rows with dynamic column sizing and scrollbars."""

    def __init__(self, master: ctk.CTkBaseClass, **kwargs: object) -> None:
        super().__init__(master, **kwargs)
        self.tree = ttk.Treeview(self, show="headings", selectmode="browse")
        v_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    @staticmethod
    def _column_alignment(column_name: str) -> str:
        col = column_name.lower()
        if any(term in col for term in ("monto", "precio", "costo", "cuota", "total", "cantidad", "kilometraje", "salario", "saldo")):
            return "e"
        if any(col == term or col.endswith(f"_{term}") for term in ("id", "dni", "ruc", "anio", "estado")):
            return "center"
        if "fecha" in col or "estado" in col:
            return "center"
        return "w"

    def set_rows(self, columns: list[str], rows: list[tuple[object, ...]]) -> None:
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = columns

        for idx, column in enumerate(columns):
            header_text = column.replace("_", " ").title()

            max_char_len = len(header_text)
            for row in rows[:150]:
                if idx < len(row) and row[idx] is not None:
                    max_char_len = max(max_char_len, len(str(row[idx])))

            calc_width = max(max_char_len * 9 + 28, 90)
            calc_width = min(calc_width, 360)

            align = self._column_alignment(column)
            self.tree.heading(
                column,
                text=header_text,
                command=lambda c=column: self._sort_by_column(c, False),
            )
            self.tree.column(column, width=calc_width, minwidth=75, anchor=align)

        for row in rows:
            formatted_row = [
                "-" if value is None or str(value).strip() == "" else str(value)
                for value in row
            ]
            self.tree.insert("", END, values=formatted_row)

    def _sort_by_column(self, col: str, reverse: bool) -> None:
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]

        def _sort_key(item: tuple[str, str]) -> tuple[int, object]:
            val = item[0]
            cleaned = val.replace("S/", "").replace("$", "").replace(",", "").strip()
            try:
                return (0, float(cleaned))
            except ValueError:
                return (1, val.lower())

        items.sort(key=_sort_key, reverse=reverse)

        for index, (_val, k) in enumerate(items):
            self.tree.move(k, "", index)

        self.tree.heading(col, command=lambda: self._sort_by_column(col, not reverse))

    def selected_values(self) -> tuple[str, ...] | None:
        selected = self.tree.selection()
        if not selected:
            return None
        return tuple("" if str(value) == "-" else str(value) for value in self.tree.item(selected[0], "values"))


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
        self.status_combo: ctk.CTkComboBox
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
            row = (index // 3) * 2
            col = index % 3
            ctk.CTkLabel(form, text=label).grid(row=row, column=col, padx=10, pady=(10, 2), sticky="w")
            entry = ctk.CTkEntry(form, width=190)
            entry.grid(row=row + 1, column=col, padx=10, pady=(0, 8))
            self.entries[key] = entry
        ctk.CTkLabel(form, text="Estado").grid(row=0, column=3, padx=10, pady=(10, 2), sticky="w")
        self.status_combo = ctk.CTkComboBox(form, width=190, values=["Disponible", "Ocupado", "Arrendado"])
        self.status_combo.grid(row=1, column=3, padx=10, pady=(0, 8))
        self.status_combo.set("Disponible")
        buttons = ctk.CTkFrame(form, fg_color="transparent")
        buttons.grid(row=4, column=0, columnspan=4, pady=8)
        for text, command in [("Nuevo", self.new_record), ("Guardar", self.save),
                              ("Actualizar", self.update), ("Eliminar", self.delete),
                              ("Buscar", self.search), ("Mostrar todos", self.show_all)]:
            ctk.CTkButton(buttons, text=text, width=110, command=command).pack(side="left", padx=4)

    def new_record(self) -> None:
        self.selected_id = None
        for entry in self.entries.values():
            entry.delete(0, END)
        self.status_combo.set("Disponible")

    def values(self) -> tuple[str, ...]:
        return tuple(entry.get().strip() for entry in self.entries.values()) + (
            self.status_combo.get().strip() or "Disponible",
        )

    def save(self) -> None:
        try:
            self.db.insert(
                """INSERT INTO dbo.vehiculo
                   (marca,modelo,anio,precio,color,kilometraje_actual,estado)
                   VALUES (?,?,?,?,?,?,?)""", self.values()
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
                   kilometraje_actual=?,estado=? WHERE vehiculo_id=?""",
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
                """SELECT vehiculo_id,marca,modelo,anio,precio,color,kilometraje_actual,estado
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
        values = tuple(entry.get().strip() for entry in self.entries.values())
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

        status_value = self.status_combo.get().strip()
        if status_value:
            conditions.append("estado LIKE ?")
            parameters.append(f"%{status_value}%")

        query = """SELECT vehiculo_id,marca,modelo,anio,precio,color,kilometraje_actual,estado
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
        self.status_combo.set("")
        self.refresh()


    def _select_row(self, _event: object) -> None:
        values = self.table.selected_values()
        if not values:
            return
        self.selected_id = int(values[0])
        for entry, value in zip(self.entries.values(), values[1:7]):
            entry.delete(0, END)
            entry.insert(0, value)
        if len(values) > 7:
            self.status_combo.set(values[7])


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
                              ("Eliminar", self.delete), ("Buscar", self.search),
                              ("Mostrar Todos", self.show_all)]:
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
            _, payments = self.db.select(
                "SELECT COUNT(*) FROM dbo.pago WHERE contrato_id=?",
                (self.selected_id,),
            )
            if payments and payments[0][0] > 0:
                self.info("No se puede eliminar el contrato porque tiene pagos asociados.")
                return

            _, registrations = self.db.select(
                "SELECT COUNT(*) FROM dbo.matricula WHERE contrato_id=?",
                (self.selected_id,),
            )
            if registrations and registrations[0][0] > 0:
                self.info("No se puede eliminar el contrato porque tiene una matrícula asociada.")
                return

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

    def search(self) -> None:
        filter_values = (
            ("cl.nombre", self.combos["cliente"].get(), True),
            ("CONCAT(v.marca,' ',v.modelo)", self.combos["vehiculo"].get(), True),
            ("e.nombre", self.combos["empleado"].get(), True),
            ("c.fecha_inicio", self.entries["fecha_inicio"].get().strip(), False),
            ("c.fecha_fin", self.entries["fecha_fin"].get().strip(), False),
            ("c.cuota_mensual", self.entries["cuota_mensual"].get().strip(), False),
            ("c.kilometraje_permitido", self.entries["kilometraje_permitido"].get().strip(), False),
        )
        conditions = []
        parameters: list[str] = []
        for column, value, is_text_filter in filter_values:
            if value:
                conditions.append(f"{column} LIKE ?" if is_text_filter else f"{column} = ?")
                parameters.append(f"%{value}%" if is_text_filter else value)

        query = """SELECT c.contrato_id,cl.nombre AS cliente,
                          CONCAT(v.marca,' ',v.modelo) AS vehiculo,e.nombre AS empleado,
                          c.fecha_inicio,c.fecha_fin,c.cuota_mensual,c.kilometraje_permitido
                   FROM dbo.contrato_leasing c
                   JOIN dbo.cliente cl ON cl.cliente_id=c.cliente_id
                   JOIN dbo.vehiculo v ON v.vehiculo_id=c.vehiculo_id
                   JOIN dbo.empleado e ON e.empleado_id=c.empleado_id"""
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY c.contrato_id"

        try:
            columns, rows = self.db.select(query, parameters)
            self.table.set_rows(columns, rows)
            if not rows:
                self.info("No se encontraron contratos.")
        except DatabaseError as exc:
            self.error(exc)

    def show_all(self) -> None:
        for combo in self.combos.values():
            combo.set("")
        for entry in self.entries.values():
            entry.delete(0, END)
        self.refresh()

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
        self.contracts: list[Contract] = []
        self.payments: list[Payment] = []
        self.rows: list[PaymentRow] = []
        self.table_rows: dict[str, PaymentRow] = {}
        self._build_form()
        summary = ctk.CTkFrame(self)
        summary.pack(fill="x", padx=24, pady=(0, 12))
        self.summary_label = ctk.CTkLabel(
            summary, text="Seleccione un contrato para ver su resumen financiero.",
            anchor="w",
        )
        self.summary_label.pack(fill="x", padx=12, pady=10)
        ctk.CTkLabel(
            self, text="Cuotas estimadas desde el inicio del contrato; seleccione una fila para gestionarla.",
            anchor="w",
        ).pack(fill="x", padx=24, pady=(0, 6))
        self.table = DataTable(self)
        self.table.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        self.table.tree.bind("<<TreeviewSelect>>", self._select_row)
        self.refresh()

    def _build_form(self) -> None:
        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=24, pady=(0, 12))
        ctk.CTkLabel(form, text="Contrato").grid(row=0, column=0, padx=10, pady=(10, 2), sticky="w")
        self.contract_combo = ctk.CTkComboBox(
            form, width=190, values=[], command=self._contract_changed
        )
        self.contract_combo.grid(row=1, column=0, padx=10, pady=(0, 8))
        self.contract_combo.set("")
        self.contract_combo.bind("<KeyRelease>", self._contract_changed)
        fields = [("monto", "Monto"), ("fecha_pago", "Fecha Pago"), ("metodo_pago", "Método Pago"), ("estado", "Estado")]
        for index, (key, label) in enumerate(fields, start=1):
            ctk.CTkLabel(form, text=label).grid(row=0, column=index, padx=10, pady=(10, 2), sticky="w")
            entry = ctk.CTkEntry(form, width=160)
            entry.grid(row=1, column=index, padx=10, pady=(0, 8))
            self.entries[key] = entry
        buttons = ctk.CTkFrame(form, fg_color="transparent")
        buttons.grid(row=2, column=0, columnspan=5, pady=8)
        for text, command in [("Registrar Pago", self.save), ("Actualizar", self.update),
                              ("Eliminar", self.delete), ("Buscar", self.search),
                              ("Mostrar Todos", self.show_all)]:
            ctk.CTkButton(buttons, text=text, width=135, command=command).pack(side="left", padx=4)

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
            self._load_data()
            self._display_rows(self.rows)
        except DatabaseError as exc:
            self.error(exc)

    def _load_data(self) -> None:
        _, contract_rows = self.db.select(
            """SELECT c.contrato_id,cl.nombre,c.fecha_inicio,c.fecha_fin,
                      c.cuota_mensual,v.precio
               FROM dbo.contrato_leasing c
               JOIN dbo.cliente cl ON cl.cliente_id=c.cliente_id
               JOIN dbo.vehiculo v ON v.vehiculo_id=c.vehiculo_id
               ORDER BY c.contrato_id"""
        )
        _, payment_rows = self.db.select(
            """SELECT pago_id,contrato_id,monto,fecha_pago,metodo_pago,estado
               FROM dbo.pago ORDER BY contrato_id,fecha_pago,pago_id"""
        )
        self.contracts = [Contract(*row) for row in contract_rows]
        self.payments = [Payment(*row) for row in payment_rows]
        self.rows = build_payment_rows(self.contracts, self.payments, date.today())
        self.contract_ids = {
            f"{contract.contract_id} - {contract.client}": contract.contract_id
            for contract in self.contracts
        }
        self.contract_combo.configure(values=list(self.contract_ids))
        self._update_summary()

    def _display_rows(self, rows: list[PaymentRow]) -> None:
        self.selected_id = None
        self.table.set_rows(
            ["cliente", "fecha_pago", "monto", "metodo_pago", "estado"],
            [
                (row.contract.client, row.payment_date.strftime("%d/%m/%Y"),
                 f"S/ {row.amount:,.2f}",
                 row.payment.method if row.payment else "Sin registrar", row.status)
                for row in rows
            ],
        )
        self.table_rows = dict(zip(self.table.tree.get_children(), rows))

    def _contract_changed(self, _value: object) -> None:
        self._update_summary()

    def _update_summary(self) -> None:
        contract_id = self.contract_ids.get(self.contract_combo.get())
        contract = next((item for item in self.contracts if item.contract_id == contract_id), None)
        if contract is None:
            self.summary_label.configure(text="Seleccione un contrato para ver su resumen financiero.")
            return
        total = paid_total(contract.contract_id, self.payments)
        self.summary_label.configure(
            text=(f"Contrato {contract.contract_id}  |  Precio del vehículo: S/ {contract.vehicle_price:,.2f}"
                  f"  |  Total pagado: S/ {total:,.2f}"
                  f"  |  Saldo pendiente: S/ {contract.vehicle_price - total:,.2f}")
        )

    def search(self) -> None:
        try:
            contract_value = self.contract_combo.get().strip()
            if contract_value and contract_value not in self.contract_ids:
                raise ValueError("Seleccione un contrato válido.")
            amount_text = self.entries["monto"].get().strip()
            date_text = self.entries["fecha_pago"].get().strip()
            try:
                amount = Decimal(amount_text) if amount_text else None
                if amount is not None and not amount.is_finite():
                    raise ValueError
                payment_date = None
                if date_text:
                    try:
                        payment_date = date.fromisoformat(date_text)
                    except ValueError:
                        payment_date = datetime.strptime(date_text, "%d/%m/%Y").date()
            except (InvalidOperation, ValueError):
                raise ValueError("Ingrese un monto válido y una fecha AAAA-MM-DD o DD/MM/AAAA.")
            method = self.entries["metodo_pago"].get().strip().casefold()
            status = self.entries["estado"].get().strip().casefold()
            self._load_data()
            contract_id = self.contract_ids.get(contract_value)
            rows = [
                row for row in self.rows
                if (not contract_value or row.contract.contract_id == contract_id)
                and (amount is None or row.amount == amount)
                and (payment_date is None or row.payment_date == payment_date)
                and (not method or (row.payment is not None and method in row.payment.method.casefold()))
                and (not status or status in row.status.casefold())
            ]
            self._display_rows(rows)
            if not rows:
                self.info("No se encontraron pagos.")
        except (DatabaseError, ValueError) as exc:
            self.error(exc)

    def show_all(self) -> None:
        self.contract_combo.set("")
        for entry in self.entries.values():
            entry.delete(0, END)
        self.refresh()

    def _select_row(self, _event: object) -> None:
        selection = self.table.tree.selection()
        row = self.table_rows.get(selection[0]) if selection else None
        if row is None:
            return
        self.selected_id = row.payment.payment_id if row.payment else None
        contract = next(
            (name for name, value in self.contract_ids.items() if value == row.contract.contract_id), ""
        )
        self.contract_combo.set(contract)
        self._update_summary()
        values = (
            str(row.amount), row.payment_date.isoformat(),
            row.payment.method if row.payment else "",
            row.payment.status if row.payment else row.status,
        )
        for entry, value in zip(self.entries.values(), values):
            entry.delete(0, END)
            entry.insert(0, value)


class MaintenanceScreen(BaseScreen):
    """Maintenance management and quarterly scheduling."""

    def __init__(self, master: ctk.CTkBaseClass, db: DatabaseManager) -> None:
        super().__init__(master, db, "Mantenimientos")
        self.selected_id: int | None = None
        self.original_status: str | None = None
        self.vehicles: dict[str, tuple[int, int]] = {}
        self.providers: dict[str, int] = {}
        self.plates: dict[int, list[str]] = {}
        self.table_rows: dict[str, tuple[object, ...]] = {}
        self.entries: dict[str, ctk.CTkEntry] = {}
        self._build_form()
        summary = ctk.CTkFrame(self)
        summary.pack(fill="x", padx=24, pady=(0, 12))
        self.summary_label = ctk.CTkLabel(summary, text="Total proyectado anual: —", anchor="w")
        self.summary_label.pack(fill="x", padx=12, pady=10)
        self.table = DataTable(self)
        self.table.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        self.table.tree.bind("<<TreeviewSelect>>", self._select_row)
        self.refresh()

    def _build_form(self) -> None:
        form = ctk.CTkFrame(self)
        form.pack(fill="x", padx=24, pady=(0, 12))
        ctk.CTkLabel(form, text="Vehículo").grid(row=0, column=0, padx=10, pady=(10, 2), sticky="w")
        self.vehicle_combo = ctk.CTkComboBox(form, width=190, values=[], command=self._vehicle_changed)
        self.vehicle_combo.grid(row=1, column=0, padx=10, pady=(0, 8))
        self.vehicle_combo.set("")
        ctk.CTkLabel(form, text="Placa(s) asociada(s)").grid(row=0, column=1, padx=10, pady=(10, 2), sticky="w")
        self.plate_var = ctk.StringVar(value="Sin placa")
        ctk.CTkEntry(form, width=190, textvariable=self.plate_var, state="readonly").grid(
            row=1, column=1, padx=10, pady=(0, 8)
        )
        ctk.CTkLabel(form, text="Proveedor").grid(row=0, column=2, padx=10, pady=(10, 2), sticky="w")
        self.provider_combo = ctk.CTkComboBox(form, width=190, values=[])
        self.provider_combo.grid(row=1, column=2, padx=10, pady=(0, 8))
        self.provider_combo.set("")
        for index, (key, label) in enumerate([
            ("tipo_servicio", "Tipo de servicio"), ("fecha", "Fecha (AAAA-MM-DD)"),
            ("costo", "Costo"), ("kilometraje", "Kilometraje"),
        ]):
            column = index % 4
            ctk.CTkLabel(form, text=label).grid(row=2, column=column, padx=10, pady=(5, 2), sticky="w")
            entry = ctk.CTkEntry(form, width=190)
            entry.grid(row=3, column=column, padx=10, pady=(0, 8))
            self.entries[key] = entry
        self.entries["costo"].bind("<KeyRelease>", self._update_summary)
        ctk.CTkLabel(form, text="Estado").grid(row=0, column=3, padx=10, pady=(10, 2), sticky="w")
        self.status_combo = ctk.CTkComboBox(form, width=190, values=["Programado", "En Proceso", "Finalizado"])
        self.status_combo.grid(row=1, column=3, padx=10, pady=(0, 8))
        self.status_combo.set("Programado")
        buttons = ctk.CTkFrame(form, fg_color="transparent")
        buttons.grid(row=4, column=0, columnspan=4, pady=8)
        for text, command in [
            ("Nuevo", self.handle_nuevo), ("Guardar", self.save), ("Actualizar", self.update),
            ("Eliminar", self.delete), ("Buscar", self.search), ("Mostrar Todos", self.show_all),
        ]:
            ctk.CTkButton(buttons, text=text, width=110, command=command).pack(side="left", padx=4)

    def _load_lookups(self) -> None:
        _, vehicle_rows = self.db.select(
            "SELECT vehiculo_id,marca,modelo,kilometraje_actual FROM dbo.vehiculo ORDER BY vehiculo_id"
        )
        _, provider_rows = self.db.select(
            "SELECT proveedor_id,nombre_empresa FROM dbo.proveedor ORDER BY proveedor_id"
        )
        _, plate_rows = self.db.select(
            """SELECT c.vehiculo_id,ma.numero_placa
               FROM dbo.contrato_leasing c JOIN dbo.matricula ma ON ma.contrato_id=c.contrato_id
               ORDER BY c.vehiculo_id,ma.numero_placa"""
        )
        self.vehicles = {
            f"{row[0]} - {row[1]} {row[2]}": (int(row[0]), int(row[3])) for row in vehicle_rows
        }
        self.providers = {f"{row[0]} - {row[1]}": int(row[0]) for row in provider_rows}
        self.plates = {}
        for vehicle_id, plate in plate_rows:
            plates = self.plates.setdefault(int(vehicle_id), [])
            if str(plate) not in plates:
                plates.append(str(plate))
        self.vehicle_combo.configure(values=list(self.vehicles))
        self.provider_combo.configure(values=list(self.providers))
        self._show_plates()

    def _show_plates(self) -> None:
        vehicle = self.vehicles.get(self.vehicle_combo.get())
        self.plate_var.set(", ".join(self.plates.get(vehicle[0], [])) if vehicle and self.plates.get(vehicle[0]) else "Sin placa")

    def _vehicle_changed(self, value: str) -> None:
        self._show_plates()
        vehicle = self.vehicles.get(value)
        if vehicle:
            self.entries["kilometraje"].delete(0, END)
            self.entries["kilometraje"].insert(0, str(vehicle[1]))

    def _update_summary(self, _event: object = None) -> None:
        try:
            amount = Decimal(self.entries["costo"].get().strip())
            if not amount.is_finite() or amount < 0:
                raise ValueError
            text = f"Total proyectado anual (costo × 4): S/ {amount * 4:,.2f}"
        except (InvalidOperation, ValueError):
            text = "Total proyectado anual: ingrese un costo válido."
        self.summary_label.configure(text=text)

    def handle_nuevo(self) -> None:
        if self.selected_id is None and self._has_input():
            self.save()
        else:
            self.new_record()

    def _has_input(self) -> bool:
        return bool(
            self.vehicle_combo.get().strip()
            or self.provider_combo.get().strip()
            or any(entry.get().strip() for entry in self.entries.values())
        )

    def new_record(self) -> None:
        self.selected_id = None
        self.original_status = None
        if self.table.tree.selection():
            self.table.tree.selection_remove(*self.table.tree.selection())
        self.vehicle_combo.set("")
        self.provider_combo.set("")
        self.status_combo.set("Programado")
        self._show_plates()
        for entry in self.entries.values():
            entry.delete(0, END)
        self._update_summary()

    def _form_values(self) -> tuple[int, int, str, date, Decimal, int, str]:
        vehicle = self.vehicles.get(self.vehicle_combo.get().strip())
        provider = self.providers.get(self.provider_combo.get().strip())
        if vehicle is None or provider is None:
            raise ValueError("Seleccione un vehículo y un proveedor válidos.")
        service = self.entries["tipo_servicio"].get().strip()
        if not service or len(service) > 40:
            raise ValueError("Ingrese un tipo de servicio de hasta 40 caracteres.")
        date_text = self.entries["fecha"].get().strip()
        if not date_text:
            maintenance_date = date.today()
        else:
            try:
                maintenance_date = date.fromisoformat(date_text)
            except ValueError:
                try:
                    maintenance_date = datetime.strptime(date_text, "%d/%m/%Y").date()
                except ValueError:
                    raise ValueError("Ingrese una fecha válida en formato AAAA-MM-DD o DD/MM/AAAA.")
        cost_text = self.entries["costo"].get().strip().replace("S/", "").replace("s/", "").replace(",", "").strip()
        try:
            cost = Decimal(cost_text)
            if not cost.is_finite() or cost < 0 or cost >= Decimal("100000000") or cost.as_tuple().exponent < -2:
                raise ValueError
        except (ValueError, InvalidOperation):
            raise ValueError("Ingrese un costo numérico válido (ej. 120.00).")
        mileage_text = self.entries["kilometraje"].get().strip().replace(",", "").strip()
        if not mileage_text:
            mileage = vehicle[1]
        else:
            try:
                mileage = int(mileage_text)
                if mileage < 0 or mileage > 2147483647:
                    raise ValueError
            except ValueError:
                raise ValueError("Ingrese un kilometraje entero no negativo.")
        status = self.status_combo.get().strip() or "Programado"
        if status.casefold() not in {"programado", "en proceso", "finalizado"} and status != self.original_status:
            raise ValueError("Seleccione un estado válido.")
        return vehicle[0], provider, service, maintenance_date, cost, mileage, status

    def save(self) -> None:
        try:
            vehicle, provider, service, start, cost, mileage, _status = self._form_values()
            dates = quarterly_dates(start)
            parameters = tuple(
                value for scheduled in dates
                for value in (vehicle, provider, scheduled, service, cost, mileage, "Programado")
            )
            self.db.insert(
                """INSERT INTO dbo.mantenimiento
                   (vehiculo_id,proveedor_id,fecha,tipo_servicio,costo,kilometraje,estado)
                   VALUES (?,?,?,?,?,?,?),(?,?,?,?,?,?,?),(?,?,?,?,?,?,?),(?,?,?,?,?,?,?)""",
                parameters,
            )
            self.refresh()
            self.new_record()
            self.info("Mantenimiento registrado con éxito. Se generaron las 4 fechas programadas para el año.")
        except (DatabaseError, ValueError) as exc:
            self.error(exc)

    def update(self) -> None:
        if self.selected_id is None:
            self.info("Seleccione un mantenimiento en la tabla.")
            return
        try:
            vehicle, provider, service, maintenance_date, cost, mileage, status = self._form_values()
            self.db.update(
                """UPDATE dbo.mantenimiento SET vehiculo_id=?,proveedor_id=?,fecha=?,
                   tipo_servicio=?,costo=?,kilometraje=?,estado=? WHERE mantenimiento_id=?""",
                (vehicle, provider, maintenance_date, service, cost, mileage, status, self.selected_id),
            )
            self.refresh()
            self.info("Mantenimiento actualizado exitosamente.")
        except (DatabaseError, ValueError) as exc:
            self.error(exc)

    def delete(self) -> None:
        if self.selected_id is None:
            self.info("Seleccione un mantenimiento en la tabla.")
            return
        try:
            self.db.delete("DELETE FROM dbo.mantenimiento WHERE mantenimiento_id=?", (self.selected_id,))
            self.refresh()
            self.new_record()
            self.info("Mantenimiento eliminado exitosamente.")
        except DatabaseError as exc:
            self.error(exc)

    def _load_rows(self) -> list[tuple[object, ...]]:
        _, rows = self.db.select(
            """SELECT m.mantenimiento_id,m.vehiculo_id,m.proveedor_id,
                      CONCAT(v.marca,' ',v.modelo),pr.nombre_empresa,m.tipo_servicio,
                      m.fecha,m.costo,m.kilometraje,m.estado
               FROM dbo.mantenimiento m JOIN dbo.vehiculo v ON v.vehiculo_id=m.vehiculo_id
               JOIN dbo.proveedor pr ON pr.proveedor_id=m.proveedor_id
               ORDER BY m.fecha DESC,m.mantenimiento_id DESC"""
        )
        return rows

    def _display_rows(self, rows: list[tuple[object, ...]]) -> None:
        self.selected_id = None
        self.original_status = None
        self.table.set_rows(
            ["vehiculo", "placa", "proveedor", "tipo_servicio", "fecha", "costo", "estado"],
            [
                (
                    row[3],
                    ", ".join(self.plates.get(int(row[1]), [])) or "Sin placa",
                    row[4],
                    row[5],
                    row[6].strftime("%d/%m/%Y") if hasattr(row[6], "strftime") else str(row[6]),
                    f"S/ {row[7]:,.2f}",
                    row[9],
                )
                for row in rows
            ],
        )
        self.table_rows = dict(zip(self.table.tree.get_children(), rows))

    def refresh(self) -> None:
        try:
            self._load_lookups()
            self._display_rows(self._load_rows())
        except DatabaseError as exc:
            self.error(exc)

    def search(self) -> None:
        try:
            vehicle_text = self.vehicle_combo.get().strip()
            provider_text = self.provider_combo.get().strip()
            if vehicle_text and vehicle_text not in self.vehicles:
                raise ValueError("Seleccione un vehículo válido.")
            if provider_text and provider_text not in self.providers:
                raise ValueError("Seleccione un proveedor válido.")
            filters = {key: entry.get().strip() for key, entry in self.entries.items()}
            try:
                selected_date = None
                if filters["fecha"]:
                    try:
                        selected_date = date.fromisoformat(filters["fecha"])
                    except ValueError:
                        selected_date = datetime.strptime(filters["fecha"], "%d/%m/%Y").date()
                cost_text = filters["costo"].replace("S/", "").replace("s/", "").replace(",", "").strip()
                cost = Decimal(cost_text) if cost_text else None
                mileage_text = filters["kilometraje"].replace(",", "").strip()
                mileage = int(mileage_text) if mileage_text else None
                if cost is not None and not cost.is_finite():
                    raise ValueError
            except (ValueError, InvalidOperation):
                raise ValueError("Ingrese una fecha válida (AAAA-MM-DD o DD/MM/AAAA), costo y kilometraje válidos.")
            status = self.status_combo.get().strip().casefold()
            rows = [
                row for row in self._load_rows()
                if (not vehicle_text or row[1] == self.vehicles[vehicle_text][0])
                and (not provider_text or row[2] == self.providers[provider_text])
                and (not filters["tipo_servicio"] or filters["tipo_servicio"].casefold() in str(row[5]).casefold())
                and (selected_date is None or row[6] == selected_date)
                and (cost is None or row[7] == cost)
                and (mileage is None or row[8] == mileage)
                and (not status or status in str(row[9]).casefold())
            ]
            self._display_rows(rows)
            if not rows:
                self.info("No se encontraron mantenimientos.")
        except (DatabaseError, ValueError) as exc:
            self.error(exc)

    def show_all(self) -> None:
        self.new_record()
        self.status_combo.set("")
        self.refresh()

    def _select_row(self, _event: object) -> None:
        selection = self.table.tree.selection()
        row = self.table_rows.get(selection[0]) if selection else None
        if row is None:
            return
        self.selected_id = int(row[0])
        self.original_status = str(row[9])
        self.vehicle_combo.set(next((name for name, value in self.vehicles.items() if value[0] == row[1]), ""))
        self.provider_combo.set(next((name for name, value in self.providers.items() if value == row[2]), ""))
        self.status_combo.set(self.original_status)
        self._show_plates()
        fecha_str = row[6].strftime("%d/%m/%Y") if hasattr(row[6], "strftime") else str(row[6])
        for key, value in zip(("tipo_servicio", "fecha", "costo", "kilometraje"), (row[5], fecha_str, row[7], row[8])):
            self.entries[key].delete(0, END)
            self.entries[key].insert(0, str(value))
        self._update_summary()


class ReportsScreen(BaseScreen):
    """Displays user-facing reports backed by SQL views and tables with KPI summaries."""

    def __init__(self, master: ctk.CTkBaseClass, db: DatabaseManager) -> None:
        super().__init__(master, db, "Reportes del Sistema")
        self.report_configs: dict[str, dict[str, str]] = {
            "Resumen de Pagos": {
                "query": """SELECT c.contrato_id,
                                   COALESCE(cl.nombre, 'Sin cliente asignado') AS cliente,
                                   COALESCE(cl.dni, '-') AS dni,
                                   CONCAT(v.marca, ' ', v.modelo) AS vehiculo,
                                   c.cuota_mensual,
                                   rp.cantidad_pagos,
                                   rp.total_pagado,
                                   CASE 
                                       WHEN (c.cuota_mensual * NULLIF(DATEDIFF(month, c.fecha_inicio, c.fecha_fin), 0)) > rp.total_pagado 
                                       THEN (c.cuota_mensual * DATEDIFF(month, c.fecha_inicio, c.fecha_fin)) - rp.total_pagado 
                                       ELSE 0 
                                   END AS saldo_pendiente,
                                   CASE 
                                       WHEN rp.cantidad_pagos = 0 THEN 'Sin pagos'
                                       WHEN rp.total_pagado >= (c.cuota_mensual * DATEDIFF(month, c.fecha_inicio, c.fecha_fin)) THEN 'Completado'
                                       ELSE 'En curso'
                                   END AS estado_pago,
                                   c.fecha_inicio,
                                   c.fecha_fin
                            FROM dbo.vw_resumen_pagos rp
                            JOIN dbo.contrato_leasing c ON c.contrato_id = rp.contrato_id
                            LEFT JOIN dbo.cliente cl ON cl.cliente_id = c.cliente_id
                            LEFT JOIN dbo.vehiculo v ON v.vehiculo_id = c.vehiculo_id
                            ORDER BY c.contrato_id""",
                "type": "resumen_pagos",
            },
            "Resumen Consolidado de Pagos y Clientes": {
                "query": """SELECT cl.nombre AS cliente, cl.dni, c.contrato_id,
                                   c.cuota_mensual, rp.cantidad_pagos, rp.total_pagado,
                                   c.fecha_inicio, c.fecha_fin
                            FROM dbo.vw_resumen_pagos rp
                            JOIN dbo.contrato_leasing c ON c.contrato_id = rp.contrato_id
                            JOIN dbo.cliente cl ON cl.cliente_id = c.cliente_id
                            ORDER BY cl.nombre, c.contrato_id""",
                "type": "consolidado",
            },
            "Clientes y sus Contratos": {
                "query": "SELECT * FROM dbo.vw_clientes_contratos ORDER BY cliente, contrato_id",
                "type": "clientes_contratos",
            },
            "Reporte de Seguros de Vehículos": {
                "query": "SELECT * FROM dbo.vw_vehiculos_seguros ORDER BY marca, modelo",
                "type": "vehiculos_seguros",
            },
            "Historial de Mantenimientos": {
                "query": "SELECT * FROM dbo.vw_historial_mantenimiento ORDER BY fecha DESC",
                "type": "mantenimiento",
            },
        }
        self.report_views = {
            "Resumen de Pagos": "vw_resumen_pagos",
            "Reporte de Seguros de Vehículos": "vw_vehiculos_seguros",
            "Clientes y sus Contratos": "vw_clientes_contratos",
            "Historial de Mantenimientos": "vw_historial_mantenimiento",
            "Resumen Consolidado de Pagos y Clientes": "vw_resumen_pagos",
        }
        self.report_name = ctk.StringVar(value="Resumen de Pagos")
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._apply_filter())

        self._all_columns: list[str] = []
        self._all_rows: list[tuple[object, ...]] = []
        self._current_columns: list[str] = []
        self._current_rows: list[tuple[object, ...]] = []

        self._build_controls()
        self._build_kpi_cards()
        self._build_table()
        self.refresh()

    def _build_controls(self) -> None:
        control_frame = ctk.CTkFrame(self, fg_color="transparent")
        control_frame.pack(fill="x", padx=24, pady=(0, 10))

        top_row = ctk.CTkFrame(control_frame, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(top_row, text="Reporte:", font=ctk.CTkFont(weight="bold")).pack(
            side="left", padx=(0, 8)
        )
        self.selector = ctk.CTkComboBox(
            top_row,
            width=330,
            variable=self.report_name,
            values=list(self.report_configs),
            command=lambda _val: self.refresh(),
        )
        self.selector.pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            top_row,
            text="Actualizar reporte",
            width=135,
            command=self.refresh,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            top_row,
            text="Exportar CSV",
            width=120,
            fg_color="#047857",
            hover_color="#065f46",
            command=self.export_csv,
        ).pack(side="left")

        filter_row = ctk.CTkFrame(control_frame, fg_color="transparent")
        filter_row.pack(fill="x")

        ctk.CTkLabel(filter_row, text="Buscar:", font=ctk.CTkFont(weight="bold")).pack(
            side="left", padx=(0, 8)
        )
        self.search_entry = ctk.CTkEntry(
            filter_row,
            placeholder_text="Filtrar datos por cliente, ID, fecha, estado...",
            textvariable=self.search_var,
            width=330,
        )
        self.search_entry.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            filter_row,
            text="Limpiar",
            width=80,
            fg_color="transparent",
            border_width=1,
            command=lambda: self.search_var.set(""),
        ).pack(side="left", padx=(0, 16))

        self.status_label = ctk.CTkLabel(
            filter_row,
            text="",
            text_color="#9ca3af",
            font=ctk.CTkFont(size=12),
        )
        self.status_label.pack(side="left")

    def _build_kpi_cards(self) -> None:
        self.kpi_container = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_container.pack(fill="x", padx=24, pady=(0, 12))

        self.kpi_labels: list[tuple[ctk.CTkLabel, ctk.CTkLabel]] = []
        for i in range(4):
            card = ctk.CTkFrame(
                self.kpi_container,
                corner_radius=10,
                border_width=1,
                border_color=("#e5e7eb", "#374151"),
                fg_color=("#ffffff", "#1e293b"),
            )
            card.pack(side="left", fill="both", expand=True, padx=(0 if i == 0 else 8, 0))

            title_lbl = ctk.CTkLabel(
                card,
                text="--",
                font=ctk.CTkFont(size=11),
                text_color="#9ca3af",
            )
            title_lbl.pack(anchor="w", padx=14, pady=(10, 2))

            val_lbl = ctk.CTkLabel(
                card,
                text="--",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=("#111827", "#f9fafb"),
            )
            val_lbl.pack(anchor="w", padx=14, pady=(0, 10))

            self.kpi_labels.append((title_lbl, val_lbl))

    def _build_table(self) -> None:
        self.table = DataTable(self)
        self.table.pack(fill="both", expand=True, padx=24, pady=(0, 24))

    def _update_kpis(self, rows: list[tuple[object, ...]]) -> None:
        report_key = self.report_name.get()
        config = self.report_configs.get(report_key, {})
        rtype = config.get("type", "")

        def _to_float(val: object) -> float:
            try:
                return float(str(val).replace("S/", "").replace("$", "").replace(",", "").strip())
            except (ValueError, TypeError):
                return 0.0

        def _to_int(val: object) -> int:
            try:
                return int(float(str(val).replace(",", "").strip()))
            except (ValueError, TypeError):
                return 0

        count = len(rows)

        if rtype == "resumen_pagos":
            # Columns: contrato_id, cliente, dni, vehiculo, cuota_mensual, cantidad_pagos, total_pagado, saldo_pendiente, estado_pago, fecha_inicio, fecha_fin
            total_pagos = sum(_to_int(row[5]) for row in rows if len(row) > 5)
            total_recaudado = sum(_to_float(row[6]) for row in rows if len(row) > 6)
            con_pagos = sum(1 for row in rows if len(row) > 5 and _to_int(row[5]) > 0)
            sin_pagos = count - con_pagos
            cards_data = [
                ("Total Contratos", f"{count}"),
                ("Total Recaudado", f"S/ {total_recaudado:,.2f}"),
                ("Con Pagos Registrados", f"{con_pagos} contratos ({total_pagos} pagos)"),
                ("Sin Pagos (Vacíos / Pend.)", f"{sin_pagos} contratos"),
            ]
        elif rtype == "consolidado":
            unique_clients = len({row[0] for row in rows if row and row[0] and row[0] != "-"})
            total_pagos = sum(_to_int(row[4]) for row in rows if len(row) > 4)
            total_recaudado = sum(_to_float(row[5]) for row in rows if len(row) > 5)
            sin_pagos = sum(1 for row in rows if len(row) > 4 and _to_int(row[4]) == 0)
            cards_data = [
                ("Contratos Asociados", f"{count}"),
                ("Clientes Únicos", f"{unique_clients}"),
                ("Total Recaudado", f"S/ {total_recaudado:,.2f}"),
                ("Contratos Sin Pagos", f"{sin_pagos}"),
            ]
        elif rtype == "clientes_contratos":
            unique_clients = len({row[0] for row in rows if row and row[0]})
            total_cuotas = sum(_to_float(row[4]) for row in rows if len(row) > 4)
            cuota_prom = (total_cuotas / count) if count > 0 else 0.0
            cards_data = [
                ("Total Contratos", f"{count}"),
                ("Clientes Registrados", f"{unique_clients}"),
                ("Cuota Mensual Promedio", f"S/ {cuota_prom:,.2f}"),
                ("Suma Cuotas Mensuales", f"S/ {total_cuotas:,.2f}"),
            ]
        elif rtype == "vehiculos_seguros":
            unique_insurers = len({row[2] for row in rows if len(row) > 2 and row[2]})
            unique_brands = len({row[0] for row in rows if len(row) > 0 and row[0]})
            cards_data = [
                ("Vehículos Asegurados", f"{count}"),
                ("Aseguradoras Aliadas", f"{unique_insurers}"),
                ("Marcas de Vehículos", f"{unique_brands}"),
                ("Pólizas Registradas", f"{count}"),
            ]
        elif rtype == "mantenimiento":
            total_costo = sum(_to_float(row[4]) for row in rows if len(row) > 4)
            costo_prom = (total_costo / count) if count > 0 else 0.0
            completados = sum(
                1 for row in rows
                if len(row) > 5 and str(row[5]).strip().lower() in ("completado", "finalizado", "realizado")
            )
            cards_data = [
                ("Total Servicios", f"{count}"),
                ("Costo Total Mantenimiento", f"S/ {total_costo:,.2f}"),
                ("Costo Promedio", f"S/ {costo_prom:,.2f}"),
                ("Servicios Completados", f"{completados}"),
            ]
        else:
            cards_data = [
                ("Total Registros", f"{count}"),
                ("--", "--"),
                ("--", "--"),
                ("--", "--"),
            ]

        for i, (title, val) in enumerate(cards_data):
            if i < len(self.kpi_labels):
                self.kpi_labels[i][0].configure(text=title)
                self.kpi_labels[i][1].configure(text=val)

    def refresh(self) -> None:
        report_key = self.report_name.get()
        config = self.report_configs.get(report_key)
        if not config:
            return
        try:
            columns, rows = self.db.select(config["query"])
            self._all_columns = columns
            self._all_rows = rows
            self._apply_filter()
        except DatabaseError as exc:
            self.error(exc)

    def _apply_filter(self) -> None:
        search_text = self.search_var.get().strip().lower()
        if not search_text:
            filtered = self._all_rows
        else:
            filtered = [
                row for row in self._all_rows
                if any(search_text in str(val).lower() for val in row if val is not None)
            ]
        self._current_columns = self._all_columns
        self._current_rows = filtered
        self.table.set_rows(self._all_columns, filtered)
        self._update_kpis(filtered)
        if search_text:
            self.status_label.configure(
                text=f"Mostrando {len(filtered)} de {len(self._all_rows)} registros"
            )
        else:
            self.status_label.configure(
                text=f"Total: {len(self._all_rows)} registros"
            )

    def export_csv(self) -> None:
        if not self._current_rows:
            self.info("No hay datos disponibles para exportar.")
            return
        file_path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".csv",
            filetypes=[("Archivos CSV (*.csv)", "*.csv"), ("Todos los archivos", "*.*")],
            title="Exportar reporte a CSV",
            initialfile=f"reporte_{self.report_name.get().lower().replace(' ', '_')}.csv",
        )
        if not file_path:
            return
        try:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([c.replace("_", " ").title() for c in self._current_columns])
                for row in self._current_rows:
                    writer.writerow([str(v) if v is not None else "" for v in row])
            self.info(f"Reporte exportado exitosamente con {len(self._current_rows)} filas.")
        except Exception as exc:
            self.error(exc)
