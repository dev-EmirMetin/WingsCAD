# core/naca6.py

from dataclasses import dataclass
import numpy as np


@dataclass
class NACA6Params:
    code: str              # e.g. "63-018" veya "65-415"
    pos_min_pressure: int  # ikinci rakam (x/c * 10)
    design_cl: float       # tasarım Cl
    thickness: float       # t/c
    chord: float = 1.0


def parse_naca6(code: str, chord: float = 1.0) -> NACA6Params:
    """
    Basitleştirilmiş NACA 6-serisi parser'ı.

    Format (şu an desteklenen):
        6x-abc
        x  : min. basınç yeri (x/c * 10)
        a  : design Cl * 10
        bc : kalınlık %c

    Örnekler:
        63-018  (x/c~0.3, Cl=0.0, t/c=0.18)
        65-415  (x/c~0.5, Cl=0.4, t/c=0.15)  <-- geometri hala simetrik üretilecek.
    """
    code = code.strip()

    if len(code) != 6 or code[0] != "6" or code[2] != "-":
        raise ValueError("NACA 6-series format: e.g. '63-018', '65-415'.")

    pos_min = int(code[1])
    cl_digit = int(code[3])
    t = int(code[4:]) / 100.0

    design_cl = cl_digit / 10.0

    return NACA6Params(
        code=code,
        pos_min_pressure=pos_min,
        design_cl=design_cl,
        thickness=t,
        chord=chord,
    )


def generate_geometry(params: NACA6Params,
                      n_points: int = 200,
                      spacing: str = "cosine"):
    """
    Basitleştirilmiş NACA 6-serisi geometri üretimi.

    ÖNEMLİ:
      - Camber line şu an 0, yani profil simetrik.
      - Kalınlık dağılımı klasik NACA 00xx polinomu ile hesaplanıyor.
      - design_cl ve pos_min_pressure sadece metriklerde saklanıyor.

    Bu, gerçek 6-seri laminar profilleriyle bire bir aynı DEĞİLDİR;
    ancak aynı t/c'ye sahip, simetrik, düzgün bir airfoil verir.
    """
    t = params.thickness
    c = params.chord

    # ---- x dağılımı ----
    if spacing == "cosine":
        beta = np.linspace(0.0, np.pi, n_points)
        x = (1.0 - np.cos(beta)) / 2.0   # 0..1
    elif spacing == "linear":
        x = np.linspace(0.0, 1.0, n_points)
    else:
        raise ValueError("spacing must be 'cosine' or 'linear'.")

    # ---- kalınlık dağılımı (4-digit 00xx formülü) ----
    yt = 5 * t * (
        0.2969 * np.sqrt(x)
        - 0.1260 * x
        - 0.3516 * x**2
        + 0.2843 * x**3
        - 0.1015 * x**4
    )

    yc = np.zeros_like(x)   # simetrik
    # üst/alt yüzey
    xu = x
    yu = yt
    xl = x
    yl = -yt

    # kapalı loop
    x_loop = np.concatenate([xu[::-1], xl[1:]])
    y_loop = np.concatenate([yu[::-1], yl[1:]])

    # chord ile ölçekle
    x_loop *= c
    x_c = x * c

    return x_loop, y_loop, x_c, yc, x, yt


def compute_metrics(params: NACA6Params,
                    x_loop: np.ndarray,
                    y_loop: np.ndarray,
                    x: np.ndarray,
                    yc: np.ndarray,
                    yt: np.ndarray):
    max_thickness = np.max(2 * yt) * params.chord
    max_camber = np.max(np.abs(yc)) * params.chord

    area = 0.5 * np.abs(
        np.dot(x_loop, np.roll(y_loop, -1))
        - np.dot(y_loop, np.roll(x_loop, -1))
    )

    r_le = 1.1019 * (params.thickness ** 2) * params.chord

    return {
        "code": params.code,
        "pos_min_pressure": params.pos_min_pressure,
        "design_cl": params.design_cl,
        "thickness": params.thickness,
        "chord": params.chord,
        "max_thickness": max_thickness,
        "max_camber": max_camber,
        "area": area,
        "leading_edge_radius": r_le,
    }


def generate_naca6_full(code: str,
                        chord: float = 1.0,
                        n_points: int = 200,
                        spacing: str = "cosine"):
    params = parse_naca6(code, chord=chord)
    x_loop, y_loop, x_c, yc, x_raw, yt = generate_geometry(
        params,
        n_points=n_points,
        spacing=spacing,
    )
    metrics = compute_metrics(params, x_loop, y_loop, x_raw, yc, yt)
    return x_loop, y_loop, x_c, yc, metrics
