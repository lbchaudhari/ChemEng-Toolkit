"""Rule-based chemistry assistant.

For each topic we attempt:
1. To extract numeric values from the user's message and run a quick calculation.
2. Otherwise, return the formula and a short explanation.

Returned shape: {"reply": str, "formula": str|None, "results": list|None, "calculator": str|None}
"calculator" is the slug of a related calculator the user can open.
"""
from __future__ import annotations
import re

from calculations import fluids, heat, thermo, reaction, economics


# ---------- helpers --------------------------------------------------------

NUM = r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"

def _grab(pattern, text, group=1, cast=float):
    m = re.search(pattern, text, re.IGNORECASE)
    if not m:
        return None
    try:
        return cast(m.group(group))
    except (ValueError, IndexError):
        return None


def _result_lines(results):
    return [f"{r['label']}: {r['value']} {r.get('unit', '')}".rstrip()
            for r in results]


def _wrap(reply, formula=None, results=None, calculator=None):
    return {
        "reply": reply,
        "formula": formula,
        "results": results or [],
        "calculator": calculator,
    }


# ---------- intent handlers ------------------------------------------------

def _intent_reynolds(q):
    rho = _grab(rf"\b(?:density|rho|ρ)\s*=?\s*({NUM})", q)
    v   = _grab(rf"\b(?:velocity|speed|v)\s*=?\s*({NUM})", q)
    d   = _grab(rf"\b(?:diameter|dia|d)\s*=?\s*({NUM})", q)
    mu  = _grab(rf"\b(?:viscosity|mu|μ)\s*=?\s*({NUM})", q)
    if all(x is not None for x in (rho, v, d, mu)):
        out = fluids.reynolds({"rho": rho, "v": v, "d": d, "mu": mu})
        return _wrap(
            f"Reynolds number for ρ={rho}, v={v}, D={d}, μ={mu}:",
            "Re = ρ·v·D / μ",
            out["results"],
            "reynolds",
        )
    return _wrap(
        "The Reynolds number indicates whether flow is laminar (Re < 2300), "
        "transitional (2300–4000) or turbulent (Re ≥ 4000). Open the calculator to compute it.",
        "Re = ρ·v·D / μ",
        calculator="reynolds",
    )


def _intent_lmtd(q):
    Thi = _grab(rf"\b(?:hot[^\d]*in|Thi)\s*=?\s*({NUM})", q)
    Tho = _grab(rf"\b(?:hot[^\d]*out|Tho)\s*=?\s*({NUM})", q)
    Tci = _grab(rf"\b(?:cold[^\d]*in|Tci)\s*=?\s*({NUM})", q)
    Tco = _grab(rf"\b(?:cold[^\d]*out|Tco)\s*=?\s*({NUM})", q)
    flow = "parallel" if "parallel" in q.lower() or "co-current" in q.lower() else "counter"
    if all(x is not None for x in (Thi, Tho, Tci, Tco)):
        out = heat.lmtd({"Thi": Thi, "Tho": Tho, "Tci": Tci, "Tco": Tco, "flow": flow})
        return _wrap(
            f"LMTD ({flow} flow) for Th: {Thi}→{Tho}, Tc: {Tci}→{Tco}:",
            "LMTD = (ΔT1 - ΔT2) / ln(ΔT1/ΔT2)",
            out["results"],
            "lmtd",
        )
    return _wrap(
        "LMTD is the log-mean temperature difference driving heat transfer in "
        "a heat exchanger. Provide the four terminal temperatures.",
        "LMTD = (ΔT1 - ΔT2) / ln(ΔT1/ΔT2)",
        calculator="lmtd",
    )


def _intent_ideal_gas(q):
    P = _grab(rf"\bP\s*=?\s*({NUM})", q)
    V = _grab(rf"\bV\s*=?\s*({NUM})", q)
    n = _grab(rf"\bn\s*=?\s*({NUM})", q)
    T = _grab(rf"\bT\s*=?\s*({NUM})", q)
    vals = [P, V, n, T]
    if sum(1 for x in vals if x is not None) == 3:
        spec = {"P": P or 0, "V": V or 0, "n": n or 0, "T": T or 0}
        out = thermo.ideal_gas(spec)
        return _wrap(
            f"Solving PV = nRT with the missing variable left as 0:",
            "P·V = n·R·T",
            out["results"],
            "ideal_gas",
        )
    return _wrap(
        "The ideal-gas law relates pressure, volume, moles and temperature. "
        "Use SI units: P [Pa], V [m³], n [mol], T [K]. R = 8.314 J/(mol·K).",
        "P·V = n·R·T",
        calculator="ideal_gas",
    )


