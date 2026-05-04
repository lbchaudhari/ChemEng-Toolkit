"""Thermodynamics calculations."""
from __future__ import annotations
import math

R_GAS = 8.314462618  # J/(mol·K)


def _r(value, unit, label):
    return {"label": label, "value": value, "unit": unit}


def ideal_gas(inp):
    """Solve PV = nRT for the missing variable (set the unknown to 0)."""
    P = float(inp.get("P") or 0)   # Pa
    V = float(inp.get("V") or 0)   # m³
    n = float(inp.get("n") or 0)   # mol
    T = float(inp.get("T") or 0)   # K
    unknowns = sum(1 for x in (P, V, n, T) if x == 0)
    if unknowns != 1:
        raise ValueError("Leave exactly ONE field as 0; the others must be filled.")
    if P == 0:
        P = n * R_GAS * T / V
        out = _r(round(P, 4), "Pa", "Pressure P")
    elif V == 0:
        V = n * R_GAS * T / P
        out = _r(round(V, 6), "m³", "Volume V")
    elif n == 0:
        n = P * V / (R_GAS * T)
        out = _r(round(n, 6), "mol", "Moles n")
    else:
        T = P * V / (n * R_GAS)
        out = _r(round(T, 4), "K", "Temperature T")
    return {
        "results": [
            out,
            _r(round(P, 2), "Pa", "P"),
            _r(round(V, 6), "m³", "V"),
            _r(round(n, 6), "mol", "n"),
            _r(round(T, 3), "K", "T"),
        ],
        "notes": ["P·V = n·R·T,  R = 8.314 J/(mol·K)"],
    }


def antoine_vapor_pressure(inp):
    """log10(P_mmHg) = A - B / (T_C + C). Returns P at given T."""
    A = float(inp["A"])
    B = float(inp["B"])
    C = float(inp["C"])
    T = float(inp["T"])  # °C
    log10P = A - B / (T + C)
    P_mmHg = 10 ** log10P
    P_Pa   = P_mmHg * 133.322
    return {
        "results": [
            _r(round(P_mmHg, 4), "mmHg", "Vapor pressure P"),
            _r(round(P_Pa, 2), "Pa", "Vapor pressure P"),
            _r(round(P_Pa / 1000.0, 4), "kPa", "Vapor pressure P"),
            _r(round(P_Pa / 101325.0, 5), "atm", "Vapor pressure P"),
        ],
        "notes": [
            "Antoine: log10(P) = A - B/(T + C)",
            "Make sure A, B, C correspond to the units used (mmHg & °C here).",
        ],
    }


def compressibility_redlich_kwong(inp):
    """Redlich–Kwong cubic EoS — returns Z at given T, P (largest root)."""
    Tc = float(inp["Tc"])
    Pc = float(inp["Pc"])
    T  = float(inp["T"])
    P  = float(inp["P"])
    R  = R_GAS
    a = 0.42748 * R * R * Tc ** 2.5 / Pc
    b = 0.08664 * R * Tc / Pc
    A = a * P / (R ** 2 * T ** 2.5)
    B = b * P / (R * T)
    # Z^3 - Z^2 + (A - B - B^2)Z - AB = 0
    coeffs = [1.0, -1.0, A - B - B * B, -A * B]
    roots = _cubic_roots(coeffs)
    real_roots = [r for r in roots if abs(r.imag) < 1e-8 and r.real > 0]
    if not real_roots:
        raise ValueError("No physical Z root found.")
    Z = max(r.real for r in real_roots)
    Vm = Z * R * T / P
    return {
        "results": [
            _r(round(Z, 5), "-", "Compressibility Z"),
            _r(round(Vm, 6), "m³/mol", "Molar volume Vm"),
            _r(round(a, 4), "Pa·m⁶·K^0.5/mol²", "RK parameter a"),
            _r(round(b, 8), "m³/mol", "RK parameter b"),
        ],
        "notes": [
            "Redlich–Kwong: P = RT/(V-b) - a/[√T·V·(V+b)]",
            "a = 0.42748·R²·Tc^2.5/Pc,  b = 0.08664·R·Tc/Pc",
        ],
    }


