import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from telegram_bot import _get_due_reminder_notifications


class FakeReminder:
    def __init__(self, fecha, status="pendiente"):
        self.fecha = fecha
        self.status = status


def test_get_due_reminder_notifications_returns_today_and_tomorrow_only():
    now = datetime(2026, 7, 8, 8, 55, 0)
    reminders = [
        FakeReminder(datetime(2026, 7, 8, 9, 0, 0)),
        FakeReminder(datetime(2026, 7, 9, 9, 0, 0)),
        FakeReminder(datetime(2026, 7, 10, 9, 0, 0)),
        FakeReminder(datetime(2026, 7, 8, 9, 0, 0), status="notificado"),
    ]

    due = _get_due_reminder_notifications(reminders, now=now)

    assert len(due) == 2
    assert due[0][1] == "hoy"
    assert due[1][1] == "mañana"


def test_get_due_reminder_notifications_includes_pre_alert_window():
    now = datetime(2026, 7, 8, 12, 0, 0)
    reminder = FakeReminder(datetime(2026, 7, 8, 12, 5, 0))

    due = _get_due_reminder_notifications([reminder], now=now)

    assert len(due) == 1
    assert due[0][1] == "hoy"
