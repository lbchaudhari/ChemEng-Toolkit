"""Full equipment-design calculators with datasheets and SVG diagrams.

Modules covered:
    * Centrifugal pump design (full hydraulic + datasheet)
    * Shell & tube heat exchanger design (Kern method, TEMA datasheet)
    * Distillation column design (Fenske–Underwood–Gilliland + datasheet)
    * Vertical 2-phase separator (Souders–Brown)
"""
from __future__ import annotations
import math
from .diagrams import PUMP_SVG, HX_SVG, COLUMN_SVG, SEPARATOR_SVG
from .charts import line_chart


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
    if x is None or not math.isfinite(x):
        return x
    return round(x, n)


def _nps_select(D_m):
    """Pick the smallest standard NPS (in inches) that meets the calculated bore."""
    table = [
        (0.5, 15.80), (0.75, 20.93), (1.0, 26.64), (1.25, 35.05),
        (1.5, 40.89), (2.0, 52.50), (2.5, 62.71), (3.0, 77.93),
        (4.0, 102.26), (6.0, 154.05), (8.0, 202.72), (10.0, 254.46),
        (12.0, 303.23), (14.0, 333.34), (16.0, 381.00), (18.0, 428.66),
        (20.0, 477.82), (24.0, 574.65), (30.0, 717.55), (36.0, 863.60),
    ]
    D_mm = D_m * 1000.0
    for nps, id_mm in table:
        if id_mm >= D_mm:
            return nps, id_mm
    nps, id_mm = table[-1]
    return nps, id_mm


