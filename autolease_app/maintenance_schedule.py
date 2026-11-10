"""Dates for a quarterly maintenance schedule."""

from calendar import monthrange
from datetime import date


def quarterly_dates(start: date) -> tuple[date, ...]:
    dates = []
    for offset in (0, 3, 6, 9):
        year, month = divmod(start.year * 12 + start.month - 1 + offset, 12)
        if year > 9999:
            raise ValueError("La fecha es demasiado lejana para programar un año de mantenimientos.")
        month += 1
        dates.append(date(year, month, min(start.day, monthrange(year, month)[1])))
    return tuple(dates)
