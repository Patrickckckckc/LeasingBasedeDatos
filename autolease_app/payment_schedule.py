"""Payment schedule calculations used by the payments screen."""

from calendar import monthrange
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Contract:
    contract_id: int
    client: str
    start: date
    end: date
    installment: Decimal
    vehicle_price: Decimal


@dataclass(frozen=True)
class Payment:
    payment_id: int
    contract_id: int
    amount: Decimal
    payment_date: date
    method: str
    status: str


@dataclass(frozen=True)
class PaymentRow:
    contract: Contract
    payment_date: date
    amount: Decimal
    status: str
    payment: Payment | None


def payment_status(status: str, payment_date: date, today: date) -> str:
    normalized = status.strip().casefold()
    if normalized == "pagado":
        return "Pagado"
    if normalized in {"pendiente", "atrasado"}:
        return "Atrasado" if payment_date < today else "Pendiente"
    return status


def scheduled_dates(start: date, end: date):
    month_offset = 0
    while True:
        month_index = start.year * 12 + start.month - 1 + month_offset
        year, month = divmod(month_index, 12)
        if year > 9999:
            break
        month += 1
        due_date = date(year, month, min(start.day, monthrange(year, month)[1]))
        if due_date >= end:
            break
        yield due_date
        month_offset += 1


def build_payment_rows(
    contracts: list[Contract], payments: list[Payment], today: date
) -> list[PaymentRow]:
    by_contract: dict[int, list[Payment]] = {}
    for payment in payments:
        by_contract.setdefault(payment.contract_id, []).append(payment)

    rows = []
    for contract in contracts:
        contract_payments = by_contract.get(contract.contract_id, [])
        recorded_dates = {payment.payment_date for payment in contract_payments}
        for payment in contract_payments:
            rows.append(PaymentRow(
                contract, payment.payment_date, payment.amount,
                payment_status(payment.status, payment.payment_date, today), payment,
            ))
        for due_date in scheduled_dates(contract.start, contract.end):
            if due_date not in recorded_dates:
                rows.append(PaymentRow(
                    contract, due_date, contract.installment,
                    payment_status("Pendiente", due_date, today), None,
                ))
    return sorted(
        rows,
        key=lambda row: (
            row.contract.contract_id, row.payment_date,
            row.payment.payment_id if row.payment else 0,
        ),
    )


def paid_total(contract_id: int, payments: list[Payment]) -> Decimal:
    return sum(
        (payment.amount for payment in payments
         if payment.contract_id == contract_id and payment.status.strip().casefold() == "pagado"),
        Decimal("0"),
    )