# =====================================================================
# 1. CENTRIFUGAL PUMP – FULL DESIGN
# =====================================================================
def pump_design(inp):
    Q_m3h   = _f(inp, "Q",          50.0)
    rho     = _f(inp, "rho",        1000.0)
    mu      = _f(inp, "mu",         0.001)
    P_suc   = _f(inp, "P_suc",      101325.0)   # absolute, Pa
    P_dis   = _f(inp, "P_dis",      400000.0)   # absolute, Pa
    H_stat  = _f(inp, "H_stat",     15.0)        # m static (+ above pump)
    L_suc   = _f(inp, "L_suc",      8.0)
    L_dis   = _f(inp, "L_dis",      30.0)
    K_suc   = _f(inp, "K_suc",      2.5)
    K_dis   = _f(inp, "K_dis",      8.0)
    Pv      = _f(inp, "Pv",         3170.0)      # vapour pressure, Pa
    eta_p   = _f(inp, "eta_pump",   0.70)
    eta_m   = _f(inp, "eta_motor",  0.92)
    margin  = _f(inp, "margin",     15.0)        # design margin %
    NPSHr   = _f(inp, "NPSHr",      3.0)
    v_suc_t = _f(inp, "v_suc",      1.5)         # target suction vel, m/s
    v_dis_t = _f(inp, "v_dis",      2.5)         # target discharge vel

    if rho <= 0 or eta_p <= 0 or eta_m <= 0:
        raise ValueError("Density and efficiencies must be > 0.")

    g       = 9.81
    Q       = Q_m3h / 3600.0                     # m³/s

    # Pipe sizing from target velocities
    D_suc   = math.sqrt(4.0 * Q / (math.pi * v_suc_t)) if v_suc_t > 0 else 0.0
    D_dis   = math.sqrt(4.0 * Q / (math.pi * v_dis_t)) if v_dis_t > 0 else 0.0
    nps_s, id_s = _nps_select(D_suc)
    nps_d, id_d = _nps_select(D_dis)
    D_s, D_d    = id_s / 1000.0, id_d / 1000.0
    v_s         = 4.0 * Q / (math.pi * D_s ** 2) if D_s else 0.0
    v_d         = 4.0 * Q / (math.pi * D_d ** 2) if D_d else 0.0
    Re_s        = rho * v_s * D_s / mu if mu > 0 else 0.0
    Re_d        = rho * v_d * D_d / mu if mu > 0 else 0.0

    # Friction factor (Swamee–Jain, ε = 0.045 mm commercial steel)
    eps         = 4.5e-5
    def f_d(re, D):
        if re <= 0 or D <= 0:
            return 0.0
        if re < 2300:
            return 64.0 / re
        return 0.25 / (math.log10(eps / (3.7 * D) + 5.74 / re ** 0.9)) ** 2
    f_s, f_dd = f_d(Re_s, D_s), f_d(Re_d, D_d)

    # Friction head (m of liquid)
    h_f_suc = (f_s * L_suc / D_s + K_suc) * v_s ** 2 / (2 * g) if D_s else 0.0
    h_f_dis = (f_dd * L_dis / D_d + K_dis) * v_d ** 2 / (2 * g) if D_d else 0.0

    # Pressure-drop head from P_suc / P_dis
    h_press = (P_dis - P_suc) / (rho * g)
    TDH_calc = H_stat + h_press + h_f_suc + h_f_dis
    TDH      = TDH_calc * (1.0 + margin / 100.0)

    # Power
    P_hyd  = rho * g * Q * TDH                     # W (hydraulic at design TDH)
    P_brk  = P_hyd / eta_p                         # shaft / brake power
    P_mot  = P_brk / eta_m                         # electrical motor input
    # Standard motor sizing (next IEC frame)
    iec_kw = [0.75, 1.1, 1.5, 2.2, 3.0, 4.0, 5.5, 7.5, 11, 15, 18.5,
              22, 30, 37, 45, 55, 75, 90, 110, 132, 160, 200, 250, 315, 400]
    mot_std = next((k for k in iec_kw if k * 1000 >= P_mot), iec_kw[-1])

    # NPSH available
    NPSHa = (P_suc - Pv) / (rho * g) + 0.0 - h_f_suc      # static head added separately
    # If suction tank is above pump (H_stat from suction surface to pump centerline
    # is ambiguous) – we report base NPSHa using head above pump = 0 unless user
    # specified via h_static_suc:
    h_static_suc = _f(inp, "h_static_suc", 1.0)
    NPSHa = (P_suc - Pv) / (rho * g) + h_static_suc - h_f_suc
    NPSH_margin = NPSHa - NPSHr

    # Specific speed (US units, for reference): Ns = N·sqrt(Q_gpm)/H_ft^0.75
    N_rpm = _f(inp, "N_rpm", 2950.0)
    Q_gpm = Q_m3h * 4.40287
    H_ft  = TDH * 3.28084
    Ns    = N_rpm * math.sqrt(Q_gpm) / (H_ft ** 0.75) if H_ft > 0 else 0.0

    cavitation_ok = NPSH_margin >= 0.6     # 0.6 m minimum margin rule of thumb

    results = [
        _r(_round(Q_m3h, 3),        "m³/h",     "Design flow Q"),
        _r(_round(TDH_calc, 3),     "m",        "Calculated TDH (no margin)"),
        _r(_round(TDH, 3),          "m",        f"Design TDH (incl. {margin}% margin)"),
        _r(_round(P_hyd / 1000, 3), "kW",       "Hydraulic power"),
        _r(_round(P_brk / 1000, 3), "kW",       "Brake (shaft) power"),
        _r(_round(P_mot / 1000, 3), "kW",       "Motor input power"),
        _r(mot_std,                 "kW",       "Standard motor (next IEC)"),
        _r(_round(NPSHa, 3),        "m",        "NPSH available"),
        _r(_round(NPSH_margin, 3),  "m",        "NPSH margin (NPSHa − NPSHr)"),
        _r("OK" if cavitation_ok else "REVIEW", "", "Cavitation check"),
        _r(f"{nps_s}\"",            "NPS",      "Suction line size"),
        _r(_round(v_s, 3),          "m/s",      "Suction velocity"),
        _r(f"{nps_d}\"",            "NPS",      "Discharge line size"),
        _r(_round(v_d, 3),          "m/s",      "Discharge velocity"),
        _r(_round(Ns, 1),           "(US)",     "Specific speed Ns @ N_rpm"),
    ]

    datasheet = [
        _ds("Pump Datasheet – Process Data", [
            ["Service / Tag",                inp.get("tag", "P-101")],
            ["Liquid",                       inp.get("fluid", "Water")],
            ["Density ρ",                    f"{rho} kg/m³"],
            ["Viscosity μ",                  f"{mu} Pa·s"],
            ["Vapour pressure Pv",           f"{Pv} Pa"],
            ["Operating temperature",        f"{inp.get('T_op', 25)} °C"],
        ]),
        _ds("Pump Datasheet – Hydraulic Design", [
            ["Capacity (rated)",             f"{Q_m3h:.2f} m³/h ({Q_gpm:.1f} US gpm)"],
            ["Suction pressure (abs)",       f"{P_suc} Pa"],
            ["Discharge pressure (abs)",     f"{P_dis} Pa"],
            ["Static head",                  f"{H_stat} m"],
            ["Suction friction loss",        f"{h_f_suc:.2f} m"],
            ["Discharge friction loss",      f"{h_f_dis:.2f} m"],
            ["Total dynamic head (rated)",   f"{TDH_calc:.2f} m"],
            ["Design TDH (with margin)",     f"{TDH:.2f} m"],
            ["NPSH available",               f"{NPSHa:.2f} m"],
            ["NPSH required",                f"{NPSHr:.2f} m"],
            ["NPSH margin",                  f"{NPSH_margin:.2f} m"],
        ]),
        _ds("Pump Datasheet – Driver", [
            ["Pump efficiency",              f"{eta_p*100:.0f} %"],
            ["Motor efficiency",             f"{eta_m*100:.0f} %"],
            ["Hydraulic power",              f"{P_hyd/1000:.2f} kW"],
            ["Brake power",                  f"{P_brk/1000:.2f} kW"],
            ["Motor input power",            f"{P_mot/1000:.2f} kW"],
            ["Selected motor (std IEC)",     f"{mot_std} kW"],
            ["Speed",                        f"{N_rpm:.0f} rpm"],
            ["Specific speed Ns (US)",       f"{Ns:.0f}"],
        ]),
        _ds("Pump Datasheet – Piping", [
            ["Suction line",                 f"{nps_s}\" NPS  (ID = {id_s:.1f} mm)"],
            ["Suction velocity",             f"{v_s:.2f} m/s   (target {v_suc_t})"],
            ["Discharge line",               f"{nps_d}\" NPS  (ID = {id_d:.1f} mm)"],
            ["Discharge velocity",           f"{v_d:.2f} m/s   (target {v_dis_t})"],
        ]),
    ]

    return {
        "results":   results,
        "datasheet": datasheet,
        "diagram":   PUMP_SVG,
        "charts":    _pump_curve_chart(Q_m3h, TDH, H_stat + h_press, h_f_suc + h_f_dis,
                                       NPSHa, NPSHr),
        "notes": [
            "TDH = ΔZ + (Pdis − Psuc)/(ρ·g) + h_f_suction + h_f_discharge",
            "P_hyd = ρ·g·Q·TDH ; P_shaft = P_hyd/η_pump ; P_motor = P_shaft/η_motor",
            "NPSHa = (Psuc − Pv)/(ρ·g) + h_static_suc − h_f_suc  (use absolute pressures)",
            "Friction factor: Swamee–Jain (ε = 0.045 mm commercial steel).",
            "Pipe sized to user target velocities (default 1.5 m/s suction, 2.5 m/s discharge).",
        ],
    }


