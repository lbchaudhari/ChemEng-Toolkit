"""Unit conversions."""
from __future__ import annotations


def _r(value, unit, label):
    return {"label": label, "value": value, "unit": unit}


# Each table maps unit -> factor to SI base
LENGTH = {  # to meters
    "m": 1.0, "mm": 1e-3, "cm": 1e-2, "km": 1e3,
    "in": 0.0254, "ft": 0.3048, "yd": 0.9144, "mile": 1609.344,
}
MASS = {  # to kg
    "kg": 1.0, "g": 1e-3, "mg": 1e-6, "tonne": 1000.0,
    "lb": 0.45359237, "oz": 0.028349523125,
}
PRESSURE = {  # to Pa
    "Pa": 1.0, "kPa": 1e3, "MPa": 1e6, "bar": 1e5,
    "atm": 101325.0, "psi": 6894.757293168, "mmHg": 133.322387415,
    "inHg": 3386.389, "torr": 133.322387415,
}
ENERGY = {  # to J
    "J": 1.0, "kJ": 1e3, "MJ": 1e6,
    "cal": 4.184, "kcal": 4184.0,
    "Wh": 3600.0, "kWh": 3.6e6,
    "BTU": 1055.05585, "ft-lbf": 1.355817948,
}
VOLUME_FLOW = {  # to m³/s
    "m3/s": 1.0, "m3/h": 1.0 / 3600.0, "L/s": 1e-3, "L/min": 1e-3 / 60.0,
    "gal/min": 6.30901964e-5, "ft3/s": 0.0283168466, "bbl/d": 1.84013e-6,
}


def _convert(table, value, unit_from, unit_to):
    if unit_from not in table:
        raise ValueError(f"Unknown unit '{unit_from}'. Allowed: {', '.join(table)}")
    if unit_to not in table:
        raise ValueError(f"Unknown unit '{unit_to}'. Allowed: {', '.join(table)}")
    si = value * table[unit_from]
    return si / table[unit_to]


def length(inp):
    out = _convert(LENGTH, float(inp["value"]), inp["from"], inp["to"])
    return {"results": [_r(round(out, 8), inp["to"], "Converted value")],
            "notes": [f"{inp['value']} {inp['from']} = {out:g} {inp['to']}"]}


def mass(inp):
    out = _convert(MASS, float(inp["value"]), inp["from"], inp["to"])
    return {"results": [_r(round(out, 8), inp["to"], "Converted value")],
            "notes": [f"{inp['value']} {inp['from']} = {out:g} {inp['to']}"]}


def pressure(inp):
    out = _convert(PRESSURE, float(inp["value"]), inp["from"], inp["to"])
    return {"results": [_r(round(out, 6), inp["to"], "Converted value")],
            "notes": [f"{inp['value']} {inp['from']} = {out:g} {inp['to']}"]}


def energy(inp):
    out = _convert(ENERGY, float(inp["value"]), inp["from"], inp["to"])
    return {"results": [_r(round(out, 6), inp["to"], "Converted value")],
            "notes": [f"{inp['value']} {inp['from']} = {out:g} {inp['to']}"]}


def volume_flow(inp):
    out = _convert(VOLUME_FLOW, float(inp["value"]), inp["from"], inp["to"])
    return {"results": [_r(round(out, 8), inp["to"], "Converted value")],
            "notes": [f"{inp['value']} {inp['from']} = {out:g} {inp['to']}"]}


def temperature(inp):
    """Convert between °C, °F, K, °R."""
    v = float(inp["value"])
    src = inp["from"].upper().strip("°")
    dst = inp["to"].upper().strip("°")
    # to Kelvin
    if   src == "C": K = v + 273.15
    elif src == "F": K = (v - 32) * 5 / 9 + 273.15
    elif src == "K": K = v
    elif src == "R": K = v * 5 / 9
    else: raise ValueError("from must be C, F, K, or R")
    if   dst == "C": out = K - 273.15
    elif dst == "F": out = (K - 273.15) * 9 / 5 + 32
    elif dst == "K": out = K
    elif dst == "R": out = K * 9 / 5
    else: raise ValueError("to must be C, F, K, or R")
    return {
        "results": [_r(round(out, 4), inp["to"], "Converted temperature")],
        "notes": [f"{v} °{src} = {out:.4f} °{dst}"],
    }


# Allowed-unit hints (used by the registry to render dropdowns)
ALLOWED = {
    "length":      list(LENGTH),
    "mass":        list(MASS),
    "pressure":    list(PRESSURE),
    "energy":      list(ENERGY),
    "volume_flow": list(VOLUME_FLOW),
    "temperature": ["C", "F", "K", "R"],
}
