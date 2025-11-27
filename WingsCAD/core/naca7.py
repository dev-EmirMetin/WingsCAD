# core/naca7.py

from dataclasses import dataclass
import numpy as np
from .naca4 import generate_naca4_full  # 4-digit geometrisini kullanacağız


@dataclass
class NACA7Params:
    code: str      # e.g. "7120" (biz 4-haneli kısma bakıyoruz)
    base4: str     # 4-digit'e dönüştürdüğümüz kısım
    chord: float = 1.0


def parse_naca7(code: str, chord: float = 1.0) -> NACA7Params:
    """
    ÇOK ÖNEMLİ:
      Gerçek NACA 7-serisi analitik tanımı şu an uygulanmıyor.
      Burada sadece bir 'etiket' olarak 7 kullanıyoruz ve son 4 haneyi
      NACA 4-digit kodu gibi yorumluyoruz.

    Örnek:
        7412  ->  4-digit eşleniği: 412  (tam 4 hane istiyorsan 7412 yaz)
        7120  -> "120" vs. yerine en doğrusu 7 + 4-digit yazmak.

    Pratikte:
      WingsCAD içinde NACA 7 seçtiğinde, girdiğin kodun son 4 hanesi
      NACA 4-digit formülüne gönderilir ve geometri ondan gelir.
    """
    s = code.strip()
    if len(s) < 4 or not s.isdigit():
        raise ValueError("NACA 7-series: en az 4 haneli numeric kod bekleniyor, örn. '7412'.")

    if s[0] != "7":
        raise ValueError("NACA 7-series kodu 7 ile başlamalı.")

    base4 = s[1:]           # ilk 7'den sonrası 4-digit gibi
    if len(base4) != 4:
        raise ValueError("Şimdilik '7' + 4-digit formatı destekleniyor, örn. 7412, 7309 vb.")

    return NACA7Params(code=s, base4=base4, chord=chord)


def generate_naca7_full(code: str,
                        chord: float = 1.0,
                        n_points: int = 200,
                        spacing: str = "cosine"):
    """
    NACA 7-seri placeholder:
      - Gerçek 7-seri değil.
      - Son 4 hane NACA 4-digit motoruna gönderilir (camber & thickness oradan gelir).
    """
    params = parse_naca7(code, chord=chord)
    x_loop, y_loop, x_c, yc, metrics4 = generate_naca4_full(
        params.base4,
        chord=chord,
        n_points=n_points,
        spacing=spacing,
    )

    # 7 etiketiyle yeni metrics üretelim
    metrics = dict(metrics4)
    metrics["code"] = params.code
    metrics["note"] = "Geometry generated using NACA 4-digit equivalent of 7-series code."

    return x_loop, y_loop, x_c, yc, metrics
