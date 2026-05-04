"""Advanced piping & valve sizing.

* Advanced line sizing (single phase liquid / gas) with economic velocity
  and pressure-drop check.
* Control valve Cv – liquid (incompressible) and gas (ISA-75 / Crane).
* Pressure relief valve – API 520 gas/vapour and liquid.
"""
from __future__ import annotations
import math
from .diagrams import PIPE_SVG, VALVE_SVG, PSV_SVG


def _r(value, unit, label):
    return {"label": label, "value": value, "unit": unit}


def _f(d, k, default=0.0):
    v = d.get(k, default)
    if v in ("", None):
        return float(default)
    try:
        return float(v)
    except (TypeError, ValueError):
        return float(default)


def _ds(title, rows):
    return {"title": title, "rows": rows}


def _round(x, n=4):
    if x is None or not (isinstance(x, (int, float)) and math.isfinite(x)):
        return x
    return round(x, n)


# ANSI / ASME B36.10 schedule-40 typical IDs (mm) for line-size selection
_NPS = [
    (0.5, 15.80), (0.75, 20.93), (1.0, 26.64), (1.25, 35.05),
    (1.5, 40.89), (2.0, 52.50), (2.5, 62.71), (3.0, 77.93),
    (4.0, 102.26), (6.0, 154.05), (8.0, 202.72), (10.0, 254.46),
    (12.0, 303.23), (14.0, 333.34), (16.0, 381.00), (18.0, 428.66),
    (20.0, 477.82), (24.0, 574.65), (30.0, 717.55), (36.0, 863.60),
]


def _select_nps(D_required_m):
    D_mm = D_required_m * 1000.0
    for nps, id_mm in _NPS:
        if id_mm >= D_mm:
            return nps, id_mm
    return _NPS[-1]