def _pump_curve_chart(Q_design_m3h, H_design, H_static_total, h_friction_design,
                      NPSHa, NPSHr):
    """Pump head curve (parabolic), system curve, and NPSH-vs-Q chart."""
    # Pump curve: H_p = H0 − k·Q²,  H0 = 1.25·H_design,  passes through (Q_d, H_d)
    H0 = 1.25 * H_design
    k_p = (H0 - H_design) / (Q_design_m3h ** 2) if Q_design_m3h > 0 else 0.0
    # System curve: H_sys = H_static + k_s·Q²,  k_s from friction at design Q
    k_s = (h_friction_design) / (Q_design_m3h ** 2) if Q_design_m3h > 0 else 0.0
    H_static = H_static_total

    Q_max = Q_design_m3h * 1.6
    pts_pump   = []
    pts_system = []
    pts_eff    = []
    for i in range(0, 41):
        Q = Q_max * i / 40.0
        Hp = max(0.0, H0 - k_p * Q * Q)
        Hs = H_static + k_s * Q * Q
        pts_pump.append((Q, Hp))
        pts_system.append((Q, Hs))
        # Efficiency curve – simple parabola peaking at design Q
        eta_max = 0.78
        eta = max(0.0, eta_max * (1.0 - ((Q - Q_design_m3h) / (Q_design_m3h * 1.1)) ** 2))
        pts_eff.append((Q, eta * 100.0))

    op = [(Q_design_m3h, H_design)]
    chart_curves = line_chart(
        "Pump Curve (H–Q) and System Curve",
        "Flow Q (m³/h)", "Head H (m)",
        [
            {"name": "Pump curve",   "points": pts_pump,   "color": "#0F2C4A"},
            {"name": "System curve", "points": pts_system, "color": "#234A78", "dashed": True},
            {"name": "Operating",    "points": op,         "color": "#B0203A", "marker": True},
        ],
    )
    chart_eff = line_chart(
        "Estimated Efficiency Curve",
        "Flow Q (m³/h)", "Efficiency η (%)",
        [{"name": "η", "points": pts_eff, "color": "#3F7A4A"}],
        y_min=0, y_max=100,
    )
    # NPSHa / NPSHr vs Q (NPSHa drops with Q² friction, NPSHr grows ~Q^1.5)
    pts_a, pts_r = [], []
    for i in range(1, 41):
        Q = Q_max * i / 40.0
        # Approximation
        npsha = NPSHa - 0.7 * (Q / Q_design_m3h) ** 2 + 0.3
        npshr = NPSHr * (Q / Q_design_m3h) ** 1.5
        pts_a.append((Q, max(0.0, npsha)))
        pts_r.append((Q, npshr))
    chart_npsh = line_chart(
        "NPSH available vs required",
        "Flow Q (m³/h)", "NPSH (m)",
        [
            {"name": "NPSHa", "points": pts_a, "color": "#0F2C4A"},
            {"name": "NPSHr", "points": pts_r, "color": "#B0203A", "dashed": True},
        ],
    )
    return [
        {"title": "Pump curve",       "svg": chart_curves},
        {"title": "Efficiency",       "svg": chart_eff},
        {"title": "NPSH check",       "svg": chart_npsh},
    ]


def _hx_effectiveness(NTU, Cr, arrangement):
    """Effectiveness ε(NTU, Cr) for common HX arrangements."""
    a = arrangement.lower()
    if NTU <= 0:
        return 0.0
    if "counter" in a:
        if abs(Cr - 1.0) < 1e-6:
            return NTU / (1.0 + NTU)
        e = math.exp(-NTU * (1.0 - Cr))
        return (1.0 - e) / (1.0 - Cr * e)
    if "parallel" in a:
        return (1.0 - math.exp(-NTU * (1.0 + Cr))) / (1.0 + Cr)
    if "shell" in a or "1-2" in a:
        # 1 shell – 2 tube passes
        s = math.sqrt(1.0 + Cr * Cr)
        e = math.exp(-NTU * s)
        return 2.0 / ((1.0 + Cr) + s * (1.0 + e) / (1.0 - e))
    if "cross" in a:
        # Cross-flow, both fluids unmixed – approximation
        return 1.0 - math.exp((1.0 / Cr) * (NTU ** 0.22) *
                              (math.exp(-Cr * NTU ** 0.78) - 1.0))
    # Default: counter
    if abs(Cr - 1.0) < 1e-6:
        return NTU / (1.0 + NTU)
    e = math.exp(-NTU * (1.0 - Cr))
    return (1.0 - e) / (1.0 - Cr * e)


def _hx_ntu_from_eff(eps, Cr, arrangement):
    """Inverse: NTU(ε, Cr) — closed-form where possible, bisection otherwise."""
    a = arrangement.lower()
    if eps <= 0:
        return 0.0
    if "counter" in a:
        if abs(Cr - 1.0) < 1e-6:
            return eps / (1.0 - eps) if eps < 1 else 1e6
        return math.log((1.0 - eps) / (1.0 - eps * Cr)) / (Cr - 1.0)
    if "parallel" in a:
        if eps * (1.0 + Cr) >= 1.0:
            return 1e6
        return -math.log(1.0 - eps * (1.0 + Cr)) / (1.0 + Cr)
    # bisection for shell-and-tube / cross
    lo, hi = 1e-4, 50.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if _hx_effectiveness(mid, Cr, arrangement) < eps:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# =====================================================================
