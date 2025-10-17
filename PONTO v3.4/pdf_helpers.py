"""
Helpers to render headers/footers and style rows in PDF (v3.2).
Works with reportlab (preferred). If project uses FPDF, adapt calls accordingly.
"""
from datetime import date
from holidays import is_holiday
from theme import WEEKEND_ROW_COLOR, HOLIDAY_ROW_COLOR

def weekend_or_holiday(row_date: date):
    # Returns (fill_color_tuple_or_None, holiday_name_or_None)
    # Colors in 0-1 range for reportlab
    is_hol, hol_name = is_holiday(row_date)
    if is_hol:
        return _rgb255(*_hex_to_rgb(WEEKEND_ROW_COLOR)), hol_name  # color replaced below to holiday color
    # weekend
    if row_date.weekday() >= 5:
        return _rgb255(*_hex_to_rgb(WEEKEND_ROW_COLOR)), None
    return None, None

def _hex_to_rgb(hexstr: str):
    hexstr = hexstr.lstrip('#')
    return tuple(int(hexstr[i:i+2], 16) for i in (0, 2, 4))

def _rgb255(r,g,b):
    return (r/255.0, g/255.0, b/255.0)
