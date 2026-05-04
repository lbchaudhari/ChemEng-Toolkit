"""Mass transfer / distillation calculations."""
from __future__ import annotations
import math


def _r(value, unit, label):
    return {"label": label, "value": value, "unit": unit}


def fenske_min_stages(inp):
    """Minimum equilibrium stages at total reflux (Fenske)."""
    xD = float(inp["xD"])
    xB = float(inp["xB"])
    alpha = float(inp["alpha"])
    if not (0 < xD < 1 and 0 < xB < 1):
        raise ValueError("Compositions must be between 0 and 1.")
    if alpha <= 1:
        raise ValueError("Relative volatility α must be > 1.")
    num = math.log((xD / (1 - xD)) * ((1 - xB) / xB))
    den = math.log(alpha)
    nmin = num / den
    return {
        "results": [
            _r(round(nmin, 3), "stages", "N_min (incl. reboiler)"),
            _r(round(max(nmin - 1, 0), 3), "stages", "N_min (excl. reboiler)"),
        ],
        "notes": [
            "N_min = log[(xD/(1-xD))·((1-xB)/xB)] / log(α)",
            "Fenske eq. assumes constant relative volatility.",
        ],
    }


def underwood_min_reflux(inp):
    """Underwood minimum reflux for a binary feed at its bubble point (q=1)."""
    xF = float(inp["xF"])
    xD = float(inp["xD"])
    alpha = float(inp["alpha"])
    q = float(inp.get("q", 1.0))
    if not 0 < xF < 1:
        raise ValueError("xF must be between 0 and 1.")
    if alpha <= 1:
        raise ValueError("α must be > 1.")
    # Solve Underwood θ for binary: α·xF/(α-θ) + (1-xF)/(1-θ) = 1 - q
    # For q = 1 (saturated liquid feed): θ between 1 and α
    if abs(q - 1.0) < 1e-6:
        # bisection for theta in (1, alpha)
        def f(theta):
            return alpha * xF / (alpha - theta) + (1 - xF) / (1 - theta) - (1 - q)
        lo, hi = 1.0 + 1e-6, alpha - 1e-6
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            if f(mid) > 0:
                lo = mid
            else:
                hi = mid
        theta = 0.5 * (lo + hi)
    else:
        # general: search in (1, alpha)
        def f(theta):
            return alpha * xF / (alpha - theta) + (1 - xF) / (1 - theta) - (1 - q)
        lo, hi = 1.0 + 1e-6, alpha - 1e-6
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            if f(mid) * f(lo) < 0:
                hi = mid
            else:
                lo = mid
        theta = 0.5 * (lo + hi)

    Rmin_plus_1 = alpha * xD / (alpha - theta) + (1 - xD) / (1 - theta)
    Rmin = Rmin_plus_1 - 1
    return {
        "results": [
            _r(round(theta, 4), "-", "Underwood θ"),
            _r(round(Rmin, 4), "-", "Minimum reflux R_min"),
            _r(round(1.3 * Rmin, 4), "-", "Suggested R (1.3·R_min)"),
        ],
        "notes": [
            "Σ α_i·x_iF / (α_i - θ) = 1 - q",
            "R_min + 1 = Σ α_i·x_iD / (α_i - θ)",
        ],
    }


def kremser_absorption(inp):
    """Kremser equation for dilute counter-current absorption."""
    A   = float(inp["A"])      # absorption factor L/(m·G)
    yin = float(inp["yin"])
    yout = float(inp["yout"])
    xin = float(inp.get("xin", 0.0))
    m   = float(inp.get("m", 1.0))
    if A <= 0 or A == 1.0:
        raise ValueError("A must be > 0 and ≠ 1.")
    y_star_in = m * xin
    num = (yin - y_star_in) / (yout - y_star_in)
    n = math.log(num * (1 - 1 / A) + 1 / A) / math.log(A)
    return {
        "results": [
            _r(round(n, 3), "stages", "Theoretical stages N"),
            _r(round(num, 3), "-", "(yin - m·xin)/(yout - m·xin)"),
        ],
        "notes": [
            "N = ln[((yin - m·xin)/(yout - m·xin))·(1 - 1/A) + 1/A] / ln(A)",
            "A = L / (m·G)",
        ],
    }


def souders_brown_diameter(inp):
    """Tray-column diameter from Souders-Brown / F-factor (Branan, Fractionators).

        v_max = K · √[(ρ_L − ρ_V) / ρ_V]
        A = (ṁ_V / ρ_V) / v_max,    D = √(4A/π)
    """
    rho_L = float(inp["rho_L"])
    rho_V = float(inp["rho_V"])
    m_V   = float(inp["m_V"])     # kg/s vapour mass flow
    K     = float(inp.get("K", 0.055))   # m/s, Souders-Brown coefficient
    eta   = float(inp.get("eta", 0.80))  # design fraction of flooding
    if rho_L <= rho_V:
        raise ValueError("ρ_L must be > ρ_V.")
    v_flood = K * math.sqrt((rho_L - rho_V) / rho_V)
    v_des   = eta * v_flood
    Q_V = m_V / rho_V                       # m³/s
    A   = Q_V / v_des
    D   = math.sqrt(4 * A / math.pi)
    return {
        "results": [
            _r(round(v_flood, 4), "m/s", "Flooding vapour velocity v_flood"),
            _r(round(v_des, 4), "m/s",   "Design vapour velocity v_des"),
            _r(round(A, 5), "m²",        "Cross-sectional area A"),
            _r(round(D, 4), "m",         "Column diameter D"),
            _r(round(Q_V, 5), "m³/s",    "Vapour volumetric flow"),
        ],
        "notes": [
            "Souders–Brown: v_flood = K·√[(ρ_L − ρ_V)/ρ_V]",
            "K ≈ 0.04–0.10 m/s for sieve/valve trays at 24-in. spacing.",
            "Design typically 75–85 % of flooding; here η = " + f"{eta:.2f}",
        ],
    }