# 2. SHELL & TUBE HX – LMTD or NTU METHOD WITH TEMA DATASHEET
# =====================================================================
def hx_design(inp):
    method = (inp.get("method") or "LMTD").strip().upper()
    arrangement = (inp.get("arrangement") or "Counter-current").strip()
    # Hot stream
    m_h    = _f(inp, "m_hot",   2.5)
    Cp_h   = _f(inp, "Cp_hot",  4180.0)
    Th_in  = _f(inp, "Th_in",   120.0)
    Th_out = _f(inp, "Th_out",  60.0)
    # Cold stream
    m_c    = _f(inp, "m_cold",  3.0)
    Cp_c   = _f(inp, "Cp_cold", 4180.0)
    Tc_in  = _f(inp, "Tc_in",   30.0)
    Tc_out = _f(inp, "Tc_out",  0.0)
    # Geometry / U
    U      = _f(inp, "U",       500.0)
    Ft     = _f(inp, "Ft",      0.92)
    do_mm  = _f(inp, "do",      19.05)            # tube OD, mm (3/4")
    BWG    = _f(inp, "BWG",     14)
    L_t    = _f(inp, "L_tube",  6.0)              # tube length, m
    PT     = _f(inp, "PT",      1.25)             # pitch ratio
    layout = (inp.get("layout") or "Triangular").strip()
    n_pass = int(_f(inp, "n_pass", 2))
    foul   = _f(inp, "fouling", 0.00035)          # m²K/W (≈ Rd combined)

    if Cp_h <= 0 or Cp_c <= 0:
        raise ValueError("Cp must be > 0")
    if m_h <= 0:
        raise ValueError("Hot mass flow must be > 0")

    # Duty Q (W) from hot side
    Q = m_h * Cp_h * (Th_in - Th_out)
    if Tc_out in (None, 0.0):
        if m_c <= 0 or Cp_c <= 0:
            raise ValueError("Provide either cold outlet T or cold flow + Cp.")
        Tc_out = Tc_in + Q / (m_c * Cp_c)
    else:
        # back-out m_c if blank
        if m_c <= 0:
            m_c = Q / (Cp_c * (Tc_out - Tc_in))

    # Capacity rates and NTU/effectiveness analysis (always computed)
    C_h     = m_h * Cp_h
    C_c     = m_c * Cp_c
    C_min   = min(C_h, C_c)
    C_max   = max(C_h, C_c)
    Cr      = C_min / C_max if C_max > 0 else 0.0
    Q_max   = C_min * (Th_in - Tc_in)
    eps_act = Q / Q_max if Q_max > 0 else 0.0

    Uc      = U                                      # clean
    Ud      = 1.0 / (1.0 / U + foul)                 # dirty (service)

    if method == "NTU":
        # NTU sized from required effectiveness (ε from terminal Ts)
        if eps_act >= 1.0:
            raise ValueError("Required effectiveness ≥ 1 — temperature cross.")
        NTU_req = _hx_ntu_from_eff(eps_act, Cr, arrangement)
        UA      = NTU_req * C_min
        A_req   = UA / Ud
        # LMTD reported for comparison
        dT1, dT2 = (Th_in - Tc_out), (Th_out - Tc_in)
        LMTD = (dT1 - dT2) / math.log(dT1 / dT2) if (dT1 > 0 and dT2 > 0 and dT1 != dT2) else max(dT1, dT2)
    else:
        # LMTD method (default)
        dT1, dT2 = (Th_in - Tc_out), (Th_out - Tc_in)
        if dT1 <= 0 or dT2 <= 0:
            raise ValueError("Temperature cross detected – review terminal temperatures.")
        LMTD    = (dT1 - dT2) / math.log(dT1 / dT2) if dT1 != dT2 else dT1
        A_req   = Q / (Ud * Ft * LMTD)
        UA      = Ud * A_req
        NTU_req = UA / C_min if C_min > 0 else 0.0

    # Tube count (per Kern/Towler shortcut)
    do      = do_mm / 1000.0
    a_one   = math.pi * do * L_t                   # area per tube (outside)
    Nt      = max(1, math.ceil(A_req / a_one))

    # Bundle / shell diameter via tube-count layout factor (Kern)
    if layout.lower().startswith("tri"):
        if n_pass == 1:
            K1, n1 = 0.319, 2.142
        elif n_pass == 2:
            K1, n1 = 0.249, 2.207
        elif n_pass == 4:
            K1, n1 = 0.175, 2.285
        else:
            K1, n1 = 0.0743, 2.499
    else:  # square pitch
        if n_pass == 1:
            K1, n1 = 0.215, 2.207
        elif n_pass == 2:
            K1, n1 = 0.156, 2.291
        elif n_pass == 4:
            K1, n1 = 0.158, 2.263
        else:
            K1, n1 = 0.0402, 2.617
    Db_mm   = do_mm * (Nt / K1) ** (1.0 / n1)
    clear   = 50.0
    Ds_mm   = Db_mm + clear
    pitch_mm = PT * do_mm
    B_mm    = Ds_mm / 5.0
    A_shell = (Ds_mm / 1000.0) * (B_mm / 1000.0) * ((pitch_mm - do_mm) / pitch_mm)

    tema    = (inp.get("TEMA") or "AES").upper()

    results = [
        _r(method,                 "",     "Design method"),
        _r(arrangement,            "",     "Flow arrangement"),
        _r(_round(Q / 1000, 3),    "kW",   "Heat duty Q"),
        _r(_round(eps_act, 4),     "-",    "Effectiveness ε"),
        _r(_round(Cr, 4),          "-",    "Capacity ratio Cr = Cmin/Cmax"),
        _r(_round(NTU_req, 4),     "-",    "NTU = UA/Cmin"),
        _r(_round(LMTD, 3),        "°C",   "LMTD (counter-current)"),
        _r(_round(Ud, 1),          "W/m²K","Service U (with fouling)"),
        _r(_round(UA, 1),          "W/K",  "UA (= NTU·Cmin)"),
        _r(_round(A_req, 3),       "m²",   "Required heat-transfer area"),
        _r(Nt,                     "-",    "Number of tubes"),
        _r(_round(Db_mm, 1),       "mm",   "Bundle diameter Db"),
        _r(_round(Ds_mm, 1),       "mm",   "Shell ID Ds"),
        _r(_round(pitch_mm, 2),    "mm",   "Tube pitch"),
        _r(_round(B_mm, 1),        "mm",   "Baffle spacing (Ds/5)"),
        _r(_round(Tc_out, 2),      "°C",   "Cold outlet temperature"),
    ]

    datasheet = [
        _ds("Heat Exchanger – Service", [
            ["Service / Tag",          inp.get("tag", "E-101")],
            ["Design method",          method],
            ["Flow arrangement",       arrangement],
            ["TEMA type",              tema],
            ["Position",               inp.get("pos", "Horizontal")],
            ["Hot fluid",              inp.get("hot",  "Process")],
            ["Cold fluid",             inp.get("cold", "Cooling water")],
        ]),
        _ds("Heat Exchanger – Process Data", [
            ["", "Hot side", "Cold side"],
            ["Mass flow (kg/s)",       f"{m_h:.3f}",   f"{m_c:.3f}"],
            ["Cp (J/kg·K)",            f"{Cp_h}",      f"{Cp_c}"],
            ["Inlet T (°C)",           f"{Th_in}",     f"{Tc_in}"],
            ["Outlet T (°C)",          f"{Th_out}",    f"{Tc_out:.2f}"],
            ["ΔT (°C)",                f"{Th_in-Th_out:.1f}", f"{Tc_out-Tc_in:.1f}"],
            ["Capacity rate C (W/K)",  f"{C_h:.1f}",   f"{C_c:.1f}"],
        ]),
        _ds("Heat Exchanger – Thermal Design", [
            ["Heat duty Q",            f"{Q/1000:.2f} kW"],
            ["Q max (Cmin·ΔT)",        f"{Q_max/1000:.2f} kW"],
            ["Effectiveness ε",        f"{eps_act:.4f}"],
            ["Capacity ratio Cr",      f"{Cr:.4f}"],
            ["NTU",                    f"{NTU_req:.4f}"],
            ["UA",                     f"{UA:.1f} W/K"],
            ["LMTD (counter)",         f"{LMTD:.2f} °C"],
            ["Ft correction",          f"{Ft:.2f}"],
            ["Effective ΔT = Ft·LMTD", f"{Ft*LMTD:.2f} °C"],
            ["U clean",                f"{Uc:.0f} W/m²K"],
            ["U service (fouled)",     f"{Ud:.0f} W/m²K"],
            ["Combined fouling Rd",    f"{foul} m²K/W"],
            ["Required area",          f"{A_req:.2f} m²"],
        ]),
        _ds("Heat Exchanger – Mechanical / TEMA", [
            ["Tube OD",                f"{do_mm} mm  (BWG {BWG})"],
            ["Tube length",            f"{L_t} m"],
            ["Layout",                 layout],
            ["Pitch ratio / pitch",    f"{PT}  ({pitch_mm:.1f} mm)"],
            ["Number of passes",       f"{n_pass}"],
            ["Number of tubes Nt",     f"{Nt}"],
            ["Bundle diameter Db",     f"{Db_mm:.0f} mm"],
            ["Shell ID Ds",            f"{Ds_mm:.0f} mm"],
            ["Baffle spacing",         f"{B_mm:.0f} mm"],
            ["Shell flow area (est.)", f"{A_shell*1e4:.1f} cm²"],
        ]),
    ]

    # ---- Charts ---------------------------------------------------------
    charts = []
    # 1) Temperature profile along (normalised) length
    arr = arrangement.lower()
    xs = [i / 20 for i in range(21)]
    if "parallel" in arr:
        hot  = [(x, Th_in - (Th_in - Th_out) * x) for x in xs]
        cold = [(x, Tc_in + (Tc_out - Tc_in) * x) for x in xs]
    else:
        # Counter-current (and shell&tube/cross approximated as counter terminals)
        hot  = [(x, Th_in - (Th_in - Th_out) * x) for x in xs]
        cold = [(x, Tc_out - (Tc_out - Tc_in) * x) for x in xs]
    charts.append({
        "title": "Temperature profile",
        "svg": line_chart(
            "Temperature Profile along HX",
            "Normalised length", "T (°C)",
            [
                {"name": "Hot",  "points": hot,  "color": "#B0203A"},
                {"name": "Cold", "points": cold, "color": "#234A78"},
            ],
        ),
    })
    # 2) ε–NTU curve at given Cr (highlight design point)
    ntu_pts = [n / 10 for n in range(1, 81)]
    eff_curve = [(n, _hx_effectiveness(n, Cr, arrangement)) for n in ntu_pts]
    design_pt = [(NTU_req, eps_act)]
    charts.append({
        "title": "ε–NTU curve",
        "svg": line_chart(
            f"ε vs NTU  ({arrangement}, Cr={Cr:.2f})",
            "NTU", "Effectiveness ε",
            [
                {"name": "ε(NTU)",       "points": eff_curve, "color": "#0F2C4A"},
                {"name": "Design point", "points": design_pt, "color": "#B0203A",
                 "marker": True},
            ],
            y_min=0, y_max=1, x_min=0, x_max=8,
        ),
    })

    return {
        "results":   results,
        "datasheet": datasheet,
        "diagram":   HX_SVG,
        "charts":    charts,
        "notes": [
            "LMTD method: A = Q / (U_service · Ft · LMTD).",
            "NTU method: ε = Q/Qmax, NTU(ε,Cr) inverted from arrangement formula → UA = NTU·Cmin → A = UA/U.",
            "Effectiveness formulas: counter, parallel, shell-and-tube 1-2, cross-flow (both unmixed).",
            "Bundle diameter (Kern/Towler): Db = do·(Nt/K1)^(1/n1).",
            "Baffle spacing default = Ds/5 (Kern). Shell clearance = 50 mm.",
        ],
    }


