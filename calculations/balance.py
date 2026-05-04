"""Mass and energy balance calculations."""
from __future__ import annotations


def _r(value, unit, label):
    return {"label": label, "value": value, "unit": unit}


# ---------- Mass Balance --------------------------------------------------

def binary_distillation_balance(inp):
    """Overall mass balance on a binary distillation column.
    F = D + B   and   F·xF = D·xD + B·xB
    Given F, xF, xD, xB → solve D and B."""
    F  = float(inp["F"])
    xF = float(inp["xF"])
    xD = float(inp["xD"])
    xB = float(inp["xB"])
    if not (0 < xB < xF < xD < 1):
        raise ValueError("Compositions must satisfy 0 < xB < xF < xD < 1.")
    if F <= 0:
        raise ValueError("Feed flow F must be > 0.")
    D = F * (xF - xB) / (xD - xB)
    B = F - D
    rec_light = D * xD / (F * xF)
    rec_heavy = B * (1 - xB) / (F * (1 - xF))
    return {
        "results": [
            _r(round(D, 4), "kg/h or mol/h", "Distillate flow D"),
            _r(round(B, 4), "kg/h or mol/h", "Bottoms flow B"),
            _r(round(D / F, 4), "-", "D/F ratio"),
            _r(round(B / F, 4), "-", "B/F ratio"),
            _r(round(rec_light * 100, 3), "%", "Light-key recovery in distillate"),
            _r(round(rec_heavy * 100, 3), "%", "Heavy-key recovery in bottoms"),
        ],
        "notes": [
            "Overall: F = D + B",
            "Component: F·xF = D·xD + B·xB",
            "→ D = F·(xF − xB) / (xD − xB),  B = F − D",
        ],
    }


def stream_mixer(inp):
    """Adiabatic mixing of N streams. 'streams' is a multiline / comma list of
    'flow, composition' pairs (mass or molar — be consistent).
    Output: total flow and overall composition."""
    raw = inp["streams"]
    pairs = []
    for line in raw.replace(";", "\n").splitlines():
        line = line.strip().strip(",")
        if not line:
            continue
        parts = [p.strip() for p in line.split(",") if p.strip()]
        if len(parts) < 2:
            raise ValueError(f"Stream needs 'flow, x'. Got: '{line}'")
        flow = float(parts[0])
        x    = float(parts[1])
        if flow < 0:
            raise ValueError("Stream flows must be ≥ 0.")
        if not 0 <= x <= 1:
            raise ValueError("Composition x must be in [0, 1].")
        pairs.append((flow, x))
    if not pairs:
        raise ValueError("Provide at least one stream.")
    total = sum(f for f, _ in pairs)
    if total == 0:
        raise ValueError("Total flow is 0.")
    x_out = sum(f * x for f, x in pairs) / total
    rows = [_r(round(total, 4), "flow units", "Total outlet flow"),
            _r(round(x_out, 6),  "-", "Outlet composition x_out")]
    for i, (f, x) in enumerate(pairs, 1):
        rows.append(_r(f"flow={f:g}, x={x:g}", "", f"Stream {i}"))
    return {
        "results": rows,
        "notes": [
            "Total = Σ Fi",
            "x_out = Σ(Fi·xi) / Σ Fi",
            "Assumes well-mixed, single-component basis.",
        ],
    }