# =====================================================================
# 1. ADVANCED LINE SIZING (liquid OR gas)
# =====================================================================
def line_sizing(inp):
    phase  = (inp.get("phase") or "Liquid").strip()
    m      = _f(inp, "m",   10.0)             # mass flow kg/s
    rho    = _f(inp, "rho", 1000.0)
    mu     = _f(inp, "mu",  0.001)
    L      = _f(inp, "L",   100.0)
    eps    = _f(inp, "eps", 4.5e-5)            # 0.045 mm commercial steel
    K_fit  = _f(inp, "K_fit", 4.0)             # ΣK fittings

    # Branan / Branan-Mills economic velocity ranges
    if phase.lower().startswith("gas"):
        v_target = _f(inp, "v_target", 20.0)   # gas line: 15–30 m/s typical
    elif phase.lower().startswith("two"):
        v_target = _f(inp, "v_target", 8.0)
    else:
        v_target = _f(inp, "v_target", 2.0)    # pump discharge ~2 m/s, suction ~1.5

    if rho <= 0 or m <= 0 or v_target <= 0:
        raise ValueError("Flow, density and target velocity must be > 0.")

    Q       = m / rho                          # m³/s
    D_calc  = math.sqrt(4.0 * Q / (math.pi * v_target))
    nps, id_mm = _select_nps(D_calc)
    D       = id_mm / 1000.0
    v_act   = 4.0 * Q / (math.pi * D ** 2)

    # Friction
    Re = rho * v_act * D / mu if mu > 0 else 0.0
    if Re < 2300:
        f = 64.0 / Re if Re > 0 else 0.0
        regime = "Laminar"
    else:
        f = 0.25 / (math.log10(eps / (3.7 * D) + 5.74 / Re ** 0.9)) ** 2
        regime = "Turbulent"

    dP_pipe = f * (L / D) * 0.5 * rho * v_act ** 2
    dP_fit  = K_fit * 0.5 * rho * v_act ** 2
    dP_tot  = dP_pipe + dP_fit
    dP_per_100 = dP_tot * 100.0 / L if L > 0 else 0.0

    # Branan recommended ΔP/100m thresholds
    rec = "Within typical range"
    if phase.lower().startswith("gas"):
        if dP_per_100 > 11000:                # ~ 0.5 psi/100ft = 11.3 kPa/100m
            rec = "ΔP high – consider larger NPS"
        elif dP_per_100 < 1000:
            rec = "ΔP low – may be over-sized"
    else:
        if dP_per_100 > 4500:                 # ~ 0.2 psi/100ft = 4.5 kPa/100m
            rec = "ΔP high – consider larger NPS"
        elif dP_per_100 < 250:
            rec = "ΔP low – may be over-sized"

    results = [
        _r(_round(Q, 5),       "m³/s", "Volumetric flow Q"),
        _r(f"{nps}\"",         "NPS",  "Selected line size"),
        _r(_round(id_mm, 1),   "mm",   "Inside diameter ID"),
        _r(_round(v_act, 3),   "m/s",  "Actual velocity"),
        _r(_round(Re, 0),      "-",    "Reynolds number"),
        _r(regime,             "",     "Flow regime"),
        _r(_round(f, 5),       "-",    "Darcy friction factor"),
        _r(_round(dP_pipe/1000,3),"kPa","ΔP straight pipe"),
        _r(_round(dP_fit /1000,3),"kPa","ΔP fittings"),
        _r(_round(dP_tot /1000,3),"kPa","ΔP total"),
        _r(_round(dP_per_100/1000,3),"kPa/100m","ΔP per 100 m"),
        _r(rec,                "",     "Recommendation"),
    ]
    datasheet = [
        _ds("Line Sizing – Service", [
            ["Line tag",     inp.get("tag", "L-101")],
            ["Phase",        phase],
            ["Length",       f"{L} m"],
            ["Roughness ε",  f"{eps*1000:.3f} mm"],
        ]),
        _ds("Line Sizing – Design", [
            ["Mass flow",        f"{m} kg/s"],
            ["Density",          f"{rho} kg/m³"],
            ["Viscosity",        f"{mu} Pa·s"],
            ["Target velocity",  f"{v_target} m/s"],
            ["Selected NPS",     f"{nps}\"  (ID {id_mm:.1f} mm)"],
            ["Actual velocity",  f"{v_act:.2f} m/s"],
            ["Reynolds",         f"{Re:.0f}"],
            ["ΔP total",         f"{dP_tot/1000:.2f} kPa"],
            ["ΔP per 100 m",     f"{dP_per_100/1000:.2f} kPa/100m"],
        ]),
    ]
    return {
        "results":   results,
        "datasheet": datasheet,
        "diagram":   PIPE_SVG,
        "notes": [
            "Pipe sized to user target velocity, then snapped to next NPS (Sch 40).",
            "Branan target velocities: liquid 1–3 m/s, gas 15–30 m/s, two-phase 5–10 m/s.",
            "ΔP = f·(L/D)·½ρv² + ΣK·½ρv²  (Darcy–Weisbach + fitting heads).",
            "Friction factor: Swamee–Jain (turbulent) or 64/Re (laminar).",
            "Branan recommends ΔP < ~0.2 psi/100ft (≈ 4.5 kPa/100m) for liquid lines.",
        ],
    }