# =====================================================================
# 3. DISTILLATION COLUMN – FUG SHORTCUT + DATASHEET
# =====================================================================
def column_design(inp):
    method = (inp.get("method") or "FUG (shortcut)").strip()
    F      = _f(inp, "F",    100.0)
    zF     = _f(inp, "zF",   0.4)
    xD     = _f(inp, "xD",   0.95)
    xB     = _f(inp, "xB",   0.05)
    q      = _f(inp, "q",    1.0)
    alpha  = _f(inp, "alpha", 2.5)
    R_mult = _f(inp, "R_mult", 1.5)        # R = R_mult × Rmin
    rho_L  = _f(inp, "rho_L", 750.0)
    rho_V  = _f(inp, "rho_V", 3.0)
    K_SB   = _f(inp, "K_SB",  0.06)        # Souders–Brown m/s
    eta_t  = _f(inp, "eta_tray", 0.65)
    HETP   = _f(inp, "HETP", 0.6)          # m / theoretical stage (tray spacing-equiv.)
    P_top  = _f(inp, "P_top", 101325.0)

    if not (0 < xB < zF < xD < 1):
        raise ValueError("Require 0 < xB < zF < xD < 1.")
    if alpha <= 1:
        raise ValueError("Relative volatility α must be > 1.")

    # Material balance (light component basis)
    D = F * (zF - xB) / (xD - xB)
    B = F - D

    # Fenske – minimum stages (theoretical)
    Nmin = math.log((xD / (1 - xD)) * ((1 - xB) / xB)) / math.log(alpha)

    # Underwood θ for q ≠ 1 (binary): θ between 1 and α
    # For binary mixture, Rmin formula:
    # Rmin = (1/(α-1)) * (xD/zF − α(1-xD)/(1-zF)) when q = 1 (saturated liquid feed)
    if abs(q - 1.0) < 1e-6:
        Rmin = (1.0 / (alpha - 1.0)) * (xD / zF - alpha * (1.0 - xD) / (1.0 - zF))
    else:
        # Solve α·zF/(α−θ) + (1−zF)/(1−θ) = 1 − q  (Underwood eq.)
        def under(th):
            return alpha * zF / (alpha - th) + (1 - zF) / (1 - th) - (1 - q)
        lo, hi = 1.0001, alpha - 0.0001
        # Bisection
        flo, fhi = under(lo), under(hi)
        if flo * fhi > 0:
            theta = (1.0 + alpha) / 2.0
        else:
            for _ in range(80):
                mid = 0.5 * (lo + hi)
                fm = under(mid)
                if fm * flo <= 0:
                    hi, fhi = mid, fm
                else:
                    lo, flo = mid, fm
            theta = 0.5 * (lo + hi)
        Rmin = alpha * xD / (alpha - theta) + (1 - xD) / (1 - theta) - 1.0

    Rmin = max(Rmin, 0.001)
    R    = R_mult * Rmin

    # Gilliland correlation (Eduljee form) – always reported
    X = (R - Rmin) / (R + 1.0)
    Y_g = 1.0 - math.exp(((1.0 + 54.4 * X) / (11.0 + 117.2 * X)) * (X - 1.0) / math.sqrt(X)) \
        if X > 0 else 0.0
    N_FUG = (Nmin + Y_g) / (1.0 - Y_g) if Y_g < 1 else Nmin * 2

    # McCabe–Thiele stepping (constant α, equimolar overflow)
    mt_stages, mt_steps = _mccabe_thiele(alpha, xD, xB, zF, q, R)

    if method.lower().startswith("mccabe"):
        N_theor = mt_stages
    else:
        N_theor = N_FUG

    N_actual = N_theor / eta_t

    # Kirkbride feed-stage location
    # log10(Nr/Ns) = 0.206·log10[(B/D)·(xB·(1−zF)²)/(zF·(1−xB)²·xD²)] inverse?
    # Use the standard Kirkbride correlation:
    arg = (B / D) * ((1.0 - zF) / zF) * (xB / (1.0 - xD)) ** 2
    if arg > 0:
        ratio = arg ** 0.206
        Nr_over_Ns = ratio
        # Nr + Ns = N_actual
        Ns = N_actual / (1.0 + Nr_over_Ns)
        Nr = N_actual - Ns
    else:
        Nr = Ns = N_actual / 2.0

    # Column diameter (Souders–Brown, top tray vapour load)
    L_top = R * D                          # liquid reflux flow (kmol/h equivalent)
    V_top = (R + 1.0) * D                  # vapour flow at top
    # Convert to mass flow assuming average MW from feed (approx)
    MW    = _f(inp, "MW", 50.0)
    m_V   = V_top * MW / 3600.0            # kg/s (if F is kmol/h)
    v_max = K_SB * math.sqrt((rho_L - rho_V) / rho_V)
    v_des = 0.80 * v_max
    A_x   = m_V / (rho_V * v_des) if v_des > 0 else 0.0
    D_col = math.sqrt(4.0 * A_x / math.pi) if A_x > 0 else 0.0

    H_col = N_actual * HETP + 4.0          # add 4 m for sumps and disengaging
    results = [
        _r(method,             "",       "Design method"),
        _r(_round(D,    3),    "kmol/h", "Distillate D"),
        _r(_round(B,    3),    "kmol/h", "Bottoms B"),
        _r(_round(Nmin, 3),    "-",      "Minimum stages Nmin (Fenske)"),
        _r(_round(Rmin, 3),    "-",      "Minimum reflux Rmin (Underwood)"),
        _r(_round(R,    3),    "-",      f"Operating reflux R = {R_mult}·Rmin"),
        _r(_round(N_FUG, 2),   "-",      "N theoretical (FUG / Gilliland)"),
        _r(_round(mt_stages,2),"-",      "N theoretical (McCabe–Thiele)"),
        _r(_round(N_theor, 2), "-",      f"N theoretical (selected: {method})"),
        _r(_round(N_actual,2), "-",      f"Actual trays (η = {eta_t})"),
        _r(_round(Nr,   2),    "-",      "Trays above feed (Kirkbride)"),
        _r(_round(Ns,   2),    "-",      "Trays below feed (Kirkbride)"),
        _r(_round(v_max,3),    "m/s",    "Flooding velocity (Souders–Brown)"),
        _r(_round(D_col,3),    "m",      "Column diameter (80% flood)"),
        _r(_round(H_col,2),    "m",      "Column height (estimated)"),
    ]

    datasheet = [
        _ds("Distillation Column – Service", [
            ["Tag",                inp.get("tag", "T-101")],
            ["Service",            inp.get("service", "Binary separation")],
            ["Design method",      method],
            ["Top pressure",       f"{P_top} Pa"],
        ]),
        _ds("Distillation Column – Process Data", [
            ["Feed F",             f"{F} kmol/h"],
            ["Feed composition zF",f"{zF}"],
            ["Distillate xD",      f"{xD}"],
            ["Bottoms xB",         f"{xB}"],
            ["q (feed condition)", f"{q}"],
            ["Relative volatility α", f"{alpha}"],
            ["Distillate D",       f"{D:.2f} kmol/h"],
            ["Bottoms B",          f"{B:.2f} kmol/h"],
        ]),
        _ds("Distillation Column – Shortcut Design", [
            ["Nmin (Fenske)",          f"{Nmin:.2f}"],
            ["Rmin (Underwood)",       f"{Rmin:.3f}"],
            ["R / Rmin",               f"{R_mult}"],
            ["Operating reflux R",     f"{R:.3f}"],
            ["N theoretical (FUG)",    f"{N_FUG:.2f}"],
            ["N theoretical (MT)",     f"{mt_stages:.2f}"],
            ["N theoretical (selected)", f"{N_theor:.2f}"],
            ["Tray efficiency",        f"{eta_t}"],
            ["N actual",               f"{N_actual:.1f}"],
            ["Trays above feed",       f"{Nr:.1f}"],
            ["Trays below feed",       f"{Ns:.1f}"],
        ]),
        _ds("Distillation Column – Mechanical", [
            ["Liquid density",     f"{rho_L} kg/m³"],
            ["Vapour density",     f"{rho_V} kg/m³"],
            ["Avg. MW",            f"{MW} g/mol"],
            ["Top vapour mass flow", f"{m_V:.3f} kg/s"],
            ["Souders–Brown K",    f"{K_SB} m/s"],
            ["Flooding velocity",  f"{v_max:.3f} m/s"],
            ["Design velocity (80%)", f"{v_des:.3f} m/s"],
            ["Column diameter",    f"{D_col:.2f} m"],
            ["HETP / tray spacing", f"{HETP} m"],
            ["Column tangent height (est.)", f"{H_col:.1f} m"],
        ]),
    ]

    return {
        "results":   results,
        "datasheet": datasheet,
        "diagram":   COLUMN_SVG,
        "charts":    _column_charts(alpha, xD, xB, zF, q, R, Rmin, mt_steps),
        "notes": [
            "Material balance: D = F·(zF − xB)/(xD − xB), B = F − D.",
            "Fenske: Nmin = ln[(xD/(1−xD))·((1−xB)/xB)] / ln α.",
            "Underwood Rmin from θ between 1 and α.",
            "Gilliland (Eduljee): Y = 1 − exp[((1+54.4X)/(11+117.2X))·((X−1)/√X)], X = (R−Rmin)/(R+1).",
            "McCabe–Thiele: stage-by-stage stepping between equilibrium curve and operating lines.",
            "Kirkbride locates feed: log10(Nr/Ns) = 0.206·log10[(B/D)·(1−zF)/zF·(xB/(1−xD))²].",
            "Diameter from Souders–Brown at 80 % of flooding.",
        ],
    }


