"""Stoichiometry & basic chemical calculations (Sikdar Ch. 2 & 4)."""
from __future__ import annotations


def _r(value, unit, label):
    return {"label": label, "value": value, "unit": unit}


# ---------- Composition conversions ---------------------------------------

def _parse_components(text):
    """Parse 'name, MW, value' triples (one per line)."""
    rows = []
    for line in text.replace(";", "\n").splitlines():
        line = line.strip().strip(",")
        if not line:
            continue
        parts = [p.strip() for p in line.split(",") if p.strip()]
        if len(parts) < 3:
            raise ValueError(f"Each line must be 'name, MW, value'. Got: '{line}'")
        name = parts[0]
        mw   = float(parts[1])
        val  = float(parts[2])
        if mw <= 0:
            raise ValueError(f"MW must be > 0 (got {mw} for {name}).")
        if val < 0:
            raise ValueError(f"Composition must be ≥ 0 (got {val} for {name}).")
        rows.append((name, mw, val))
    if not rows:
        raise ValueError("Provide at least one component.")
    return rows


def wt_to_mol_percent(inp):
    """Convert weight % (or mass fractions) into mole %."""
    rows = _parse_components(inp["components"])
    total_w = sum(v for _, _, v in rows)
    if total_w == 0:
        raise ValueError("Sum of weight fractions is 0.")
    moles = [(n, v / total_w / mw) for n, mw, v in rows]
    total_n = sum(m for _, m in moles)
    out = []
    for (n, mw, v), (_, m) in zip(rows, moles):
        wf = v / total_w
        xf = m / total_n
        out.append(_r(f"wt={wf*100:.4f}%, mol={xf*100:.4f}%", "", n))
    avg_mw = sum(mw * (m / total_n) for (_, mw, _), (_, m) in zip(rows, moles))
    out.append(_r(round(avg_mw, 4), "g/mol", "Average molecular weight"))
    return {
        "results": out,
        "notes": [
            "Basis: 100 g of mixture.",
            "n_i = w_i / MW_i,  x_i = n_i / Σ n_i",
            "MW_avg = Σ x_i · MW_i",
        ],
    }


def mol_to_wt_percent(inp):
    """Convert mole % (or mole fractions) into weight %."""
    rows = _parse_components(inp["components"])
    total_n = sum(v for _, _, v in rows)
    if total_n == 0:
        raise ValueError("Sum of mole fractions is 0.")
    masses = [(n, v / total_n * mw) for n, mw, v in rows]
    total_m = sum(m for _, m in masses)
    out = []
    for (n, mw, v), (_, m) in zip(rows, masses):
        xf = v / total_n
        wf = m / total_m
        out.append(_r(f"mol={xf*100:.4f}%, wt={wf*100:.4f}%", "", n))
    avg_mw = sum((v / total_n) * mw for n, mw, v in rows)
    out.append(_r(round(avg_mw, 4), "g/mol", "Average molecular weight"))
    return {
        "results": out,
        "notes": [
            "Basis: 100 mol of mixture.",
            "m_i = x_i · MW_i,  w_i = m_i / Σ m_i",
            "MW_avg = Σ x_i · MW_i",
        ],
    }


# ---------- Reaction stoichiometry ----------------------------------------

