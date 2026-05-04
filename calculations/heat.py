"""Heat transfer calculations."""
from __future__ import annotations
import math


def _r(value, unit, label):
    return {"label": label, "value": value, "unit": unit}


def lmtd(inp):
    Thi = float(inp["Thi"])
    Tho = float(inp["Tho"])
    Tci = float(inp["Tci"])
    Tco = float(inp["Tco"])
    flow = (inp.get("flow") or "counter").lower()

    if flow.startswith("par"):
        dT1 = Thi - Tci
        dT2 = Tho - Tco
        flow_label = "Parallel flow"
    else:
        dT1 = Thi - Tco
        dT2 = Tho - Tci
        flow_label = "Counter flow"

    if dT1 * dT2 <= 0:
        raise ValueError("Temperature crossover; check inputs.")
    if abs(dT1 - dT2) < 1e-9:
        lm = dT1
    else:
        lm = (dT1 - dT2) / math.log(dT1 / dT2)

    return {
        "results": [
            _r(round(dT1, 3), "°C/K", "ΔT1"),
            _r(round(dT2, 3), "°C/K", "ΔT2"),
            _r(round(lm, 3), "°C/K", "LMTD"),
            _r(flow_label, "", "Configuration"),
        ],
        "notes": ["LMTD = (ΔT1 - ΔT2) / ln(ΔT1/ΔT2)"],
    }


def heat_exchanger_area(inp):
    Q = float(inp["Q"])     # W
    U = float(inp["U"])     # W/m²K
    lm = float(inp["lmtd"]) # K
    F  = float(inp.get("F", 1.0))
    if U <= 0 or lm <= 0:
        raise ValueError("U and LMTD must be > 0")
    A = Q / (U * F * lm)
    return {
        "results": [
            _r(round(A, 4), "m²", "Heat transfer area A"),
            _r(round(Q / 1000.0, 3), "kW", "Duty Q"),
        ],
        "notes": [
            "Q = U·A·F·LMTD  →  A = Q / (U·F·LMTD)",
            "F = LMTD correction factor (1.0 for true counter/co-current).",
        ],
    }


def conduction_wall(inp):
    k  = float(inp["k"])
    A  = float(inp["A"])
    T1 = float(inp["T1"])
    T2 = float(inp["T2"])
    L  = float(inp["L"])
    if L <= 0:
        raise ValueError("Wall thickness must be > 0")
    Q = k * A * (T1 - T2) / L
    R = L / (k * A)
    return {
        "results": [
            _r(round(Q, 3), "W", "Heat flow Q"),
            _r(round(Q / 1000.0, 4), "kW", "Heat flow Q"),
            _r(round(R, 6), "K/W", "Thermal resistance R"),
        ],
        "notes": [
            "Q = k·A·(T1 - T2) / L",
            "R = L / (k·A)",
        ],
    }