def _mccabe_thiele(alpha, xD, xB, zF, q, R):
    """Step a binary McCabe–Thiele construction. Constant α equilibrium.
    Returns (n_stages, list_of_(x,y)_polyline_points for SVG plotting)."""
    # Operating lines:
    # Rectifying:  y = (R/(R+1))·x + xD/(R+1)
    # Stripping:   y = ((Vm·B − ...))   approximated from x-intercept (xB,xB) through feed pinch
    # Use feed-stage intercept: q-line meets ROL at (x*, y*)
    #    q-line: y = q/(q-1)·x − zF/(q-1) for q != 1
    #    saturated liquid (q=1): vertical at x = zF
    R_ratio = R / (R + 1.0)
    rol = (R_ratio, xD / (R + 1.0))         # slope, intercept
    if abs(q - 1.0) < 1e-6:
        x_int = zF
        y_int = R_ratio * x_int + rol[1]
    else:
        # Solve y = R_ratio·x + b   and   y = q/(q-1)·x − zF/(q-1)
        m_q = q / (q - 1.0)
        b_q = -zF / (q - 1.0)
        x_int = (rol[1] - b_q) / (m_q - R_ratio)
        y_int = R_ratio * x_int + rol[1]

    # Stripping line: passes through (xB, xB) and (x_int, y_int)
    if x_int != xB:
        slope_s = (y_int - xB) / (x_int - xB)
    else:
        slope_s = 1.0
    intercept_s = xB - slope_s * xB

    def y_eq(x):
        return alpha * x / (1.0 + (alpha - 1.0) * x)

    def x_eq(y):
        # invert α-form
        return y / (alpha - (alpha - 1.0) * y)

    def y_op(x):
        if x >= x_int:
            return rol[0] * x + rol[1]
        return slope_s * x + intercept_s

    # Step from (xD, xD) downward to xB
    pts = [(xD, xD)]
    x = xD
    n = 0
    max_steps = 200
    while x > xB and n < max_steps:
        # Horizontal to equilibrium curve: x_new such that y_eq(x_new) = current y
        y_cur = y_op(x) if x != xD else xD
        # actually current point is (x, y_op(x))? We start at (xD, xD) ON the y=x line then
        # step horizontally to equilibrium (going LEFT): x_new = x_eq(xD)
        # Use convention: from (x, y) on op line, go left to eq curve at same y
        x_new = x_eq(y_op(x)) if n > 0 else x_eq(xD)
        pts.append((x_new, y_op(x) if n > 0 else xD))
        # Vertical down to op line: y_new = y_op(x_new)
        y_new = y_op(x_new)
        pts.append((x_new, y_new))
        n += 1
        x = x_new
        if x <= xB:
            break
    return n, pts


