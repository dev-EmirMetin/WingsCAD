# core/naca5.py

from dataclasses import dataclass
import numpy as np
import math


@dataclass
class NACA5Params:
    code: str        # e.g. "23012"
    L: int           # camber parameter
    P: int           # max camber position parameter
    Q: int           # 0: standard, 1: reflex
    t: float         # thickness (fraction of chord)
    chord: float = 1.0


def parse_naca5(code: str, chord: float = 1.0) -> NACA5Params:
    """
    Parse a NACA 5-digit code like '23012' into geometric parameters.
    Format: LPQTT (L,P,Q,T,T all digits).
    """
    code = code.strip()
    if len(code) != 5 or not code.isdigit():
        raise ValueError("NACA 5-digit code must be 5 digits, e.g. '23012'.")

    L = int(code[0])
    P = int(code[1])
    Q = int(code[2])
    t = int(code[3:]) / 100.0

    if Q not in (0, 1):
        raise ValueError("Third digit (Q) must be 0 (standard) or 1 (reflex).")

    return NACA5Params(code=code, L=L, P=P, Q=Q, t=t, chord=chord)


def _compute_r_standard(xmc: float, tol: float = 1e-6, max_iter: int = 1000) -> float:
    """
    Solve x_mc = r * (1 - sqrt(r/3)) for r (standard, non-reflex case).
    Fixed point iteration as in ITU/Abbott. :contentReference[oaicite:1]{index=1}
    """
    r_old = 0.1
    diff = 1.0
    it = 0
    while diff > tol and it < max_iter:
        r = xmc + r_old * math.sqrt(r_old / 3.0)
        diff = abs(r - r_old)
        r_old = r
        it += 1
    return r_old


def _compute_k1_standard(L: int, r: float) -> float:
    """
    k1 for standard 5-digit camber line.
    C_li = 0.15 * L, and N(r) as in ITU notes. :contentReference[oaicite:2]{index=2}
    """
    cli = 0.15 * L
    # N(r)
    N = ((3 * r - 7 * r**2 + 8 * r**3 - 4 * r**4) / math.sqrt(r - r**2)
         - 1.5 * (1 - 2 * r) * (math.pi / 2 - math.asin(1 - 2 * r)))
    k1 = 6.0 * cli / N
    return k1


def generate_geometry(params: NACA5Params,
                      n_points: int = 200,
                      spacing: str = "cosine"):
    """
    Generate NACA 5-digit airfoil geometry (standard camber Q=0 only).

    Returns:
        x_loop, y_loop : closed loop coordinates (upper TE->LE, lower LE->TE)
        x_c, y_c       : camber line coordinates
        x_raw, yt      : base x and thickness distribution (for analysis)
    """
    if params.Q == 1:
        raise NotImplementedError(
            "Reflexed NACA 5-digit (Q=1) not implemented yet."
        )

    L, P, t, c = params.L, params.P, params.t, params.chord

    # ---- x distribution ----
    if spacing == "cosine":
        beta = np.linspace(0.0, np.pi, n_points)
        x = (1.0 - np.cos(beta)) / 2.0   # 0..1
    elif spacing == "linear":
        x = np.linspace(0.0, 1.0, n_points)
    else:
        raise ValueError("spacing must be 'cosine' or 'linear'.")

    # ---- thickness distribution (same as 4-digit) ----
    yt = 5 * t * (
        0.2969 * np.sqrt(x)
        - 0.1260 * x
        - 0.3516 * x**2
        + 0.2843 * x**3
        - 0.1015 * x**4
    )

    # ---- camber line (standard, Q=0) ----
    xmc = 0.05 * P   # position of max camber
    r = _compute_r_standard(xmc)
    k1 = _compute_k1_standard(L, r)

    yc = np.zeros_like(x)
    dyc_dx = np.zeros_like(x)

    for i, xi in enumerate(x):
        if xi < r:
            yc[i] = (k1 / 6.0) * (
                xi**3 - 3 * r * xi**2 + r**2 * (3 - r) * xi
            )
            dyc_dx[i] = (k1 / 6.0) * (
                3 * xi**2 - 6 * r * xi + r**2 * (3 - r)
            )
        else:
            yc[i] = (k1 * r**3 / 6.0) * (1 - xi)
            dyc_dx[i] = -(k1 * r**3 / 6.0)

    theta = np.arctan(dyc_dx)

    # upper / lower surfaces
    xu = x - yt * np.sin(theta)
    yu = yc + yt * np.cos(theta)
    xl = x + yt * np.sin(theta)
    yl = yc - yt * np.cos(theta)

    # closed loop: upper TE->LE, lower LE->TE
    x_loop = np.concatenate([xu[::-1], xl[1:]])
    y_loop = np.concatenate([yu[::-1], yl[1:]])

    # scale chord only in x (y in chord units, t/c remains same)
    x_loop *= c
    x_c = x * c

    return x_loop, y_loop, x_c, yc, x, yt


def compute_metrics(params: NACA5Params,
                    x_loop: np.ndarray,
                    y_loop: np.ndarray,
                    x: np.ndarray,
                    yc: np.ndarray,
                    yt: np.ndarray):
    """
    Basic geometric metrics for NACA 5-digit.
    """
    max_thickness = np.max(2 * yt) * params.chord
    max_camber = np.max(np.abs(yc)) * params.chord

    area = 0.5 * np.abs(
        np.dot(x_loop, np.roll(y_loop, -1))
        - np.dot(y_loop, np.roll(x_loop, -1))
    )

    r_le = 1.1019 * (params.t ** 2) * params.chord

    return {
        "code": params.code,
        "L": params.L,
        "P": params.P,
        "Q": params.Q,
        "t": params.t,
        "chord": params.chord,
        "max_thickness": max_thickness,
        "max_camber": max_camber,
        "area": area,
        "leading_edge_radius": r_le,
    }


def generate_naca5_full(code: str,
                        chord: float = 1.0,
                        n_points: int = 200,
                        spacing: str = "cosine"):
    """
    Convenience: tek çağrıda hem geometriyi hem metrikleri döndürür.

    Returns:
        x_loop, y_loop, x_c, yc, metrics_dict
    """
    params = parse_naca5(code, chord=chord)
    x_loop, y_loop, x_c, yc, x_raw, yt = generate_geometry(
        params,
        n_points=n_points,
        spacing=spacing,
    )
    metrics = compute_metrics(params, x_loop, y_loop, x_raw, yc, yt)
    return x_loop, y_loop, x_c, yc, metrics
