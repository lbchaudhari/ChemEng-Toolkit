"""Combustion calculations (Sikdar Ch. 5).

Air composition assumed: 21% O₂ / 79% N₂ by mole.
Ultimate fuel analysis given as mass fractions (or %): C, H, S, N, O, Ash, H2O.
"""
from __future__ import annotations


def _r(value, unit, label):
    return {"label": label, "value": value, "unit": unit}


# Atomic / molecular weights (g/mol)
MW = {"C": 12.011, "H": 1.008, "O": 15.999, "N": 14.007, "S": 32.06,
      "H2": 2.016, "O2": 31.998, "N2": 28.014, "H2O": 18.015,
      "CO2": 44.009, "SO2": 64.06}


def theoretical_air(inp):
    """Stoichiometric air requirement and flue-gas composition for a fuel
    given by ultimate (mass) analysis. Optionally apply a % excess air."""
    # Mass fractions (%): C, H, S, N, O, ash, moisture
    C   = float(inp.get("C", 0))   / 100.0
    H   = float(inp.get("H", 0))   / 100.0
    S   = float(inp.get("S", 0))   / 100.0
    N   = float(inp.get("N", 0))   / 100.0
    O   = float(inp.get("O", 0))   / 100.0
    ash = float(inp.get("ash", 0)) / 100.0
    H2O = float(inp.get("H2O", 0)) / 100.0
    excess_pct = float(inp.get("excess", 20))

    total = C + H + S + N + O + ash + H2O
    if abs(total - 1.0) > 0.02:
        # tolerate small rounding; otherwise warn via note
        norm_warning = (
            f"Component sum = {total*100:.2f}%, normalising to 100% for the calculation."
        )
        if total <= 0:
            raise ValueError("All components are zero.")
        C, H, S, N, O, ash, H2O = (x / total for x in (C, H, S, N, O, ash, H2O))
    else:
        norm_warning = None

    # Per kg fuel: moles of each element
    n_C = C / MW["C"]            # kmol per kg fuel
    n_H = H / MW["H"]
    n_S = S / MW["S"]
    n_O_fuel = O / MW["O"]

    # O2 required (kmol/kg fuel):
    # C + O2 → CO2,    H + 1/4 O2 → 1/2 H2O,   S + O2 → SO2
    O2_req = n_C + n_H / 4.0 + n_S - n_O_fuel / 2.0
    if O2_req < 0:
        raise ValueError("Negative theoretical O₂ — fuel is over-oxygenated.")

    air_req_mol = O2_req / 0.21                   # kmol air/kg fuel
    air_req_mass = air_req_mol * 28.84            # kg air/kg fuel (MW_air≈28.84)

    excess_frac = excess_pct / 100.0
    O2_supplied = O2_req * (1 + excess_frac)
    air_supplied_mol  = O2_supplied / 0.21
    air_supplied_mass = air_supplied_mol * 28.84

    # Flue gas (per kg fuel):
    n_CO2 = n_C
    n_H2O = n_H / 2.0 + H2O / MW["H2O"]
    n_SO2 = n_S
    n_O2_excess = O2_supplied - O2_req
    n_N2 = air_supplied_mol * 0.79 + N / MW["N"] / 2.0  # N from fuel as N2

    n_dry  = n_CO2 + n_SO2 + n_O2_excess + n_N2
    n_wet  = n_dry + n_H2O

    def pct(x, t):
        return round(x / t * 100, 4) if t > 0 else 0

    return {
        "results": [
            _r(round(O2_req, 6), "kmol/kg fuel", "Theoretical O₂"),
            _r(round(air_req_mol, 6), "kmol/kg fuel", "Theoretical air"),
            _r(round(air_req_mass, 4), "kg/kg fuel", "Theoretical air (mass)"),
            _r(round(excess_pct, 3), "%", "Excess air specified"),
            _r(round(air_supplied_mol, 6), "kmol/kg fuel", "Actual air supplied"),
            _r(round(air_supplied_mass, 4), "kg/kg fuel", "Actual air (mass)"),
            _r(pct(n_CO2, n_dry), "%", "Orsat (dry) CO₂"),
            _r(pct(n_SO2, n_dry), "%", "Orsat (dry) SO₂"),
            _r(pct(n_O2_excess, n_dry), "%", "Orsat (dry) O₂"),
            _r(pct(n_N2, n_dry), "%", "Orsat (dry) N₂"),
            _r(pct(n_H2O, n_wet), "%", "Wet basis H₂O"),
            _r(round(n_dry, 6), "kmol/kg fuel", "Dry flue-gas total"),
            _r(round(n_wet, 6), "kmol/kg fuel", "Wet flue-gas total"),
        ],
        "notes": [
            "Reactions: C+O₂→CO₂, H₂+½O₂→H₂O, S+O₂→SO₂",
            "Theoretical O₂ = nC + nH/4 + nS − nO_fuel/2 (per kg fuel).",
            "Air ≈ 21 mol% O₂ / 79 mol% N₂; MW_air ≈ 28.84.",
            "Actual air = theoretical × (1 + %excess/100).",
            *( [norm_warning] if norm_warning else [] ),
        ],
    }


def hhv_dulong(inp):
    """Higher heating value of a solid/liquid fuel from ultimate analysis.

    Dulong's formula (kJ/kg):
        HHV = 33820·C + 144212·(H − O/8) + 9304·S
    where C, H, O, S are mass fractions.
    """
    C = float(inp.get("C", 0)) / 100.0
    H = float(inp.get("H", 0)) / 100.0
    O = float(inp.get("O", 0)) / 100.0
    S = float(inp.get("S", 0)) / 100.0
    H2O = float(inp.get("H2O", 0)) / 100.0
    HHV = 33820 * C + 144212 * (H - O / 8.0) + 9304 * S          # kJ/kg
    # Latent heat of water at 25 °C ≈ 2442 kJ/kg
    water_from_H = 9.0 * H        # kg water / kg fuel
    LHV = HHV - 2442.0 * (water_from_H + H2O)
    return {
        "results": [
            _r(round(HHV, 2), "kJ/kg",     "HHV (Dulong)"),
            _r(round(HHV / 1000.0, 4), "MJ/kg", "HHV (Dulong)"),
            _r(round(LHV, 2), "kJ/kg",     "LHV (net heating value)"),
            _r(round(LHV / 1000.0, 4), "MJ/kg", "LHV"),
        ],
        "notes": [
            "Dulong: HHV = 33820·C + 144212·(H − O/8) + 9304·S  (kJ/kg)",
            "LHV = HHV − λ_water · (9·H + moisture);  λ_water ≈ 2442 kJ/kg @ 25°C.",
            "C, H, O, S, moisture entered as wt %.",
        ],
    }
