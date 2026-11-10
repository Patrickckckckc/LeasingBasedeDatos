import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from tkinter import END

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "autolease_app"))

import customtkinter as ctk

from payment_schedule import Contract, Payment, build_payment_rows, paid_total, scheduled_dates
from ui import PaymentScreen


class PaymentScheduleTests(unittest.TestCase):
    def setUp(self):
        self.contract = Contract(
            1, "Ana", date(2026, 1, 31), date(2026, 5, 1),
            Decimal("1000.00"), Decimal("10000.00"),
        )
        self.payments = [
            Payment(1, 1, Decimal("1000.00"), date(2026, 1, 31), "Tarjeta", "Pagado"),
            Payment(2, 1, Decimal("200.00"), date(2026, 2, 28), "Efectivo", "Pendiente"),
            Payment(3, 1, Decimal("50.00"), date(2026, 2, 28), "Tarjeta", "Pagado"),
            Payment(4, 1, Decimal("100.00"), date(2026, 2, 15), "Tarjeta", "Pagado"),
            Payment(5, 2, Decimal("500.00"), date(2026, 1, 31), "Tarjeta", "Pagado"),
        ]

    def test_schedule_preserves_day_and_excludes_end(self):
        self.assertEqual(list(scheduled_dates(self.contract.start, self.contract.end)), [
            date(2026, 1, 31), date(2026, 2, 28), date(2026, 3, 31), date(2026, 4, 30)
        ])
        self.assertEqual(list(scheduled_dates(date(2026, 1, 1), date(2026, 3, 1))), [
            date(2026, 1, 1), date(2026, 2, 1)
        ])
        self.assertEqual(list(scheduled_dates(date(2026, 1, 1), date(2026, 1, 1))), [])
        self.assertEqual(list(scheduled_dates(date(2024, 1, 31), date(2024, 4, 1))), [
            date(2024, 1, 31), date(2024, 2, 29), date(2024, 3, 31)
        ])

    def test_schedule_includes_records_and_uses_current_date(self):
        rows = build_payment_rows([self.contract], self.payments, date(2026, 3, 31))
        self.assertEqual([row.payment_date for row in rows], [
            date(2026, 1, 31), date(2026, 2, 15), date(2026, 2, 28),
            date(2026, 2, 28), date(2026, 3, 31), date(2026, 4, 30),
        ])
        self.assertEqual([row.status for row in rows], [
            "Pagado", "Pagado", "Atrasado", "Pagado", "Pendiente", "Pendiente"
        ])
        self.assertIsNone(rows[-1].payment)
        self.assertEqual(rows[-1].amount, Decimal("1000.00"))

    def test_total_is_paid_records_for_selected_contract_only(self):
        self.assertEqual(paid_total(1, self.payments), Decimal("1150.00"))
        self.assertEqual(self.contract.vehicle_price - paid_total(1, self.payments), Decimal("8850.00"))
        self.assertEqual(paid_total(9, self.payments), Decimal("0"))

    def test_unknown_status_is_not_silently_classified(self):
        payment = Payment(10, 1, Decimal("1"), date(2026, 1, 31), "Tarjeta", "Revisión")
        self.assertEqual(build_payment_rows([self.contract], [payment], date(2026, 2, 1))[0].status, "Revisión")


class FakeDatabase:
    def __init__(self):
        self.contracts = [(1, "Ana", date(2026, 1, 1), date(2026, 4, 1), Decimal("1000"), Decimal("5000"))]
        self.payments = [(1, 1, Decimal("1000"), date(2026, 1, 1), "Tarjeta", "Pagado")]
        self.calls = []

    def select(self, query, parameters=()):
        if "FROM dbo.contrato_leasing c" in query:
            return [], self.contracts
        if "FROM dbo.pago" in query:
            return [], self.payments
        raise AssertionError(query)

    def insert(self, query, parameters):
        self.calls.append(("insert", parameters))
        contract, amount, payment_date, method, status = parameters
        self.payments.append((2, contract, Decimal(amount), date.fromisoformat(payment_date), method, status))
        return 1

    def update(self, query, parameters):
        self.calls.append(("update", parameters))
        contract, amount, payment_date, method, status, payment_id = parameters
        self.payments = [
            (payment_id, contract, Decimal(amount), date.fromisoformat(payment_date), method, status)
            if row[0] == payment_id else row for row in self.payments
        ]
        return 1

    def delete(self, query, parameters):
        self.calls.append(("delete", parameters))
        self.payments = [row for row in self.payments if row[0] != parameters[0]]
        return 1


class PaymentScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ctk.CTk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        self.db = FakeDatabase()
        self.screen = PaymentScreen(self.root, self.db)

    def tearDown(self):
        self.screen.destroy()

    def select_row(self, index):
        item = self.screen.table.tree.get_children()[index]
        self.screen.table.tree.selection_set(item)
        self.screen._select_row(None)

    def test_crud_and_contract_summary(self):
        self.assertEqual(tuple(self.screen.table.tree["columns"]),
                         ("cliente", "fecha_pago", "monto", "metodo_pago", "estado"))
        self.assertEqual(len(self.screen.table.tree.get_children()), 3)
        self.select_row(1)
        self.assertIsNone(self.screen.selected_id)
        self.assertEqual(self.screen.entries["fecha_pago"].get(), "2026-02-01")
        self.assertIn("Total pagado: S/ 1,000.00", self.screen.summary_label.cget("text"))
        self.assertIn("Saldo pendiente: S/ 4,000.00", self.screen.summary_label.cget("text"))
        self.screen.entries["metodo_pago"].insert(0, "Efectivo")
        self.screen.entries["estado"].delete(0, END)
        self.screen.entries["estado"].insert(0, "Pagado")
        self.screen.save()
        self.assertEqual(self.db.calls[-1][0], "insert")
        self.assertIn("Total pagado: S/ 2,000.00", self.screen.summary_label.cget("text"))
        self.select_row(1)
        self.assertEqual(self.screen.selected_id, 2)
        self.screen.update()
        self.assertEqual(self.db.calls[-1][0], "update")
        self.select_row(1)
        self.screen.delete()
        self.assertEqual(self.db.calls[-1], ("delete", (2,)))
        self.assertIn("Total pagado: S/ 1,000.00", self.screen.summary_label.cget("text"))

    def test_search_filters_schedule_but_not_summary(self):
        self.screen.contract_combo.set("1 - Ana")
        self.screen.entries["fecha_pago"].insert(0, "01/02/2026")
        self.screen.search()
        self.assertEqual(len(self.screen.table.tree.get_children()), 1)
        self.assertIn("Total pagado: S/ 1,000.00", self.screen.summary_label.cget("text"))
        self.screen.show_all()
        self.assertEqual(len(self.screen.table.tree.get_children()), 3)
        self.assertIn("Seleccione un contrato", self.screen.summary_label.cget("text"))


if __name__ == "__main__":
    unittest.main()