def component_split(inp):
    """Single-equipment component split: feed F splits into top T and bottom B.
    Given F, xF, recovery of light key in top → compute T, B, xT, xB."""
    F      = float(inp["F"])
    xF     = float(inp["xF"])
    rec_LK = float(inp["rec_LK"]) / 100.0  # % → fraction
    rec_HK_bot = float(inp.get("rec_HK", 95)) / 100.0
    if not 0 < xF < 1:
        raise ValueError("xF must be in (0, 1).")
    if not 0 < rec_LK < 1 or not 0 < rec_HK_bot < 1:
        raise ValueError("Recoveries must be in (0, 100) %.")
    LK_in = F * xF
    HK_in = F * (1 - xF)
    LK_top = LK_in * rec_LK
    HK_top = HK_in * (1 - rec_HK_bot)
    LK_bot = LK_in - LK_top
    HK_bot = HK_in - HK_top
    T = LK_top + HK_top
    B = LK_bot + HK_bot
    xT = LK_top / T if T > 0 else 0
    xB = LK_bot / B if B > 0 else 0
    return {
        "results": [
            _r(round(T, 4), "flow", "Top product T"),
            _r(round(B, 4), "flow", "Bottom product B"),
            _r(round(xT, 4), "-", "Top composition xT"),
            _r(round(xB, 4), "-", "Bottom composition xB"),
            _r(round(LK_top, 4), "flow", "Light key in top"),
            _r(round(HK_bot, 4), "flow", "Heavy key in bottom"),
        ],
        "notes": [
            "Component balance per key with specified recoveries.",
            "T = LK_top + HK_top,   B = F − T",
        ],
    }


# ---------- Energy Balance ------------------------------------------------

def sensible_heat(inp):
    """Q = m·Cp·ΔT for a single-phase stream."""
    m  = float(inp["m"])      # kg/s
    Cp = float(inp["Cp"])     # J/kg·K
    T1 = float(inp["T1"])
    T2 = float(inp["T2"])
    Q = m * Cp * (T2 - T1)
    return {
        "results": [
            _r(round(Q, 3), "W", "Heat duty Q"),
            _r(round(Q / 1000.0, 4), "kW", "Heat duty Q"),
            _r(round(Q * 3.412, 3), "BTU/h", "Heat duty Q"),
            _r(round(T2 - T1, 3), "°C/K", "ΔT"),
        ],
        "notes": [
            "Q = m·Cp·(T₂ − T₁)",
            "Positive Q → heat added; negative → removed.",
        ],
    }


def latent_heat(inp):
    """Q = m·λ for vaporization or condensation."""
    m = float(inp["m"])         # kg/s
    lam = float(inp["lam"])     # J/kg
    Q = m * lam
    return {
        "results": [
            _r(round(Q, 3), "W", "Heat duty Q"),
            _r(round(Q / 1000.0, 4), "kW", "Heat duty Q"),
            _r(round(Q / 1e6, 5), "MW", "Heat duty Q"),
        ],
        "notes": [
            "Q = m·λ",
            "Use λ_vap for boiling, λ_fus for melting.",
        ],
    }


def adiabatic_mix_temperature(inp):
    """Two-stream adiabatic mixer: outlet T from energy balance.
    m1·Cp1·T1 + m2·Cp2·T2 = (m1·Cp1 + m2·Cp2)·T_out."""
    m1  = float(inp["m1"])
    Cp1 = float(inp["Cp1"])
    T1  = float(inp["T1"])
    m2  = float(inp["m2"])
    Cp2 = float(inp["Cp2"])
    T2  = float(inp["T2"])
    if m1 < 0 or m2 < 0:
        raise ValueError("Mass flows must be ≥ 0.")
    if Cp1 <= 0 or Cp2 <= 0:
        raise ValueError("Cp must be > 0.")
    num = m1 * Cp1 * T1 + m2 * Cp2 * T2
    den = m1 * Cp1 + m2 * Cp2
    if den == 0:
        raise ValueError("Both mass flows are zero.")
    T_out = num / den
    return {
        "results": [
            _r(round(T_out, 3), "°C or K", "Outlet temperature T_out"),
            _r(round(m1 + m2, 4), "kg/s", "Total outlet flow"),
            _r(round(m1 * Cp1, 3), "W/K", "Heat capacity rate stream 1"),
            _r(round(m2 * Cp2, 3), "W/K", "Heat capacity rate stream 2"),
        ],
        "notes": [
            "Adiabatic, no phase change, constant Cp:",
            "T_out = (m₁·Cp₁·T₁ + m₂·Cp₂·T₂) / (m₁·Cp₁ + m₂·Cp₂)",
        ],
    }


