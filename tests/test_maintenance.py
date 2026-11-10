import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from tkinter import END

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "autolease_app"))

import customtkinter as ctk

from database import DatabaseError
from maintenance_schedule import quarterly_dates
from ui import MaintenanceScreen


class ScheduleTests(unittest.TestCase):
    def test_quarterly_dates_and_month_ends(self):
        self.assertEqual(quarterly_dates(date(2027, 1, 1)), (
            date(2027, 1, 1), date(2027, 4, 1), date(2027, 7, 1), date(2027, 10, 1)
        ))
        self.assertEqual(quarterly_dates(date(2023, 5, 31)), (
            date(2023, 5, 31), date(2023, 8, 31), date(2023, 11, 30), date(2024, 2, 29)
        ))
        with self.assertRaises(ValueError):
            quarterly_dates(date(9999, 12, 31))


class FakeDatabase:
    def __init__(self):
        self.rows = [(1, 1, 1, "Toyota Corolla", "Taller", "Aceite",
                      date(2026, 1, 1), Decimal("100.00"), 1200, "Pendiente revisión")]
        self.calls = []
        self.fail_insert = False

    def select(self, query, parameters=()):
        if "FROM dbo.vehiculo ORDER BY" in query:
            return [], [(1, "Toyota", "Corolla", 1500), (2, "Kia", "Rio", 200)]
        if "FROM dbo.proveedor ORDER BY" in query:
            return [], [(1, "Taller")]
        if "FROM dbo.contrato_leasing c" in query:
            return [], [(1, "ABC-123"), (1, "XYZ-789"), (1, "ABC-123")]
        if "FROM dbo.mantenimiento m" in query:
            return [], list(self.rows)
        raise AssertionError(query)

    def insert(self, query, parameters):
        if self.fail_insert:
            raise DatabaseError("Error al registrar")
        self.calls.append(("insert", query, parameters))
        for offset in range(0, len(parameters), 7):
            vehicle, provider, day, service, cost, mileage, status = parameters[offset:offset + 7]
            self.rows.append((len(self.rows) + 1, vehicle, provider, "Toyota Corolla", "Taller",
                              service, day, cost, mileage, status))
        return 4

    def update(self, query, parameters):
        self.calls.append(("update", query, parameters))
        vehicle, provider, day, service, cost, mileage, status, record_id = parameters
        self.rows = [
            (record_id, vehicle, provider, "Toyota Corolla", "Taller", service,
             day, cost, mileage, status) if row[0] == record_id else row
            for row in self.rows
        ]
        return 1

    def delete(self, query, parameters):
        self.calls.append(("delete", query, parameters))
        self.rows = [row for row in self.rows if row[0] != parameters[0]]
        return 1


class MaintenanceScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ctk.CTk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        self.db = FakeDatabase()
        self.screen = MaintenanceScreen(self.root, self.db)
        self.errors = []
        self.infos = []
        self.screen.error = self.errors.append
        self.screen.info = self.infos.append

    def tearDown(self):
        self.screen.destroy()

    def fill_form(self):
        self.screen.vehicle_combo.set("1 - Toyota Corolla")
        self.screen._vehicle_changed("1 - Toyota Corolla")
        self.screen.provider_combo.set("1 - Taller")
        self.screen.entries["tipo_servicio"].insert(0, "Revisión")
        self.screen.entries["fecha"].insert(0, "2027-01-01")
        self.screen.entries["costo"].insert(0, "120.50")
        self.screen.status_combo.set("Programado")
        self.screen._update_summary()

    def select_first(self):
        self.screen.table.tree.selection_set(self.screen.table.tree.get_children()[0])
        self.screen._select_row(None)

    def test_create_four_in_one_statement_and_summary(self):
        self.assertEqual(tuple(self.screen.table.tree["columns"]),
                         ("vehiculo", "placa", "proveedor", "tipo_servicio", "fecha", "costo", "estado"))
        self.fill_form()
        self.assertEqual(self.screen.plate_var.get(), "ABC-123, XYZ-789")
        self.assertEqual(self.screen.entries["kilometraje"].get(), "1500")
        self.assertIn("S/ 482.00", self.screen.summary_label.cget("text"))
        self.screen.save()
        self.assertFalse(self.errors)
        _, query, parameters = self.db.calls[0]
        self.assertEqual(query.count("(?,?,?,?,?,?,?)"), 4)
        self.assertEqual(parameters[2::7], quarterly_dates(date(2027, 1, 1)))
        self.assertEqual(parameters[6::7], ("Programado",) * 4)
        self.assertEqual(parameters[5::7], (1500,) * 4)
        self.assertEqual(len(self.screen.table.tree.get_children()), 5)
        self.screen.table.tree.selection_set(self.screen.table.tree.get_children()[1])
        self.screen._select_row(None)
        self.screen.status_combo.set("Finalizado")
        self.screen.update()
        self.assertEqual([row[9] for row in self.db.rows[1:]], [
            "Finalizado", "Programado", "Programado", "Programado"
        ])
        self.screen.table.tree.selection_set(self.screen.table.tree.get_children()[1])
        self.screen._select_row(None)
        self.screen.delete()
        self.assertEqual(len(self.db.rows), 4)

    def test_selection_preserves_old_status_and_updates_or_deletes_one(self):
        self.select_first()
        self.assertEqual(self.screen.status_combo.get(), "Pendiente revisión")
        self.screen.update()
        self.assertEqual(self.db.calls[-1][0], "update")
        self.assertEqual(self.db.calls[-1][2][-2:], ("Pendiente revisión", 1))
        self.select_first()
        self.screen.delete()
        self.assertEqual(self.db.calls[-1][2], (1,))

    def test_validation_and_failed_insert(self):
        self.fill_form()
        self.screen.vehicle_combo.set("")
        self.screen.save()
        self.assertFalse(self.db.calls)
        self.assertIn("vehículo", str(self.errors[-1]))
        self.screen.vehicle_combo.set("1 - Toyota Corolla")
        self.db.fail_insert = True
        self.screen.save()
        self.assertIn("Error al registrar", str(self.errors[-1]))
        self.assertEqual(len(self.db.rows), 1)

    def test_nuevo_button_saves_when_form_filled(self):
        self.fill_form()
        self.screen.entries["fecha"].delete(0, END)
        self.screen.entries["fecha"].insert(0, "01/01/2027")
        self.screen.entries["costo"].delete(0, END)
        self.screen.entries["costo"].insert(0, "S/ 120.50")
        self.screen.handle_nuevo()
        self.assertFalse(self.errors)
        self.assertEqual(len(self.screen.table.tree.get_children()), 5)
        self.assertIn("registrado con éxito", str(self.infos[-1]))

    def test_nuevo_button_clears_selection_when_row_selected(self):
        self.select_first()
        self.assertIsNotNone(self.screen.selected_id)
        self.screen.handle_nuevo()
        self.assertIsNone(self.screen.selected_id)
        self.assertEqual(self.screen.entries["tipo_servicio"].get(), "")

    def test_search_new_and_show_all(self):
        self.select_first()
        self.screen.search()
        self.assertEqual(len(self.screen.table.tree.get_children()), 1)
        self.screen.new_record()
        self.assertIsNone(self.screen.selected_id)
        self.assertEqual(self.screen.status_combo.get(), "Programado")
        self.screen.show_all()
        self.assertEqual(self.screen.status_combo.get(), "")
        self.assertEqual(len(self.screen.table.tree.get_children()), 1)
        self.screen.vehicle_combo.set("2 - Kia Rio")
        self.screen._vehicle_changed("2 - Kia Rio")
        self.assertEqual(self.screen.plate_var.get(), "Sin placa")
        self.screen.entries["costo"].insert(0, "no válido")
        self.screen.save()
        self.assertTrue(self.errors)


if __name__ == "__main__":
    unittest.main()