def _cubic_roots(coeffs):
    """Return all 3 roots (complex) of a cubic a·x³+b·x²+c·x+d using numpy-free formula."""
    a, b, c, d = coeffs
    # Convert to depressed cubic t³ + p t + q = 0 via x = t - b/(3a)
    p = (3 * a * c - b * b) / (3 * a * a)
    q = (2 * b ** 3 - 9 * a * b * c + 27 * a * a * d) / (27 * a ** 3)
    disc = (q / 2) ** 2 + (p / 3) ** 3
    roots = []
    if disc > 0:
        s = _cbrt(-q / 2 + math.sqrt(disc))
        t = _cbrt(-q / 2 - math.sqrt(disc))
        x1 = s + t
        roots.append(complex(x1, 0))
        re = -(s + t) / 2
        im = (s - t) * math.sqrt(3) / 2
        roots.append(complex(re, im))
        roots.append(complex(re, -im))
    else:
        # three real roots via trig
        r = math.sqrt(-(p / 3) ** 3)
        phi = math.acos(max(-1.0, min(1.0, -q / (2 * r))))
        m = 2 * (-p / 3) ** 0.5
        for k in range(3):
            roots.append(complex(m * math.cos((phi + 2 * math.pi * k) / 3), 0))
    shift = b / (3 * a)
    return [complex(r.real - shift, r.imag) for r in roots]


def _cbrt(x):
    return math.copysign(abs(x) ** (1 / 3), x)


# ---------- Phase behaviour -----------------------------------------------

def clausius_clapeyron(inp):
    """Two-point Clausius–Clapeyron:
        ln(P2/P1) = −(ΔH_vap / R) · (1/T2 − 1/T1)
    Solve for any one of (P1, P2, T1, T2) given the other three and ΔH_vap.
    Leave the unknown as 0.
    """
    P1 = float(inp.get("P1") or 0)
    P2 = float(inp.get("P2") or 0)
    T1 = float(inp.get("T1") or 0)   # K
    T2 = float(inp.get("T2") or 0)   # K
    dH = float(inp["dH_vap"])        # J/mol
    R  = R_GAS

    unknowns = sum(1 for x in (P1, P2, T1, T2) if x == 0)
    if unknowns != 1:
        raise ValueError("Leave exactly ONE of P1, P2, T1, T2 as 0.")

    if P2 == 0:
        P2 = P1 * math.exp(-(dH / R) * (1 / T2 - 1 / T1))
        out = _r(round(P2, 6), "Pa", "Vapor pressure P2")
    elif P1 == 0:
        P1 = P2 / math.exp(-(dH / R) * (1 / T2 - 1 / T1))
        out = _r(round(P1, 6), "Pa", "Vapor pressure P1")
    elif T2 == 0:
        T2 = 1 / (1 / T1 - (R / dH) * math.log(P2 / P1))
        out = _r(round(T2, 4), "K", "Temperature T2")
    else:
        T1 = 1 / (1 / T2 + (R / dH) * math.log(P2 / P1))
        out = _r(round(T1, 4), "K", "Temperature T1")

    return {
        "results": [
            out,
            _r(round(P1, 4), "Pa", "P1"),
            _r(round(P2, 4), "Pa", "P2"),
            _r(round(T1, 4), "K",  "T1"),
            _r(round(T2, 4), "K",  "T2"),
            _r(round(dH / 1000, 4), "kJ/mol", "ΔH_vap"),
        ],
        "notes": [
            "ln(P₂/P₁) = −(ΔH_vap / R) · (1/T₂ − 1/T₁)",
            "Assumes ΔH_vap is constant in the temperature interval.",
            "R = 8.314 J/(mol·K).",
        ],
    }


def raoult_binary_bubble(inp):
    """Bubble pressure and vapor composition for a binary ideal mixture
    using Raoult's law: y_i·P = x_i·Pᵢˢᵃᵗ.

    Inputs: x1, P1_sat, P2_sat (Pa).
    """
    x1 = float(inp["x1"])
    P1s = float(inp["P1_sat"])
    P2s = float(inp["P2_sat"])
    if not 0 <= x1 <= 1:
        raise ValueError("x1 must be in [0, 1].")
    if min(P1s, P2s) <= 0:
        raise ValueError("Saturation pressures must be > 0.")
    x2 = 1 - x1
    P_bubble = x1 * P1s + x2 * P2s
    y1 = x1 * P1s / P_bubble
    y2 = 1 - y1
    alpha = (y1 / x1) / (y2 / x2) if (x1 > 0 and x2 > 0) else float("inf")
    return {
        "results": [
            _r(round(P_bubble, 4), "Pa", "Bubble pressure P_bub"),
            _r(round(P_bubble / 1000, 5), "kPa", "Bubble pressure"),
            _r(round(P_bubble / 101325, 6), "atm", "Bubble pressure"),
            _r(round(y1, 6), "-", "Vapor mole fraction y1"),
            _r(round(y2, 6), "-", "Vapor mole fraction y2"),
            _r(round(alpha, 4) if alpha != float("inf") else "∞",
               "-", "Relative volatility α₁₂"),
        ],
        "notes": [
            "Raoult: P = x₁·P₁ˢᵃᵗ + x₂·P₂ˢᵃᵗ",
            "y_i = x_i·P_iˢᵃᵗ / P",
            "Relative volatility α₁₂ = P₁ˢᵃᵗ / P₂ˢᵃᵗ for ideal mixtures.",
        ],
    }


