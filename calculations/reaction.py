"""Reaction engineering calculations (single first-order reaction A → products)."""
from __future__ import annotations
import math


def _r(value, unit, label):
    return {"label": label, "value": value, "unit": unit}


def cstr_first_order(inp):
    """V = F_A0·X / (k·C_A0·(1 - X)) = v0·X / (k·(1 - X)) for first-order."""
    CA0 = float(inp["CA0"])    # mol/m³
    v0  = float(inp["v0"])     # m³/s
    k   = float(inp["k"])      # 1/s
    X   = float(inp["X"])      # 0..1
    if not 0 < X < 1:
        raise ValueError("Conversion X must be in (0, 1).")
    if k <= 0:
        raise ValueError("k must be > 0.")
    tau = X / (k * (1 - X))
    V = v0 * tau
    return {
        "results": [
            _r(round(tau, 4), "s", "Space time τ"),
            _r(round(V, 6), "m³", "Reactor volume V"),
            _r(round(V * 1000, 3), "L", "Reactor volume V"),
            _r(round(CA0 * (1 - X), 4), "mol/m³", "Outlet concentration CA"),
        ],
        "notes": [
            "First-order: -r_A = k·C_A,  C_A = C_A0·(1 - X)",
            "CSTR: V = F_A0·X / (-r_A) ⇒ τ = X / [k·(1 - X)]",
        ],
    }


def pfr_first_order(inp):
    """V = (v0/k)·ln(1/(1 - X)) for first-order, constant density."""
    CA0 = float(inp["CA0"])
    v0  = float(inp["v0"])
    k   = float(inp["k"])
    X   = float(inp["X"])
    if not 0 < X < 1:
        raise ValueError("Conversion X must be in (0, 1).")
    if k <= 0:
        raise ValueError("k must be > 0.")
    tau = -math.log(1 - X) / k
    V = v0 * tau
    return {
        "results": [
            _r(round(tau, 4), "s", "Space time τ"),
            _r(round(V, 6), "m³", "Reactor volume V"),
            _r(round(V * 1000, 3), "L", "Reactor volume V"),
            _r(round(CA0 * (1 - X), 4), "mol/m³", "Outlet concentration CA"),
        ],
        "notes": [
            "First-order PFR: τ = (1/k)·ln[1/(1-X)]",
            "V = v0·τ for constant density.",
        ],
    }


def batch_first_order(inp):
    """t = (1/k)·ln(C0/C) for first-order batch."""
    C0 = float(inp["C0"])
    C  = float(inp["C"])
    k  = float(inp["k"])
    if C <= 0 or C0 <= 0:
        raise ValueError("Concentrations must be > 0.")
    if C >= C0:
        raise ValueError("C must be < C0.")
    if k <= 0:
        raise ValueError("k must be > 0.")
    t = math.log(C0 / C) / k
    X = 1 - C / C0
    return {
        "results": [
            _r(round(t, 4), "s", "Reaction time t"),
            _r(round(t / 60.0, 4), "min", "Reaction time t"),
            _r(round(X, 4), "-", "Conversion X"),
        ],
        "notes": [
            "First-order batch: dC/dt = -k·C  ⇒  t = (1/k)·ln(C0/C)",
        ],
    }


def arrhenius(inp):
    """k(T) = A·exp(-Ea / R·T)."""
    A  = float(inp["A"])     # 1/s
    Ea = float(inp["Ea"])    # J/mol
    T  = float(inp["T"])     # K
    R = 8.314462618
    if T <= 0:
        raise ValueError("T must be > 0 K.")
    k = A * math.exp(-Ea / (R * T))
    return {
        "results": [
            _r(f"{k:.6g}", "1/s", "Rate constant k"),
            _r(round(Ea / 1000.0, 3), "kJ/mol", "Activation energy Ea"),
        ],
        "notes": ["k = A·exp(-Ea / R·T)"],
    }