def overall_energy_balance(inp):
    """Steady-state overall energy balance: Q − W = ΔH (open system).
    Given any 3 of the 4 (Q, W, H_in, H_out) leave one as 0 to solve."""
    Q = float(inp.get("Q") or 0)
    W = float(inp.get("W") or 0)
    H_in  = float(inp.get("H_in") or 0)
    H_out = float(inp.get("H_out") or 0)
    # Q - W = H_out - H_in   →   H_out = H_in + Q - W
    # Determine missing field by which one user left at 0 *and* marked missing.
    missing = (inp.get("solve_for") or "H_out").strip()
    if missing == "Q":
        Q = (H_out - H_in) + W
    elif missing == "W":
        W = Q - (H_out - H_in)
    elif missing == "H_in":
        H_in = H_out - Q + W
    else:
        H_out = H_in + Q - W
    return {
        "results": [
            _r(round(Q, 4), "W", "Heat into system Q"),
            _r(round(W, 4), "W", "Shaft work out W"),
            _r(round(H_in, 4), "W", "Inlet enthalpy flow H_in"),
            _r(round(H_out, 4), "W", "Outlet enthalpy flow H_out"),
            _r(round(H_out - H_in, 4), "W", "ΔH = H_out − H_in"),
            _r(missing, "", "Variable solved for"),
        ],
        "notes": [
            "Steady-state open system: Q − W = ΔH",
            "Sign convention: Q > 0 added to system, W > 0 done by system.",
        ],
    }


def cp_polynomial_enthalpy(inp):
    """Sensible enthalpy from a temperature-dependent heat capacity:
        Cp(T) = a + b·T + c·T² + d·T³     [J/mol·K, T in K]
    ΔH = ∫_{T1}^{T2} Cp dT  per mole, then × n if moles given.
    """
    a = float(inp.get("a", 0))
    b = float(inp.get("b", 0))
    c = float(inp.get("c", 0))
    d = float(inp.get("d", 0))
    T1 = float(inp["T1"])
    T2 = float(inp["T2"])
    n  = float(inp.get("n", 1.0))   # moles
    if T1 == T2:
        raise ValueError("T1 and T2 must differ.")
    # ∫(a + bT + cT² + dT³) dT = aT + bT²/2 + cT³/3 + dT⁴/4
    def F(T):
        return a * T + b * T ** 2 / 2 + c * T ** 3 / 3 + d * T ** 4 / 4
    H_per_mol = F(T2) - F(T1)
    H_total   = n * H_per_mol
    Cp_avg    = H_per_mol / (T2 - T1)
    return {
        "results": [
            _r(round(H_per_mol, 4), "J/mol", "ΔH per mole"),
            _r(round(H_per_mol / 1000, 6), "kJ/mol", "ΔH per mole"),
            _r(round(H_total, 4), "J", "Total ΔH (n × ΔH/mol)"),
            _r(round(H_total / 1000, 6), "kJ", "Total ΔH"),
            _r(round(Cp_avg, 4), "J/mol·K", "Average Cp over [T1, T2]"),
        ],
        "notes": [
            "Cp(T) = a + b·T + c·T² + d·T³  (T in K)",
            "ΔH/mol = a(T₂−T₁) + b(T₂²−T₁²)/2 + c(T₂³−T₁³)/3 + d(T₂⁴−T₁⁴)/4",
        ],
    }


def heat_of_reaction_hess(inp):
    """Heat of reaction from heats of formation (Hess's law).

    Inputs:
      reactants - lines of 'name, ΔHf°(kJ/mol), ν' (stoichiometric coeff > 0)
      products  - same format
    """
    def parse(text, label):
        rows = []
        for line in (text or "").replace(";", "\n").splitlines():
            line = line.strip().strip(",")
            if not line:
                continue
            parts = [p.strip() for p in line.split(",") if p.strip()]
            if len(parts) < 3:
                raise ValueError(f"{label}: each line must be 'name, Hf, nu'. Got: '{line}'")
            rows.append((parts[0], float(parts[1]), float(parts[2])))
        return rows

    R = parse(inp["reactants"], "Reactants")
    P = parse(inp["products"],  "Products")
    if not R or not P:
        raise ValueError("Provide both reactants and products.")
    sumR = sum(nu * Hf for _, Hf, nu in R)
    sumP = sum(nu * Hf for _, Hf, nu in P)
    dHr = sumP - sumR     # kJ (per extent of reaction = 1 mol of "rxn")
    rows = [
        _r(round(dHr, 4), "kJ", "ΔH_rxn (per mol of reaction extent)"),
        _r("exothermic" if dHr < 0 else "endothermic", "", "Reaction type"),
        _r(round(sumP, 4), "kJ", "Σ ν·ΔHf° (products)"),
        _r(round(sumR, 4), "kJ", "Σ ν·ΔHf° (reactants)"),
    ]
    for n, Hf, nu in R + P:
        rows.append(_r(f"ν={nu:g}, ΔHf°={Hf:g} kJ/mol", "", n))
    return {
        "results": rows,
        "notes": [
            "Hess's law: ΔH_rxn = Σ ν·ΔHf°(products) − Σ ν·ΔHf°(reactants)",
            "Use the same reference state for all heats of formation.",
        ],
    }


