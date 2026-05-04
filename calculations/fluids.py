"""Fluid mechanics calculations."""
from __future__ import annotations
import math


def _r(value, unit, label):
    return {"label": label, "value": value, "unit": unit}


def reynolds(inp):
    rho = float(inp["rho"])
    v   = float(inp["v"])
    d   = float(inp["d"])
    mu  = float(inp["mu"])
    if mu <= 0:
        raise ValueError("Viscosity must be > 0")
    re = rho * v * d / mu
    if re < 2300:
        regime = "Laminar (Re < 2300)"
    elif re < 4000:
        regime = "Transitional (2300 ≤ Re < 4000)"
    else:
        regime = "Turbulent (Re ≥ 4000)"
    return {
        "results": [
            _r(round(re, 2), "-", "Reynolds Number Re"),
            _r(regime, "", "Flow regime"),
        ],
        "notes": ["Re = ρ·v·D / μ"],
    }


def _swamee_jain(re, rel_rough):
    """Explicit friction factor for turbulent flow (Swamee–Jain)."""
    if re <= 0:
        return 0.0
    return 0.25 / (math.log10(rel_rough / 3.7 + 5.74 / re ** 0.9)) ** 2


def darcy_pressure_drop(inp):
    rho = float(inp["rho"])
    v   = float(inp["v"])
    d   = float(inp["d"])
    mu  = float(inp["mu"])
    L   = float(inp["L"])
    eps = float(inp.get("eps", 0.000045))  # commercial steel default
    if d <= 0:
        raise ValueError("Diameter must be > 0")
    re = rho * v * d / mu if mu > 0 else float("inf")
    if re < 2300:
        f = 64.0 / re if re > 0 else 0.0
        regime = "Laminar"
    else:
        f = _swamee_jain(re, eps / d)
        regime = "Turbulent (Swamee–Jain)"
    dp = f * (L / d) * (rho * v * v / 2.0)
    head_loss = dp / (rho * 9.81)
    return {
        "results": [
            _r(round(re, 2), "-", "Reynolds Re"),
            _r(round(f, 5), "-", "Darcy friction factor f"),
            _r(round(dp, 2), "Pa", "Pressure drop ΔP"),
            _r(round(dp / 1000.0, 3), "kPa", "Pressure drop ΔP"),
            _r(round(head_loss, 3), "m", "Head loss hL"),
            _r(regime, "", "Regime"),
        ],
        "notes": [
            "ΔP = f·(L/D)·(ρ·v²/2)",
            "Laminar: f = 64/Re",
            "Turbulent: Swamee–Jain explicit form of Colebrook eq.",
        ],
    }


def pump_power(inp):
    rho = float(inp["rho"])
    Q   = float(inp["Q"])      # m³/s
    H   = float(inp["H"])      # m
    eta = float(inp.get("eta", 0.7))
    if not 0 < eta <= 1:
        raise ValueError("Efficiency must be in (0, 1]")
    p_hyd = rho * 9.81 * Q * H
    p_shaft = p_hyd / eta
    return {
        "results": [
            _r(round(p_hyd, 2), "W", "Hydraulic power"),
            _r(round(p_hyd / 1000.0, 3), "kW", "Hydraulic power"),
            _r(round(p_shaft, 2), "W", "Shaft power"),
            _r(round(p_shaft / 1000.0, 3), "kW", "Shaft power"),
            _r(round(p_shaft / 745.7, 3), "hp", "Shaft power"),
        ],
        "notes": [
            "P_hyd = ρ·g·Q·H",
            "P_shaft = P_hyd / η_pump",
        ],
    }


def npsh_available(inp):
    """NPSH available at a centrifugal pump suction (Branan, Pumps).

        NPSHa = (P_suction − P_vap) / (ρ·g) − h_static + h_friction_losses
    Sign convention: h_static positive when source above pump.
    """
    P_s   = float(inp["P_s"])     # suction-side pressure, Pa (absolute)
    P_v   = float(inp["P_v"])     # vapour pressure of liquid, Pa
    rho   = float(inp["rho"])     # kg/m³
    h_st  = float(inp.get("h_static", 0))      # m, + above pump centerline
    h_f   = float(inp.get("h_friction", 0))    # m, friction losses (positive)
    g = 9.81
    if rho <= 0:
        raise ValueError("Density must be > 0.")
    if P_s <= P_v:
        raise ValueError("Suction pressure must exceed vapour pressure.")
    NPSHa = (P_s - P_v) / (rho * g) + h_st - h_f
    return {
        "results": [
            _r(round(NPSHa, 4), "m", "NPSH available"),
            _r(round((P_s - P_v) / (rho * g), 4), "m", "Pressure-head term"),
            _r(round(h_st, 4), "m", "Static head (+ above pump)"),
            _r(round(h_f, 4), "m", "Friction losses"),
        ],
        "notes": [
            "NPSHa = (P_s − P_v)/(ρ·g) + h_static − h_friction",
            "Compare against pump's NPSH-required curve; require NPSHa ≥ NPSHr + 0.5–1 m margin.",
        ],
    }