def dalton_partial_pressures(inp):
    """Partial pressures of components from total pressure and mole fractions.

    Inputs: components text 'name, y' (one per line), P_total (Pa).
    """
    text = inp["components"]
    P = float(inp["P"])
    rows = []
    total_y = 0.0
    for line in text.replace(";", "\n").splitlines():
        line = line.strip().strip(",")
        if not line:
            continue
        parts = [p.strip() for p in line.split(",") if p.strip()]
        if len(parts) < 2:
            raise ValueError(f"Each line: 'name, y'. Got: '{line}'")
        name = parts[0]
        y = float(parts[1])
        if y < 0:
            raise ValueError("y must be ≥ 0.")
        rows.append((name, y))
        total_y += y
    if total_y == 0:
        raise ValueError("Sum of mole fractions is 0.")
    out = []
    for name, y in rows:
        yi = y / total_y
        pi = yi * P
        out.append(_r(round(pi, 4), "Pa", f"Partial pressure of {name}"))
        out.append(_r(round(yi, 6), "-",  f"Normalised mole fraction y of {name}"))
    out.append(_r(round(P, 4), "Pa", "Total pressure P"))
    return {
        "results": out,
        "notes": [
            "Dalton: pᵢ = yᵢ · P,  with Σyᵢ = 1.",
            "Mole fractions are normalised if they don't sum to 1.",
        ],
    }


def humidity_calc(inp):
    """Psychrometric calculations for an air–water vapour mixture.

    Inputs:
      T  - dry-bulb temperature (°C)
      P  - total pressure (Pa)
      RH - relative humidity (%) [0–100]
    Computes saturation pressure via Antoine for water and the various
    humidity definitions used in Sikdar Ch. 2.
    """
    T  = float(inp["T"])
    P  = float(inp.get("P", 101325))
    RH = float(inp["RH"]) / 100.0
    if not 0 <= RH <= 1:
        raise ValueError("RH must be 0–100 %.")
    # Antoine for water (mmHg, °C): log10(P) = 8.07131 − 1730.63/(T + 233.426)
    P_sat_mmHg = 10 ** (8.07131 - 1730.63 / (T + 233.426))
    P_sat = P_sat_mmHg * 133.322                 # Pa
    p_w   = RH * P_sat                           # partial pressure of water
    if p_w >= P:
        raise ValueError("Partial pressure exceeds total — RH too high for these conditions.")
    # Absolute (specific) humidity, kg water / kg dry air:
    H_abs = (18.015 / 28.84) * p_w / (P - p_w)
    H_sat = (18.015 / 28.84) * P_sat / (P - P_sat) if P > P_sat else float("inf")
    pct_H = (H_abs / H_sat) * 100 if H_sat != float("inf") else 0
    # Humid heat (J/kg dry air·K) ≈ Cp_air + H·Cp_water_vapour
    H_humid_heat = 1005 + H_abs * 1880
    # Humid volume (m³/kg dry air) at T, P
    Tk = T + 273.15
    H_vol = (Tk / 273.15) * (101325 / P) * (22.4e-3 / 28.84) * (1 + 28.84 / 18.015 * H_abs)
    # Dew point: T at which P_sat(T_dp) = p_w (invert Antoine)
    if p_w > 0:
        T_dp = 1730.63 / (8.07131 - math.log10(p_w / 133.322)) - 233.426
    else:
        T_dp = float("-inf")
    return {
        "results": [
            _r(round(P_sat, 4), "Pa", "Saturation P of water at T"),
            _r(round(p_w, 4), "Pa",   "Partial pressure of water"),
            _r(round(RH * 100, 4), "%", "Relative humidity"),
            _r(round(H_abs, 6), "kg/kg dry air", "Absolute (specific) humidity"),
            _r(round(H_sat, 6) if H_sat != float("inf") else "∞",
               "kg/kg dry air", "Saturated humidity"),
            _r(round(pct_H, 4), "%", "Percentage humidity"),
            _r(round(H_humid_heat, 3), "J/kg dry air·K", "Humid heat"),
            _r(round(H_vol, 5), "m³/kg dry air", "Humid volume"),
            _r(round(T_dp, 3) if T_dp != float("-inf") else "—", "°C", "Dew point"),
        ],
        "notes": [
            "Antoine (water, mmHg, °C): log₁₀P = 8.07131 − 1730.63/(T + 233.426).",
            "Absolute humidity H = (MW_w/MW_air)·p_w/(P − p_w).",
            "Percentage humidity = H / H_sat · 100  (≠ relative humidity in general).",
            "Humid heat ≈ 1005 + 1880·H  J/(kg dry air·K).",
        ],
    }