def adiabatic_flame_temp(inp):
    """Approximate adiabatic flame temperature for fully combusted fuel.

    Simple lumped model:
        T_ad = T_ref + (LHV − Q_loss) / (n_fg · Cp_fg)
    where Cp_fg is the average flue-gas Cp (J/mol·K) and n_fg the moles of
    flue gas per mole of fuel (or per kg fuel if LHV is per kg).
    """
    LHV    = float(inp["LHV"])         # J / (kg or mol fuel)
    n_fg   = float(inp["n_fg"])        # moles flue gas / (kg or mol fuel)
    Cp_fg  = float(inp.get("Cp_fg", 33))  # J/mol·K
    T_ref  = float(inp.get("T_ref", 25))  # °C
    Q_loss = float(inp.get("Q_loss", 0))  # J / (kg or mol fuel)
    if n_fg <= 0 or Cp_fg <= 0:
        raise ValueError("n_fg and Cp_fg must be > 0.")
    dT = (LHV - Q_loss) / (n_fg * Cp_fg)
    T_ad = T_ref + dT
    return {
        "results": [
            _r(round(T_ad, 2), "°C", "Adiabatic flame temperature"),
            _r(round(T_ad + 273.15, 2), "K", "Adiabatic flame temperature"),
            _r(round(dT, 2), "°C/K", "Temperature rise"),
            _r(round(LHV / 1000.0, 4), "kJ", "LHV of fuel (per basis)"),
        ],
        "notes": [
            "T_ad = T_ref + (LHV − Q_losses) / (n_fg · Cp̄_fg)",
            "Use consistent units: LHV per kg fuel ↔ n_fg per kg fuel.",
            "Cp_fg ≈ 32–37 J/mol·K for typical flue gas at 1500–2000 °C.",
        ],
    }


def recycle_balance(inp):
    """Material balance with recycle and purge for a single component.

    Steady-state mixer + reactor (or process) with one recycle stream:
        Fresh feed F + Recycle R → Process → Product P + Recycle R + Purge G
    Specify what is known; we solve overall and recycle ratios.
    """
    F  = float(inp["F"])
    P  = float(inp["P"])
    G  = float(inp["G"])
    if F <= 0:
        raise ValueError("Fresh feed F must be > 0.")
    overall = F - P - G            # accumulation should be 0 → check
    R = F * float(inp.get("R_over_F", 1.0))
    return {
        "results": [
            _r(round(F, 4), "flow", "Fresh feed F"),
            _r(round(P, 4), "flow", "Product P"),
            _r(round(G, 4), "flow", "Purge G"),
            _r(round(R, 4), "flow", "Recycle R"),
            _r(round(R / F, 4), "-",   "Recycle ratio R/F"),
            _r(round(G / F * 100, 4), "%", "Purge fraction G/F"),
            _r(round(overall, 6), "flow", "Overall balance residual (≈0 expected)"),
        ],
        "notes": [
            "Overall steady-state balance: F = P + G  (one inlet, two outlets).",
            "Purge prevents inert build-up; G is set by inert balance:",
            "G·x_inert,G = F·x_inert,F  for trace inerts in fresh feed.",
        ],
    }