# =====================================================================
# 2. CONTROL VALVE Cv (LIQUID & GAS)
# =====================================================================
def control_valve_cv(inp):
    fluid = (inp.get("fluid") or "Liquid").strip()
    P1    = _f(inp, "P1", 600000.0)            # Pa abs
    P2    = _f(inp, "P2", 400000.0)            # Pa abs
    rho   = _f(inp, "rho", 1000.0)
    if fluid.lower().startswith("liq"):
        Q_m3h = _f(inp, "Q", 50.0)
        SG    = rho / 1000.0
        dP_psi = (P1 - P2) / 6894.76
        Q_gpm  = Q_m3h * 4.40287
        if dP_psi <= 0:
            raise ValueError("Need P1 > P2 for control valve.")
        # Choked-flow check (cavitation)
        Pv     = _f(inp, "Pv", 3170.0)
        Pc     = _f(inp, "Pc", 2.21e7)
        FF     = 0.96 - 0.28 * math.sqrt(Pv / Pc) if Pc > 0 else 0.9
        FL     = _f(inp, "FL", 0.9)
        dP_choke = FL ** 2 * (P1 - FF * Pv)
        choked = (P1 - P2) > dP_choke
        dP_use  = dP_choke if choked else (P1 - P2)
        Cv      = Q_gpm * math.sqrt(SG / (dP_use / 6894.76))
        Kv      = Cv / 1.156
        results = [
            _r(_round(Cv,   3), "US",   "Cv (US units)"),
            _r(_round(Kv,   3), "SI",   "Kv (= Cv/1.156)"),
            _r(_round(dP_psi,3), "psi", "Available ΔP"),
            _r(_round(dP_choke/6894.76,3), "psi", "Choked ΔP (FL²·(P1−FF·Pv))"),
            _r("Yes" if choked else "No", "", "Choked / cavitating?"),
        ]
        notes = [
            "Liquid Cv = Q[gpm]·√(SG/ΔP[psi]).  Kv = Cv/1.156.",
            "Choked when ΔP ≥ FL²·(P1 − FF·Pv); FF ≈ 0.96 − 0.28·√(Pv/Pc).",
        ]
        datasheet = [
            _ds("Control Valve – Liquid Service", [
                ["Tag",            inp.get("tag", "FV-101")],
                ["Fluid",          inp.get("name", "Water")],
                ["Flow",           f"{Q_m3h} m³/h ({Q_gpm:.1f} US gpm)"],
                ["P1 / P2",        f"{P1/1e3:.1f} / {P2/1e3:.1f} kPa abs"],
                ["SG",             f"{SG:.3f}"],
                ["Cv (US) / Kv",   f"{Cv:.1f} / {Kv:.1f}"],
                ["Cavitating?",    "Yes" if choked else "No"],
            ]),
        ]
    else:
        # Gas (ISA – simplified Crane form)
        Q_scfh = _f(inp, "Q",   1000.0)        # std ft³/h
        SG     = _f(inp, "SG",  0.65)
        T      = _f(inp, "T",   293.15)         # K
        P1_psi = P1 / 6894.76
        P2_psi = P2 / 6894.76
        dP_psi = P1_psi - P2_psi
        if dP_psi <= 0:
            raise ValueError("Need P1 > P2 for control valve.")
        # Subsonic Crane form: Cv = Q·sqrt(SG·T) / (1360·sqrt(dP·(P1+P2)))
        Cv = Q_scfh * math.sqrt(SG * T * 1.8) / (1360.0 * math.sqrt(dP_psi * (P1_psi + P2_psi)))
        # Choked check (critical pressure ratio ≈ 0.5)
        choked = (P2 / P1) < 0.528
        results = [
            _r(_round(Cv, 3),     "-",   "Cv (gas)"),
            _r(_round(dP_psi,3),  "psi", "ΔP"),
            _r(_round(P2/P1, 3),  "-",   "P2/P1 ratio"),
            _r("Yes" if choked else "No", "", "Sonic (choked)?"),
        ]
        notes = [
            "Crane-form gas Cv:  Cv = Q·√(SG·T·1.8) / (1360·√(ΔP·(P1+P2))).  Q in scfh, T in K.",
            "Sonic when P2/P1 < ~0.528.",
        ]
        datasheet = [
            _ds("Control Valve – Gas Service", [
                ["Tag",            inp.get("tag", "FV-101")],
                ["Gas",            inp.get("name", "Natural gas")],
                ["Flow",           f"{Q_scfh} scfh"],
                ["P1 / P2",        f"{P1/1e3:.1f} / {P2/1e3:.1f} kPa abs"],
                ["SG (air = 1)",   f"{SG}"],
                ["T",              f"{T} K"],
                ["Cv",             f"{Cv:.1f}"],
                ["Sonic?",         "Yes" if choked else "No"],
            ]),
        ]
    return {
        "results":   results,
        "datasheet": datasheet,
        "diagram":   VALVE_SVG,
        "notes":     notes,
    }