def limiting_reactant(inp):
    """Identify limiting reactant for a generic reaction:
        a A + b B → products (single rxn).
    Inputs:
      nu_A, nu_B  - stoichiometric coefficients
      n_A, n_B    - moles available
      conv_A      - fractional conversion of A (0–1) [optional]
    """
    nu_A = float(inp["nu_A"])
    nu_B = float(inp["nu_B"])
    n_A  = float(inp["n_A"])
    n_B  = float(inp["n_B"])
    conv = float(inp.get("conv_A", 1.0))
    if min(nu_A, nu_B) <= 0 or min(n_A, n_B) < 0:
        raise ValueError("Coefficients must be > 0 and moles ≥ 0.")
    if not 0 < conv <= 1:
        raise ValueError("Conversion must be in (0, 1].")

    # required moles of B to consume all of A:
    n_B_needed = (nu_B / nu_A) * n_A
    if n_B >= n_B_needed:
        limiting = "A"
        excess   = "B"
        n_excess = n_B - n_B_needed
        pct_excess = n_excess / n_B_needed * 100 if n_B_needed > 0 else 0
        n_limit = n_A
    else:
        limiting = "B"
        excess   = "A"
        n_A_needed = (nu_A / nu_B) * n_B
        n_excess = n_A - n_A_needed
        pct_excess = n_excess / n_A_needed * 100 if n_A_needed > 0 else 0
        n_limit = n_B

    # Extent of reaction at given conversion of A
    n_A_react = conv * n_A if limiting == "A" else (nu_A / nu_B) * (conv * n_B)
    n_B_react = (nu_B / nu_A) * n_A_react

    return {
        "results": [
            _r(limiting, "", "Limiting reactant"),
            _r(excess, "", "Excess reactant"),
            _r(round(n_excess, 6), "mol", f"Excess of {excess}"),
            _r(round(pct_excess, 4), "%", f"% Excess of {excess}"),
            _r(round(n_A_react, 6), "mol", "Moles of A reacted"),
            _r(round(n_B_react, 6), "mol", "Moles of B reacted"),
        ],
        "notes": [
            "Limiting reactant runs out first; calculated by comparing supplied moles to stoichiometric demand.",
            "% Excess = (supplied − required) / required × 100",
            "Required of B per mole A = ν_B / ν_A.",
        ],
    }


def yield_selectivity(inp):
    """Yield, conversion and selectivity for a parallel/series reaction.
    Inputs are amounts (moles) at end of reaction:
      n_A0      - initial limiting reactant
      n_A       - unreacted limiting reactant
      n_P       - moles of desired product
      n_S       - moles of side/by product
      nu_A_P, nu_P  - stoichiometric coeffs in main rxn (a·A → p·P)
      nu_A_S, nu_S  - stoichiometric coeffs in side rxn  (a·A → s·S)
    """
    n_A0   = float(inp["n_A0"])
    n_A    = float(inp["n_A"])
    n_P    = float(inp["n_P"])
    n_S    = float(inp.get("n_S", 0))
    nu_A_P = float(inp.get("nu_A_P", 1))
    nu_P   = float(inp.get("nu_P", 1))
    nu_A_S = float(inp.get("nu_A_S", 1))
    nu_S   = float(inp.get("nu_S", 1))

    if n_A0 <= 0 or n_A < 0 or n_A > n_A0:
        raise ValueError("Need 0 ≤ n_A ≤ n_A0 with n_A0 > 0.")

    conv = (n_A0 - n_A) / n_A0
    n_A_consumed_in_P = (nu_A_P / nu_P) * n_P
    n_A_consumed_in_S = (nu_A_S / nu_S) * n_S
    total_consumed = n_A_consumed_in_P + n_A_consumed_in_S

    n_P_max = (nu_P / nu_A_P) * n_A0
    yield_pct = n_P / n_P_max * 100 if n_P_max > 0 else 0
    selectivity = (n_P / n_S) if n_S > 0 else float("inf")

    return {
        "results": [
            _r(round(conv * 100, 4), "%", "Conversion of A"),
            _r(round(yield_pct, 4), "%", "Yield of desired product P"),
            _r(round(selectivity, 4) if selectivity != float("inf") else "∞",
               "mol P / mol S", "Selectivity (P/S)"),
            _r(round(n_A_consumed_in_P, 6), "mol", "A consumed → P"),
            _r(round(n_A_consumed_in_S, 6), "mol", "A consumed → S"),
            _r(round(total_consumed, 6), "mol", "Total A consumed (mass-balance check)"),
        ],
        "notes": [
            "Conversion = (n_A0 − n_A) / n_A0",
            "Yield = n_P actual / n_P_max(theoretical from n_A0)",
            "Selectivity = n_P / n_S  (ratio of desired to undesired product)",
            "Mass-balance check: 'Total A consumed' should equal n_A0 − n_A.",
        ],
    }