def _column_charts(alpha, xD, xB, zF, q, R, Rmin, mt_steps):
    # Equilibrium curve
    eq_pts = []
    for i in range(101):
        x = i / 100.0
        eq_pts.append((x, alpha * x / (1.0 + (alpha - 1.0) * x)))
    # y = x diagonal
    diag = [(0.0, 0.0), (1.0, 1.0)]
    # Operating lines
    R_ratio = R / (R + 1.0)
    rol_pts = [(0.0, xD / (R + 1.0)), (xD, xD)]
    if abs(q - 1.0) < 1e-6:
        x_int = zF
        y_int = R_ratio * x_int + xD / (R + 1.0)
        q_pts = [(zF, zF), (zF, y_int)]
    else:
        m_q = q / (q - 1.0)
        b_q = -zF / (q - 1.0)
        x_int = (xD / (R + 1.0) - b_q) / (m_q - R_ratio)
        y_int = R_ratio * x_int + xD / (R + 1.0)
        q_pts = [(zF, zF), (x_int, y_int)]
    sol_pts = [(xB, xB), (x_int, y_int)]

    chart_mt = line_chart(
        "McCabe–Thiele Diagram",
        "x  (liquid mole fraction)", "y  (vapour mole fraction)",
        [
            {"name": "y = αx / (1+(α−1)x)", "points": eq_pts,  "color": "#0F2C4A"},
            {"name": "y = x",               "points": diag,    "color": "#6A7480", "dashed": True},
            {"name": "Rectifying",          "points": rol_pts, "color": "#234A78"},
            {"name": "Stripping",           "points": sol_pts, "color": "#3F7A4A"},
            {"name": "q-line",              "points": q_pts,   "color": "#A8742C", "dashed": True},
            {"name": "Stages",              "points": mt_steps,"color": "#B0203A"},
        ],
        x_min=0, x_max=1, y_min=0, y_max=1,
    )

    # Gilliland curve N–Nmin/(N+1) vs (R−Rmin)/(R+1)
    gpts = []
    for i in range(1, 100):
        Xv = i / 100.0
        Yv = 1.0 - math.exp(((1.0 + 54.4 * Xv) / (11.0 + 117.2 * Xv)) *
                            (Xv - 1.0) / math.sqrt(Xv))
        gpts.append((Xv, Yv))
    Xd = (R - Rmin) / (R + 1.0)
    if Xd > 0:
        Yd = 1.0 - math.exp(((1.0 + 54.4 * Xd) / (11.0 + 117.2 * Xd)) *
                            (Xd - 1.0) / math.sqrt(Xd))
    else:
        Yd = 0.0
    chart_gil = line_chart(
        "Gilliland Correlation",
        "(R − Rmin)/(R + 1)", "(N − Nmin)/(N + 1)",
        [
            {"name": "Eduljee",      "points": gpts,        "color": "#0F2C4A"},
            {"name": "Design point", "points": [(Xd, Yd)],  "color": "#B0203A", "marker": True},
        ],
        x_min=0, x_max=1, y_min=0, y_max=1,
    )
    return [
        {"title": "McCabe–Thiele",     "svg": chart_mt},
        {"title": "Gilliland",         "svg": chart_gil},
    ]


