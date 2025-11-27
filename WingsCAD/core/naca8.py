# core/naca8.py

from dataclasses import dataclass
import numpy as np
from .naca4 import generate_naca4_full


@dataclass
class NACA8Params:
    code: str
    base4: str
    chord: float = 1.0


def parse_naca8(code: str, chord: float = 1.0) -> NACA8Params:
    """
    NACA 8-seri için de şu an gerçek analitik tanım yok;
    7-seri ile aynı mantık: '8' etiketi + 4-digit eşleniği.

    Örnek:
        8412 -> 4-digit eşleniği: 412  (7-serideki gibi)
    """
    s = code.strip()
    if len(s) < 4 or not s.isdigit():
        raise ValueError("NACA 8-series: en az 4 haneli numeric kod bekleniyor, örn. '8412'.")

    if s[0] != "8":
        raise ValueError("NACA 8-series kodu 8 ile başlamalı.")

    base4 = s[1:]
    if len(base4) != 4:
        raise ValueError("Şimdilik '8' + 4-digit formatı destekleniyor, örn. 8412, 8309 vb.")

    return NACA8Params(code=s, base4=base4, chord=chord)


def generate_naca8_full(code: str,
                        chord: float = 1.0,
                        n_points: int = 200,
                        spacing: str = "cosine"):
    params = parse_naca8(code, chord=chord)
    x_loop, y_loop, x_c, yc, metrics4 = generate_naca4_full(
        params.base4,
        chord=chord,
        n_points=n_points,
        spacing=spacing,
    )

    metrics = dict(metrics4)
    metrics["code"] = params.code
    metrics["note"] = "Geometry generated using NACA 4-digit equivalent of 8-series code."

    return x_loop, y_loop, x_c, yc, metrics
