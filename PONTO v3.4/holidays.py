from datetime import date

# Simplified list of national fixed holidays (BR). Extend as needed.
FIXED_HOLIDAYS = {
    (1, 1): "Confraternização Universal",
    (4, 21): "Tiradentes",
    (5, 1): "Dia do Trabalho",
    (9, 7): "Independência do Brasil",
    (10, 12): "Nossa Senhora Aparecida",
    (11, 2): "Finados",
    (11, 15): "Proclamação da República",
    (12, 25): "Natal",
}

def is_holiday(d: date):
    """Return (is_holiday: bool, name: str|None)."""
    name = FIXED_HOLIDAYS.get((d.month, d.day))
    if name:
        return True, name
    return False, None