# =====================================================================
# 4. VERTICAL 2-PHASE SEPARATOR
# =====================================================================
def separator_design(inp):
    Q_g    = _f(inp, "Q_gas",  0.5)        # m³/s actual
    m_l    = _f(inp, "m_liq",  5.0)        # kg/s liquid
    rho_g  = _f(inp, "rho_g",  3.0)
    rho_l  = _f(inp, "rho_l",  750.0)
    K      = _f(inp, "K",      0.107)      # m/s (with mist eliminator)
    t_res  = _f(inp, "t_res",  300.0)      # liquid residence time, s

    if rho_l <= rho_g:
        raise ValueError("Liquid density must exceed gas density.")
    v_t = K * math.sqrt((rho_l - rho_g) / rho_g)
    A   = Q_g / v_t
    D   = math.sqrt(4.0 * A / math.pi)
    # Liquid hold-up volume
    V_l = (m_l / rho_l) * t_res            # m³
    A_l = math.pi * D * D / 4.0
    H_l = V_l / A_l if A_l > 0 else 0.0
    # Vapor disengaging height: max(0.6·D, 0.9 m)
    H_v = max(0.6 * D, 0.9)
    H_total = H_l + H_v + 0.6              # 0.6 m allowance for inlet/mist pad
    LD = H_total / D if D > 0 else 0.0

    results = [
        _r(_round(v_t, 3), "m/s", "Terminal (vapour) velocity"),
        _r(_round(A,  3),  "m²",  "Vessel cross-section A"),
        _r(_round(D,  3),  "m",   "Vessel diameter D"),
        _r(_round(V_l,3),  "m³",  f"Liquid volume @ {t_res:.0f} s"),
        _r(_round(H_l,3),  "m",   "Liquid holdup height Hl"),
        _r(_round(H_v,3),  "m",   "Vapour disengaging height Hv"),
        _r(_round(H_total,3),"m", "Total tangent height"),
        _r(_round(LD, 2),  "-",   "L/D ratio"),
    ]
    datasheet = [
        _ds("Separator Datasheet", [
            ["Tag",                  inp.get("tag", "V-101")],
            ["Service",              "Vertical 2-phase KO drum"],
            ["Gas volumetric flow",  f"{Q_g} m³/s"],
            ["Liquid mass flow",     f"{m_l} kg/s"],
            ["Gas density",          f"{rho_g} kg/m³"],
            ["Liquid density",       f"{rho_l} kg/m³"],
            ["Souders K",            f"{K} m/s"],
            ["Residence time",       f"{t_res} s"],
            ["Diameter D",           f"{D:.2f} m"],
            ["Total height",         f"{H_total:.2f} m"],
            ["L/D",                  f"{LD:.2f}"],
        ]),
    ]
    return {
        "results": results,
        "datasheet": datasheet,
        "diagram":   SEPARATOR_SVG,
        "notes": [
            "Souders–Brown vertical: v_t = K·√((ρ_L − ρ_V)/ρ_V), K ≈ 0.107 m/s with mist pad.",
            "D = √(4·Qg/(π·v_t)), then Hl = (m_L/ρ_L)·t_res / A.",
            "Recommended L/D between 3 and 5 for typical KO drums.",
        ],
    }
