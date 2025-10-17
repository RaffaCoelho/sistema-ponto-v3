from dataclasses import dataclass
from datetime import date
from typing import Optional, Iterable, Dict, Any, List

@dataclass
class ReportFilter:
    nome: Optional[str] = None
    setor: Optional[str] = None
    lotacao: Optional[str] = None
    data_ini: Optional[date] = None
    data_fim: Optional[date] = None

def normalize(s: Optional[str]) -> Optional[str]:
    return s.strip().lower() if isinstance(s, str) else None

def apply_filters(rows: Iterable[Dict[str, Any]], f: ReportFilter) -> List[Dict[str, Any]]:
    nn = normalize(f.nome)
    ns = normalize(f.setor)
    nl = normalize(f.lotacao)
    out = []
    for r in rows:
        rn = normalize(str(r.get("nome", "")))
        rs = normalize(str(r.get("setor", "")))
        rl = normalize(str(r.get("lotacao", "")))
        rd = r.get("data")
        ok = True
        if nn and nn not in (rn or ""):
            ok = False
        if ns and ns not in (rs or ""):
            ok = False
        if nl and nl not in (rl or ""):
            ok = False
        if f.data_ini and isinstance(rd, (date,)) and rd < f.data_ini:
            ok = False
        if f.data_fim and isinstance(rd, (date,)) and rd > f.data_fim:
            ok = False
        if ok:
            out.append(r)
    return out
