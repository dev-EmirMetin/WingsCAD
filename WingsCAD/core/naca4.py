# core/naca4.py

from dataclasses import dataclass
import numpy as np


@dataclass
class NACA4Params:
    code: str        # e.g. "2412"
    m: float         # max camber (fraction of chord)
    p: float         # location of max camber (fraction of chord)
    t: float         # thickness (fraction of chord)
    chord: float = 1.0


def parse_naca4(code: str, chord: float = 1.0) -> NACA4Params:
    """
    Parse a NACA 4-digit code like '2412' into geometric parameters.
    """
    code = code.strip()
    if len(code) != 4 or not code.isdigit():
        raise ValueError("NACA 4-digit code must be 4 digits, e.g. '2412'.")

    m = int(code[0]) / 100.0      # max camber
    p = int(code[1]) / 10.0       # location of max camber
    t = int(code[2:]) / 100.0     # thickness

    return NACA4Params(code=code, m=m, p=p, t=t, chord=chord)


def generate_geometry(params: NACA4Params,
                      n_points: int = 200,
                      spacing: str = "cosine"):
    """
    Generate NACA 4-digit airfoil geometry.

    Returns:
        x_loop, y_loop : closed loop coordinates (upper TE->LE, lower LE->TE)
        x_c, y_c       : camber line coordinates
        x_raw, yt      : base x and thickness distribution (for analysis)
    """
    m, p, t, c = params.m, params.p, params.t, params.chord

    # ---- x dağılımı ----
    if spacing == "cosine":
        beta = np.linspace(0.0, np.pi, n_points)
        x = (1.0 - np.cos(beta)) / 2.0
    elif spacing == "linear":
        x = np.linspace(0.0, 1.0, n_points)
    else:
        raise ValueError("spacing must be 'cosine' or 'linear'.")

    # ---- thickness distribution (standard NACA 4 form) ----
    yt = 5 * t * (
        0.2969 * np.sqrt(x)
        - 0.1260 * x
        - 0.3516 * x**2
        + 0.2843 * x**3
        - 0.1015 * x**4
    )

    # ---- camber line & derivative ----
    yc = np.zeros_like(x)
    dyc_dx = np.zeros_like(x)

    if p == 0:
        # symmetric NACA 00xx
        yc[:] = 0.0
        dyc_dx[:] = 0.0
    else:
        for i, xi in enumerate(x):
            if xi < p:
                yc[i] = m / p**2 * (2 * p * xi - xi**2)
                dyc_dx[i] = 2 * m / p**2 * (p - xi)
            else:
                yc[i] = m / (1 - p)**2 * ((1 - 2 * p) + 2 * p * xi - xi**2)
                dyc_dx[i] = 2 * m / (1 - p)**2 * (p - xi)

    theta = np.arctan(dyc_dx)

    # ---- upper / lower surfaces ----
    xu = x - yt * np.sin(theta)
    yu = yc + yt * np.cos(theta)
    xl = x + yt * np.sin(theta)
    yl = yc - yt * np.cos(theta)

    # closed loop: upper TE->LE, lower LE->TE
    x_loop = np.concatenate([xu[::-1], xl[1:]])
    y_loop = np.concatenate([yu[::-1], yl[1:]])

    # scale by chord
    x_loop *= c
    x_c = x * c  # camber line x

    return x_loop, y_loop, x_c, yc, x, yt


def compute_metrics(params: NACA4Params,
                    x_loop: np.ndarray,
                    y_loop: np.ndarray,
                    x: np.ndarray,
                    yc: np.ndarray,
                    yt: np.ndarray):
    """
    Compute some basic geometric metrics for the airfoil.
    Returns a dict with useful scalars.
    """
    # max thickness (absolute)
    max_thickness = np.max(2 * yt) * params.chord  # upper-lower thickness

    # max camber (absolute)
    max_camber = np.max(np.abs(yc)) * params.chord

    # area (shoelace formula), chord-normalized
    area = 0.5 * np.abs(np.dot(x_loop, np.roll(y_loop, -1)) -
                        np.dot(y_loop, np.roll(x_loop, -1)))

    # approximate leading-edge radius (classical NACA formula)
    # r_le = 1.1019 * t^2 * c
    r_le = 1.1019 * (params.t ** 2) * params.chord

    return {
        "code": params.code,
        "m": params.m,
        "p": params.p,
        "t": params.t,
        "chord": params.chord,
        "max_thickness": max_thickness,
        "max_camber": max_camber,
        "area": area,
        "leading_edge_radius": r_le,
    }


def generate_naca4_full(code: str,
                        chord: float = 1.0,
                        n_points: int = 200,
                        spacing: str = "cosine"):
    """
    Convenience: tek çağrıda hem geometriyi hem metrikleri döndürür.

    Returns:
        x_loop, y_loop, x_c, yc, metrics_dict
    """
    params = parse_naca4(code, chord=chord)
    x_loop, y_loop, x_c, yc, x_raw, yt = generate_geometry(
        params,
        n_points=n_points,
        spacing=spacing,
    )
    metrics = compute_metrics(params, x_loop, y_loop, x_raw, yc, yt)
    return x_loop, y_loop, x_c, yc, metrics