def orifice_flow(inp):
    """Mass / volumetric flow through an orifice meter (incompressible):

        ṁ = Cd · A₂ · √[2·ρ·ΔP / (1 − β⁴)]
    where β = d/D.
    """
    rho = float(inp["rho"])
    dP  = float(inp["dP"])      # Pa
    D   = float(inp["D"])       # m, pipe ID
    d   = float(inp["d"])       # m, orifice
    Cd  = float(inp.get("Cd", 0.61))
    if D <= 0 or d <= 0 or d >= D:
        raise ValueError("Need 0 < d < D.")
    if rho <= 0 or dP <= 0:
        raise ValueError("ρ and ΔP must be > 0.")
    beta = d / D
    A2 = math.pi / 4 * d ** 2
    m_dot = Cd * A2 * math.sqrt(2 * rho * dP / (1 - beta ** 4))
    Q = m_dot / rho
    v = Q / (math.pi / 4 * D ** 2)
    return {
        "results": [
            _r(round(m_dot, 5), "kg/s", "Mass flow rate ṁ"),
            _r(round(m_dot * 3600, 3), "kg/h", "Mass flow rate"),
            _r(round(Q, 6), "m³/s", "Volumetric flow Q"),
            _r(round(Q * 3600, 4), "m³/h", "Volumetric flow"),
            _r(round(v, 4), "m/s", "Pipe velocity"),
            _r(round(beta, 4), "-", "β = d/D"),
        ],
        "notes": [
            "ṁ = Cd · A₂ · √[2·ρ·ΔP / (1 − β⁴)]",
            "Cd ≈ 0.61 for sharp-edged orifices (typical). Use ISO 5167 for precision.",
        ],
    }


def compressor_power(inp):
    """Adiabatic / polytropic compression power for an ideal gas.

    Adiabatic (γ = Cp/Cv):
        W_ad = (γ/(γ−1)) · n·R·T₁ · [(P₂/P₁)^((γ−1)/γ) − 1]
    Shaft power = W_ad / η_isen.
    Outlet temperature: T₂ = T₁ · (P₂/P₁)^((γ−1)/γ) / η (approx for isen.).
    """
    n_dot = float(inp["n_dot"])        # mol/s
    T1    = float(inp["T1"])           # K
    P1    = float(inp["P1"])           # Pa
    P2    = float(inp["P2"])           # Pa
    gamma = float(inp.get("gamma", 1.4))
    eta   = float(inp.get("eta", 0.75))
    R = 8.314462618
    if P1 <= 0 or P2 <= P1:
        raise ValueError("Need 0 < P1 < P2.")
    if not 1 < gamma:
        raise ValueError("γ must be > 1.")
    if not 0 < eta <= 1:
        raise ValueError("Efficiency η must be in (0, 1].")
    ratio = P2 / P1
    k = (gamma - 1) / gamma
    W_isen = (gamma / (gamma - 1)) * n_dot * R * T1 * (ratio ** k - 1)   # W
    W_shaft = W_isen / eta
    T2_isen = T1 * ratio ** k
    T2_actual = T1 + (T2_isen - T1) / eta
    return {
        "results": [
            _r(round(W_isen, 3), "W", "Isentropic compression power"),
            _r(round(W_isen / 1000.0, 4), "kW", "Isentropic power"),
            _r(round(W_shaft, 3), "W", "Shaft power"),
            _r(round(W_shaft / 1000.0, 4), "kW", "Shaft power"),
            _r(round(W_shaft / 745.7, 3), "hp", "Shaft power"),
            _r(round(T2_isen, 3), "K", "Isentropic discharge T₂"),
            _r(round(T2_actual, 3), "K", "Actual discharge T₂"),
            _r(round(ratio, 4), "-", "Pressure ratio P₂/P₁"),
        ],
        "notes": [
            "Single-stage adiabatic ideal-gas compression.",
            "W_isen = γ/(γ−1) · n·R·T₁ · [(P₂/P₁)^((γ−1)/γ) − 1]",
            "Use polytropic eqs. with η_p for high-ratio compressors; multi-stage with intercooling for ratio > ~4.",
        ],
    }
