"""
Excel export (v3.2) using openpyxl via pandas if available; falls back to openpyxl workbook.
Expected input: list of dicts or list of tuples with headers.
"""
from typing import List, Dict, Any
import datetime

def export_to_excel(rows: List[Dict[str, Any]], filepath: str, headers_order: list[str] | None = None):
    try:
        import pandas as pd
        if not rows:
            # create empty sheet with headers if provided
            if headers_order:
                df = pd.DataFrame(columns=headers_order)
            else:
                df = pd.DataFrame()
        else:
            df = pd.DataFrame(rows)
            if headers_order:
                df = df.reindex(columns=headers_order)
        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Relatorio")
    except Exception:
        # Fallback openpyxl only
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Relatorio"
        if not rows:
            # headers only
            if headers_order:
                ws.append(headers_order)
        else:
            headers = headers_order or list(rows[0].keys())
            ws.append(headers)
            for r in rows:
                ws.append([r.get(h, "") for h in headers])
        wb.save(filepath)