def _intent_arrhenius(q):
    A  = _grab(rf"\bA\s*=\s*({NUM})", q)
    Ea = _grab(rf"\bEa\s*=?\s*({NUM})", q)
    T  = _grab(rf"\bT\s*=?\s*({NUM})", q)
    if all(x is not None for x in (A, Ea, T)):
        out = reaction.arrhenius({"A": A, "Ea": Ea, "T": T})
        return _wrap(
            f"Arrhenius rate constant for A={A}, Ea={Ea} J/mol, T={T} K:",
            "k = A·exp(-Ea / R·T)",
            out["results"],
            "arrhenius",
        )
    return _wrap(
        "The Arrhenius equation gives the temperature dependence of a rate constant.",
        "k = A·exp(-Ea / R·T)",
        calculator="arrhenius",
    )


def _intent_npv(q):
    rate = _grab(rf"\b(?:rate|discount)\s*=?\s*({NUM})", q)
    m = re.search(r"flows?[:\s]+([-\d.,\s]+)", q, re.IGNORECASE)
    if rate is not None and m:
        out = economics.npv({"rate": rate, "flows": m.group(1)})
        return _wrap(
            f"NPV at {rate}% for the supplied cash flows:",
            "NPV = Σ CF_t / (1 + r)^t",
            out["results"],
            "npv",
        )
    return _wrap(
        "NPV discounts each future cash flow back to year 0. Year 0 is the initial "
        "investment (negative). Open the calculator to enter your cash-flow stream.",
        "NPV = Σ CF_t / (1 + r)^t",
        calculator="npv",
    )


def _intent_pump(q):
    return _wrap(
        "Centrifugal pump shaft power: P_shaft = ρ·g·Q·H / η_pump.",
        "P_shaft = ρ·g·Q·H / η_pump",
        calculator="pump_power",
    )


def _intent_fenske(q):
    return _wrap(
        "Fenske gives the minimum number of equilibrium stages at total reflux.",
        "N_min = log[(xD/(1-xD))·((1-xB)/xB)] / log(α)",
        calculator="fenske",
    )


def _intent_pfr(q):
    return _wrap(
        "For a first-order liquid-phase PFR at constant density.",
        "τ = (1/k)·ln[1/(1-X)]   ⇒   V = v0·τ",
        calculator="pfr",
    )


def _intent_cstr(q):
    return _wrap(
        "For a first-order liquid-phase CSTR.",
        "τ = X / [k·(1-X)]   ⇒   V = v0·τ",
        calculator="cstr",
    )


def _intent_antoine(q):
    return _wrap(
        "Antoine equation gives vapor pressure as a function of temperature. "
        "Coefficients A, B, C must match the units used.",
        "log10(P) = A − B / (T + C)",
        calculator="antoine",
    )


def _intent_default(q):
    return _wrap(
        "I can help with: Reynolds number, pipe pressure drop, pump power, "
        "LMTD, heat-exchanger area, conduction, Fenske, Underwood, Kremser, "
        "ideal gas, Antoine, Redlich–Kwong, CSTR/PFR/batch reactors, Arrhenius, "
        "unit conversions, NPV, payback, Lang-factor CAPEX. Try: "
        "“Reynolds with rho 1000 v 2 d 0.05 mu 0.001”."
    )


# ---------- dispatcher -----------------------------------------------------

ROUTES = [
    (r"\breynolds\b|\bre\b",                        _intent_reynolds),
    (r"\blmtd\b|\blog mean\b",                      _intent_lmtd),
    (r"\bideal gas\b|\bpv\s*=\s*nrt\b",             _intent_ideal_gas),
    (r"\barrhenius\b|\brate constant\b",            _intent_arrhenius),
    (r"\bnpv\b|\bnet present\b",                    _intent_npv),
    (r"\bpump\b|\bpower\b",                         _intent_pump),
    (r"\bfenske\b|\bmin(?:imum)? stages\b",         _intent_fenske),
    (r"\bpfr\b|\bplug flow\b",                      _intent_pfr),
    (r"\bcstr\b|\bstirred tank\b",                  _intent_cstr),
    (r"\bantoine\b|\bvapor pressure\b",             _intent_antoine),
]


def answer(msg: str) -> dict:
    text = msg.lower()
    for pattern, handler in ROUTES:
        if re.search(pattern, text):
            try:
                return handler(msg)
            except Exception as exc:
                return _wrap(f"Couldn't compute that: {exc}")
    return _intent_default(msg)