# =====================================================================
# 3. RELIEF VALVE SIZING – API 520
# =====================================================================
def relief_valve(inp):
    fluid = (inp.get("fluid") or "Gas").strip()
    Kd    = _f(inp, "Kd",  0.975)
    Kb    = _f(inp, "Kb",  1.0)
    Kc    = _f(inp, "Kc",  1.0)
    if fluid.lower().startswith("gas"):
        W   = _f(inp, "W",   5000.0)            # kg/h
        T   = _f(inp, "T",   373.15)
        Z   = _f(inp, "Z",   1.0)
        MW  = _f(inp, "MW",  29.0)
        k   = _f(inp, "k",   1.4)
        P1  = _f(inp, "P1",  1100000.0)         # relieving abs (Pa)
        # Critical pressure ratio
        rc = (2.0 / (k + 1.0)) ** (k / (k - 1.0))
        # C coefficient for gas (SI form, kPa basis)
        C  = 0.03948 * math.sqrt(k * (2.0 / (k + 1.0)) ** ((k + 1.0) / (k - 1.0)))
        P1_kPa = P1 / 1000.0
        # API 520 SI: A [mm²] = W / (C·Kd·Kb·Kc·P1·sqrt(MW/(T·Z))) ; with W in kg/h, P1 in kPa(a)
        denom = C * Kd * Kb * Kc * P1_kPa * math.sqrt(MW / (T * Z))
        A_mm2 = W / denom if denom > 0 else 0.0
        results = [
            _r(_round(A_mm2, 2), "mm²", "Required orifice area A"),
            _r(_round(C, 5),     "-",   "Gas coefficient C(k)"),
            _r(_round(rc, 4),    "-",   "Critical pressure ratio"),
        ]
        notes = [
            "API 520 SI gas:  A [mm²] = W / (C·Kd·Kb·Kc·P1·√(MW/(T·Z)))",
            "C = 0.03948·√[k·(2/(k+1))^((k+1)/(k−1))].  W kg/h, P1 kPa abs.",
            "Round up to next API standard orifice (D, E, F, G, H, J, K, L, M, N, P, Q, R, T).",
        ]
        ds_rows = [
            ["Tag",         inp.get("tag", "PSV-101")],
            ["Service",     inp.get("service", "Gas overpressure")],
            ["Relieving W", f"{W} kg/h"],
            ["MW",          f"{MW}"],
            ["k = Cp/Cv",   f"{k}"],
            ["T relieving", f"{T} K"],
            ["P1 (relieving abs)", f"{P1/1e3:.1f} kPa"],
            ["Required area",      f"{A_mm2:.1f} mm²"],
        ]
    else:
        # Liquid (API 520 Part I, SI eq.)
        Q_m3h = _f(inp, "Q", 50.0)
        SG    = _f(inp, "SG", 1.0)
        Kw    = _f(inp, "Kw", 1.0)
        Kv    = _f(inp, "Kv", 0.98)
        P1    = _f(inp, "P1", 1100000.0)
        P2    = _f(inp, "P2", 101325.0)
        dP_kPa = (P1 - P2) / 1000.0
        if dP_kPa <= 0:
            raise ValueError("Need P1 > P2.")
        # API 520 SI:  A[mm²] = 11.78·Q / (Kd·Kw·Kc·Kv) · √(SG/ΔP[kPa]); Q m³/h
        A_mm2 = 11.78 * Q_m3h / (Kd * Kw * Kc * Kv) * math.sqrt(SG / dP_kPa)
        results = [
            _r(_round(A_mm2, 2),  "mm²", "Required orifice area A"),
            _r(_round(dP_kPa,2),  "kPa", "ΔP relieving"),
        ]
        notes = [
            "API 520 SI liquid:  A [mm²] = 11.78·Q[m³/h] / (Kd·Kw·Kc·Kv)·√(SG/ΔP[kPa]).",
        ]
        ds_rows = [
            ["Tag",         inp.get("tag", "PSV-101")],
            ["Service",     inp.get("service", "Liquid overpressure")],
            ["Q relieving", f"{Q_m3h} m³/h"],
            ["SG",          f"{SG}"],
            ["P1 / P2",     f"{P1/1e3:.1f} / {P2/1e3:.1f} kPa abs"],
            ["Required area",      f"{A_mm2:.1f} mm²"],
        ]

    # Round to next API orifice
    api = [("D",71),("E",126),("F",198),("G",325),("H",506),("J",830),
           ("K",1186),("L",1841),("M",2323),("N",2800),("P",4116),
           ("Q",7129),("R",10322),("T",16774)]
    sel = next(((o, a) for o, a in api if a >= results[0]["value"]), api[-1])
    results.append(_r(f"{sel[0]} ({sel[1]} mm²)", "API", "Selected orifice"))
    ds_rows.append(["Selected API orifice", f"{sel[0]} ({sel[1]} mm²)"])

    return {
        "results":   results,
        "datasheet": [_ds("Relief Valve Datasheet", ds_rows)],
        "diagram":   PSV_SVG,
        "notes":     notes,
    }
