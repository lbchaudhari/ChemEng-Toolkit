"""Calculator registry: metadata + dispatch table.

Each entry has:
  id          - URL slug
  title       - human label
  category    - groups in sidebar
  description - shown above the form
  inputs      - list of {name, label, unit, default, type?, options?}
  compute     - callable taking dict of inputs, returning {results, notes}
"""
from __future__ import annotations
from calculations import (fluids, heat, mass, thermo, reaction, units,
                          economics, balance, stoichiometry, combustion,
                          equipment, piping)

# Helper to keep entries compact.
def _i(name, label, unit="", default="", typ="number", options=None):
    d = {"name": name, "label": label, "unit": unit, "default": default, "type": typ}
    if options:
        d["options"] = options
    return d


CALCULATORS = {
    # ---------- Fluid Mechanics ------------------------------------------
    "reynolds": {
        "title": "Reynolds Number",
        "category": "Fluid Mechanics",
        "description": "Compute Re = ρ·v·D/μ and classify flow regime.",
        "inputs": [
            _i("rho", "Fluid density ρ", "kg/m³", 1000),
            _i("v",   "Velocity v",      "m/s",  2.0),
            _i("d",   "Pipe diameter D", "m",    0.05),
            _i("mu",  "Dynamic viscosity μ", "Pa·s", 0.001),
        ],
        "compute": fluids.reynolds,
    },
    "darcy_dp": {
        "title": "Pipe Pressure Drop (Darcy-Weisbach)",
        "category": "Fluid Mechanics",
        "description": "ΔP across a straight pipe using Darcy-Weisbach with Swamee–Jain friction factor.",
        "inputs": [
            _i("rho", "Fluid density ρ", "kg/m³", 1000),
            _i("v",   "Velocity v",      "m/s",  2.0),
            _i("d",   "Pipe diameter D", "m",    0.05),
            _i("mu",  "Dynamic viscosity μ", "Pa·s", 0.001),
            _i("L",   "Pipe length L",   "m",    50),
            _i("eps", "Roughness ε",     "m",    0.000045),
        ],
        "compute": fluids.darcy_pressure_drop,
    },
    "pump_power": {
        "title": "Pump Power",
        "category": "Fluid Mechanics",
        "description": "Hydraulic and shaft power for a centrifugal pump.",
        "inputs": [
            _i("rho", "Fluid density ρ", "kg/m³", 1000),
            _i("Q",   "Volumetric flow Q", "m³/s", 0.01),
            _i("H",   "Total head H",      "m",    25),
            _i("eta", "Pump efficiency η", "-",   0.7),
        ],
        "compute": fluids.pump_power,
    },
    "npsh": {
        "title": "NPSH Available",
        "category": "Fluid Mechanics",
        "description": "NPSH available at a centrifugal-pump suction (compare to NPSH required).",
        "inputs": [
            _i("P_s",        "Suction pressure P_s (abs)", "Pa",    101325),
            _i("P_v",        "Liquid vapour pressure P_v", "Pa",    3170),
            _i("rho",        "Liquid density ρ",          "kg/m³", 1000),
            _i("h_static",   "Static head (+ above pump)", "m",     2.0),
            _i("h_friction", "Suction friction losses",   "m",     0.5),
        ],
        "compute": fluids.npsh_available,
    },
    "orifice": {
        "title": "Orifice Meter Flow",
        "category": "Fluid Mechanics",
        "description": "Mass / volumetric flow through an orifice meter from ΔP.",
        "inputs": [
            _i("rho", "Fluid density ρ",     "kg/m³", 1000),
            _i("dP",  "Differential ΔP",     "Pa",    5000),
            _i("D",   "Pipe inside diameter D", "m",  0.1),
            _i("d",   "Orifice diameter d",  "m",     0.05),
            _i("Cd",  "Discharge coefficient Cd", "-", 0.61),
        ],
        "compute": fluids.orifice_flow,
    },
    "compressor": {
        "title": "Adiabatic Compressor Power",
        "category": "Fluid Mechanics",
        "description": "Single-stage adiabatic ideal-gas compression power and discharge T.",
        "inputs": [
            _i("n_dot", "Molar flow ṅ",       "mol/s", 10),
            _i("T1",    "Inlet temperature T1", "K",    300),
            _i("P1",    "Inlet pressure P1",    "Pa",   101325),
            _i("P2",    "Outlet pressure P2",   "Pa",   500000),
            _i("gamma", "Heat-capacity ratio γ", "-",   1.4),
            _i("eta",   "Isentropic efficiency η", "-", 0.75),
        ],
        "compute": fluids.compressor_power,
    },

    # ---------- Heat Transfer --------------------------------------------
    "lmtd": {
        "title": "LMTD",
        "category": "Heat Transfer",
        "description": "Log-mean temperature difference for parallel or counter flow.",
        "inputs": [
            _i("Thi", "Hot inlet temp Th,i",  "°C", 150),
            _i("Tho", "Hot outlet temp Th,o", "°C", 90),
            _i("Tci", "Cold inlet temp Tc,i", "°C", 30),
            _i("Tco", "Cold outlet temp Tc,o","°C", 70),
            _i("flow", "Flow configuration", "", "counter", "select",
               ["counter", "parallel"]),
        ],
        "compute": heat.lmtd,
    },
    "hx_area": {
        "title": "Heat Exchanger Area",
        "category": "Heat Transfer",
        "description": "Required heat-transfer area from duty, U and LMTD.",
        "inputs": [
            _i("Q",   "Duty Q",        "W",       50000),
            _i("U",   "Overall U",     "W/m²·K",  500),
            _i("lmtd","LMTD",          "K",       40),
            _i("F",   "Correction factor F", "-", 1.0),
        ],
        "compute": heat.heat_exchanger_area,
    },
    "conduction": {
        "title": "Steady Conduction (Plane Wall)",
        "category": "Heat Transfer",
        "description": "1-D steady heat conduction through a plane wall.",
        "inputs": [
            _i("k",  "Thermal conductivity k", "W/m·K", 0.5),
            _i("A",  "Area A",                 "m²",    2.0),
            _i("T1", "Hot face T1",            "°C",    120),
            _i("T2", "Cold face T2",           "°C",    25),
            _i("L",  "Wall thickness L",       "m",     0.1),
        ],
        "compute": heat.conduction_wall,
    },

    # ---------- Mass Transfer / Distillation -----------------------------
    "fenske": {
        "title": "Fenske – Minimum Stages",
        "category": "Mass Transfer",
        "description": "Minimum equilibrium stages at total reflux for a binary distillation.",
        "inputs": [
            _i("xD",    "Distillate composition xD", "-", 0.95),
            _i("xB",    "Bottoms composition xB",    "-", 0.05),
            _i("alpha", "Relative volatility α",     "-", 2.5),
        ],
        "compute": mass.fenske_min_stages,
    },
    "underwood": {
        "title": "Underwood – Minimum Reflux",
        "category": "Mass Transfer",
        "description": "Minimum reflux ratio for a binary system (saturated-liquid feed by default).",
        "inputs": [
            _i("xF",    "Feed composition xF",   "-", 0.5),
            _i("xD",    "Distillate xD",         "-", 0.95),
            _i("alpha", "Relative volatility α", "-", 2.5),
            _i("q",     "Feed quality q",        "-", 1.0),
        ],
        "compute": mass.underwood_min_reflux,
    },
    "kremser": {
        "title": "Kremser – Absorber Stages",
        "category": "Mass Transfer",
        "description": "Theoretical stages for dilute counter-current gas absorption.",
        "inputs": [
            _i("A",    "Absorption factor A = L/(m·G)", "-", 1.5),
            _i("yin",  "Inlet gas mole fraction yin",   "-", 0.05),
            _i("yout", "Outlet gas mole fraction yout", "-", 0.005),
            _i("xin",  "Inlet liquid mole fraction xin","-", 0.0),
            _i("m",    "Equilibrium slope m",           "-", 1.0),
        ],
        "compute": mass.kremser_absorption,
    },
    "souders_brown": {
        "title": "Tray Column Diameter (Souders–Brown)",
        "category": "Mass Transfer",
        "description": "Column diameter from vapour and liquid densities using the Souders–Brown F-factor.",
        "inputs": [
            _i("rho_L", "Liquid density ρ_L", "kg/m³", 750),
            _i("rho_V", "Vapour density ρ_V", "kg/m³", 3.5),
            _i("m_V",   "Vapour mass flow ṁ_V", "kg/s", 5.0),
            _i("K",     "Souders–Brown K",     "m/s",   0.055),
            _i("eta",   "Design % of flooding", "-",    0.80),
        ],
        "compute": mass.souders_brown_diameter,
    },

    # ---------- Thermodynamics -------------------------------------------
    "ideal_gas": {
        "title": "Ideal Gas Law",
        "category": "Thermodynamics",
        "description": "PV = nRT — leave the unknown as 0 and fill the other three.",
        "inputs": [
            _i("P", "Pressure P",    "Pa",  101325),
            _i("V", "Volume V",      "m³",  0.024),
            _i("n", "Moles n",       "mol", 1.0),
            _i("T", "Temperature T", "K",   0),
        ],
        "compute": thermo.ideal_gas,
    },
    "antoine": {
        "title": "Antoine Vapor Pressure",
        "category": "Thermodynamics",
        "description": "log10(P_mmHg) = A − B/(T_°C + C).  (e.g. water: A=8.07131, B=1730.63, C=233.426)",
        "inputs": [
            _i("A", "Antoine A", "", 8.07131),
            _i("B", "Antoine B", "", 1730.63),
            _i("C", "Antoine C", "", 233.426),
            _i("T", "Temperature T", "°C", 100),
        ],
        "compute": thermo.antoine_vapor_pressure,
    },
    "rk_z": {
        "title": "Compressibility Z (Redlich–Kwong)",
        "category": "Thermodynamics",
        "description": "Compressibility factor and molar volume from the RK equation of state.",
        "inputs": [
            _i("Tc", "Critical temperature Tc", "K",  190.6),
            _i("Pc", "Critical pressure Pc",    "Pa", 4.604e6),
            _i("T",  "Temperature T",           "K",  300),
            _i("P",  "Pressure P",              "Pa", 5e6),
        ],
        "compute": thermo.compressibility_redlich_kwong,
    },
    "clausius": {
        "title": "Clausius–Clapeyron Equation",
        "category": "Thermodynamics",
        "description": "Two-point form. Leave the unknown variable as 0 and fill the other three.",
        "inputs": [
            _i("P1",     "Pressure P1",         "Pa",     3170),
            _i("P2",     "Pressure P2",         "Pa",     0),
            _i("T1",     "Temperature T1",      "K",      298.15),
            _i("T2",     "Temperature T2",      "K",      373.15),
            _i("dH_vap", "Heat of vaporisation", "J/mol", 40700),
        ],
        "compute": thermo.clausius_clapeyron,
    },
    "raoult_bubble": {
        "title": "Raoult's Law – Binary Bubble Point",
        "category": "Thermodynamics",
        "description": "Bubble pressure and vapour composition for an ideal binary mixture.",
        "inputs": [
            _i("x1",     "Liquid mole fraction x1",  "-", 0.5),
            _i("P1_sat", "Saturation pressure P1ˢ",  "Pa", 70000),
            _i("P2_sat", "Saturation pressure P2ˢ",  "Pa", 30000),
        ],
        "compute": thermo.raoult_binary_bubble,
    },
    "dalton": {
        "title": "Dalton's Law – Partial Pressures",
        "category": "Thermodynamics",
        "description": "Partial pressures in a gas mixture from total pressure and mole fractions.",
        "inputs": [
            _i("P", "Total pressure P", "Pa", 101325),
            _i("components", "Components (one per line: name, y)", "",
               "N2, 0.78\nO2, 0.21\nAr, 0.01", "textarea"),
        ],
        "compute": thermo.dalton_partial_pressures,
    },
    "humidity": {
        "title": "Humidity / Psychrometrics",
        "category": "Thermodynamics",
        "description": "Absolute, percentage and saturated humidity, dew point, humid heat & volume from T and RH.",
        "inputs": [
            _i("T",  "Dry-bulb temperature T", "°C", 30),
            _i("RH", "Relative humidity",      "%",  60),
            _i("P",  "Total pressure P",       "Pa", 101325),
        ],
        "compute": thermo.humidity_calc,
    },

    # ---------- Reaction Engineering -------------------------------------
    "cstr": {
        "title": "CSTR Volume (1st-order)",
        "category": "Reaction Engineering",
        "description": "Volume of a CSTR for a first-order liquid-phase reaction.",
        "inputs": [
            _i("CA0", "Inlet conc. C_A0", "mol/m³", 1000),
            _i("v0",  "Volumetric flow v₀", "m³/s", 0.001),
            _i("k",   "Rate constant k",  "1/s",   0.1),
            _i("X",   "Conversion X",     "-",     0.8),
        ],
        "compute": reaction.cstr_first_order,
    },
    "pfr": {
        "title": "PFR Volume (1st-order)",
        "category": "Reaction Engineering",
        "description": "Volume of a PFR for a first-order liquid-phase reaction.",
        "inputs": [
            _i("CA0", "Inlet conc. C_A0", "mol/m³", 1000),
            _i("v0",  "Volumetric flow v₀", "m³/s", 0.001),
            _i("k",   "Rate constant k",  "1/s",   0.1),
            _i("X",   "Conversion X",     "-",     0.8),
        ],
        "compute": reaction.pfr_first_order,
    },
    "batch": {
        "title": "Batch Time (1st-order)",
        "category": "Reaction Engineering",
        "description": "Time to reach a target concentration in a constant-volume batch reactor.",
        "inputs": [
            _i("C0", "Initial conc. C0",     "mol/m³", 1000),
            _i("C",  "Final conc. C",        "mol/m³", 200),
            _i("k",  "Rate constant k",      "1/s",    0.05),
        ],
        "compute": reaction.batch_first_order,
    },
    "arrhenius": {
        "title": "Arrhenius Rate Constant",
        "category": "Reaction Engineering",
        "description": "k(T) from pre-exponential factor and activation energy.",
        "inputs": [
            _i("A",  "Pre-exponential A",      "1/s",  1e10),
            _i("Ea", "Activation energy Ea",   "J/mol", 75000),
            _i("T",  "Temperature T",          "K",     350),
        ],
        "compute": reaction.arrhenius,
    },
    "limiting_reactant": {
        "title": "Limiting Reactant & % Excess",
        "category": "Reaction Engineering",
        "description": "For a·A + b·B → products: identify limiting reactant, % excess, and moles reacted.",
        "inputs": [
            _i("nu_A",   "Stoich. coeff. ν_A",       "-",   1),
            _i("nu_B",   "Stoich. coeff. ν_B",       "-",   2),
            _i("n_A",    "Moles of A supplied",       "mol", 100),
            _i("n_B",    "Moles of B supplied",       "mol", 250),
            _i("conv_A", "Conversion of limiting (0–1)", "-", 1.0),
        ],
        "compute": stoichiometry.limiting_reactant,
    },
    "yield_selectivity": {
        "title": "Yield, Conversion & Selectivity",
        "category": "Reaction Engineering",
        "description": "Compute conversion of A, yield of P and selectivity P/S for parallel reactions.",
        "inputs": [
            _i("n_A0",   "Initial moles of A (n_A0)", "mol", 100),
            _i("n_A",    "Final moles of A (n_A)",   "mol", 20),
            _i("n_P",    "Moles of desired product P", "mol", 60),
            _i("n_S",    "Moles of side product S",   "mol", 10),
            _i("nu_A_P", "ν_A in main rxn",          "-", 1),
            _i("nu_P",   "ν_P in main rxn",          "-", 1),
            _i("nu_A_S", "ν_A in side rxn",          "-", 1),
            _i("nu_S",   "ν_S in side rxn",          "-", 1),
        ],
        "compute": stoichiometry.yield_selectivity,
    },

    # ---------- Unit Conversions -----------------------------------------
    "conv_length": {
        "title": "Length Conversion",
        "category": "Unit Conversions",
        "description": "Convert between m, mm, cm, km, in, ft, yd, mile.",
        "inputs": [
            _i("value", "Value",   "",  1.0),
            _i("from",  "From",    "",  "m", "select", units.ALLOWED["length"]),
            _i("to",    "To",      "",  "ft", "select", units.ALLOWED["length"]),
        ],
        "compute": units.length,
    },
    "conv_mass": {
        "title": "Mass Conversion",
        "category": "Unit Conversions",
        "description": "Convert between kg, g, mg, tonne, lb, oz.",
        "inputs": [
            _i("value", "Value", "", 1.0),
            _i("from",  "From",  "", "kg", "select", units.ALLOWED["mass"]),
            _i("to",    "To",    "", "lb", "select", units.ALLOWED["mass"]),
        ],
        "compute": units.mass,
    },
    "conv_pressure": {
        "title": "Pressure Conversion",
        "category": "Unit Conversions",
        "description": "Convert between Pa, kPa, MPa, bar, atm, psi, mmHg, torr, inHg.",
        "inputs": [
            _i("value", "Value", "", 1.0),
            _i("from",  "From",  "", "bar", "select", units.ALLOWED["pressure"]),
            _i("to",    "To",    "", "psi", "select", units.ALLOWED["pressure"]),
        ],
        "compute": units.pressure,
    },
    "conv_temp": {
        "title": "Temperature Conversion",
        "category": "Unit Conversions",
        "description": "Convert between °C, °F, K, °R.",
        "inputs": [
            _i("value", "Value", "", 25.0),
            _i("from",  "From",  "", "C", "select", units.ALLOWED["temperature"]),
            _i("to",    "To",    "", "F", "select", units.ALLOWED["temperature"]),
        ],
        "compute": units.temperature,
    },
    "conv_energy": {
        "title": "Energy Conversion",
        "category": "Unit Conversions",
        "description": "Convert between J, kJ, MJ, cal, kcal, Wh, kWh, BTU, ft-lbf.",
        "inputs": [
            _i("value", "Value", "", 1.0),
            _i("from",  "From",  "", "kJ", "select", units.ALLOWED["energy"]),
            _i("to",    "To",    "", "BTU", "select", units.ALLOWED["energy"]),
        ],
        "compute": units.energy,
    },
    "conv_flow": {
        "title": "Volumetric Flow Conversion",
        "category": "Unit Conversions",
        "description": "Convert between m³/s, m³/h, L/s, L/min, gal/min, ft³/s, bbl/d.",
        "inputs": [
            _i("value", "Value", "", 1.0),
            _i("from",  "From",  "", "m3/h", "select", units.ALLOWED["volume_flow"]),
            _i("to",    "To",    "", "gal/min", "select", units.ALLOWED["volume_flow"]),
        ],
        "compute": units.volume_flow,
    },

    # ---------- Process Economics ----------------------------------------
    "npv": {
        "title": "Net Present Value",
        "category": "Process Economics",
        "description": "NPV of a stream of cash flows. Year 0 first (typically negative).",
        "inputs": [
            _i("rate",  "Discount rate", "%", 10),
            _i("flows", "Cash flows (year 0, 1, 2, …)", "$",
               "-100000, 25000, 30000, 35000, 40000, 45000", "text"),
        ],
        "compute": economics.npv,
    },
    "payback": {
        "title": "Payback Period",
        "category": "Process Economics",
        "description": "Simple (undiscounted) payback period from a list of cash flows.",
        "inputs": [
            _i("flows", "Cash flows (year 0, 1, 2, …)", "$",
               "-100000, 30000, 30000, 30000, 30000, 30000", "text"),
        ],
        "compute": economics.payback_period,
    },
    "lang_capex": {
        "title": "CAPEX from Lang Factor",
        "category": "Process Economics",
        "description": "Total fixed capital from purchased equipment cost using the Lang factor.",
        "inputs": [
            _i("pec",  "Σ Purchased equipment cost", "$", 500000),
            _i("lang", "Lang factor",                "-", 4.74),
        ],
        "compute": economics.lang_capex,
    },

    # ---------- Mass & Energy Balance ------------------------------------
    "mb_distillation": {
        "title": "Distillation Overall Balance",
        "category": "Mass & Energy Balance",
        "description": "Overall mass balance on a binary column: solve D and B from F, xF, xD, xB.",
        "inputs": [
            _i("F",  "Feed flow F",        "kg/h or mol/h", 1000),
            _i("xF", "Feed composition xF", "-", 0.40),
            _i("xD", "Distillate xD",       "-", 0.95),
            _i("xB", "Bottoms xB",          "-", 0.05),
        ],
        "compute": balance.binary_distillation_balance,
    },
    "mb_mixer": {
        "title": "Stream Mixer (Mass Balance)",
        "category": "Mass & Energy Balance",
        "description": ("Mix any number of streams. One per line as 'flow, composition' "
                        "(use consistent units, e.g. kg/h)."),
        "inputs": [
            _i("streams", "Streams (one per line: flow, x)", "",
               "100, 0.10\n200, 0.40\n50, 0.80", "textarea"),
        ],
        "compute": balance.stream_mixer,
    },
    "mb_split": {
        "title": "Component Split (Recovery-Based)",
        "category": "Mass & Energy Balance",
        "description": "Single-equipment split with specified key recoveries.",
        "inputs": [
            _i("F",      "Feed flow F",         "flow", 1000),
            _i("xF",     "Feed composition xF", "-",    0.40),
            _i("rec_LK", "Light-key recovery in top", "%", 95),
            _i("rec_HK", "Heavy-key recovery in bottom", "%", 95),
        ],
        "compute": balance.component_split,
    },
    "eb_sensible": {
        "title": "Sensible Heat Duty",
        "category": "Mass & Energy Balance",
        "description": "Q = m·Cp·ΔT for a single-phase stream.",
        "inputs": [
            _i("m",  "Mass flow m",       "kg/s",   1.0),
            _i("Cp", "Heat capacity Cp",  "J/kg·K", 4180),
            _i("T1", "Inlet temperature T1",  "°C", 25),
            _i("T2", "Outlet temperature T2", "°C", 80),
        ],
        "compute": balance.sensible_heat,
    },
    "eb_latent": {
        "title": "Latent Heat Duty",
        "category": "Mass & Energy Balance",
        "description": "Q = m·λ for vaporization, condensation, melting or freezing.",
        "inputs": [
            _i("m",   "Mass flow m",       "kg/s", 0.5),
            _i("lam", "Latent heat λ",     "J/kg", 2257000),
        ],
        "compute": balance.latent_heat,
    },
    "eb_adiabatic_mix": {
        "title": "Adiabatic Mixer Outlet T",
        "category": "Mass & Energy Balance",
        "description": "Outlet temperature when two streams adiabatically mix (no phase change).",
        "inputs": [
            _i("m1",  "Stream 1 mass flow m1",  "kg/s",   1.0),
            _i("Cp1", "Stream 1 Cp1",           "J/kg·K", 4180),
            _i("T1",  "Stream 1 temperature T1","°C",     20),
            _i("m2",  "Stream 2 mass flow m2",  "kg/s",   0.5),
            _i("Cp2", "Stream 2 Cp2",           "J/kg·K", 4180),
            _i("T2",  "Stream 2 temperature T2","°C",     80),
        ],
        "compute": balance.adiabatic_mix_temperature,
    },
    "eb_overall": {
        "title": "Overall Energy Balance (Q − W = ΔH)",
        "category": "Mass & Energy Balance",
        "description": "Steady-state open-system energy balance. Pick the variable to solve for.",
        "inputs": [
            _i("Q",     "Heat in Q",           "W", 0),
            _i("W",     "Shaft work out W",    "W", 0),
            _i("H_in",  "Inlet enthalpy H_in", "W", 100000),
            _i("H_out", "Outlet enthalpy H_out","W", 0),
            _i("solve_for", "Solve for", "", "H_out", "select",
               ["Q", "W", "H_in", "H_out"]),
        ],
        "compute": balance.overall_energy_balance,
    },
    "eb_cp_polynomial": {
        "title": "Sensible Enthalpy with Cp(T) Polynomial",
        "category": "Mass & Energy Balance",
        "description": "ΔH = ∫(a + b·T + c·T² + d·T³) dT for an ideal-gas/liquid stream.",
        "inputs": [
            _i("a",  "Cp coefficient a",      "J/mol·K",      28.11),
            _i("b",  "Cp coefficient b",      "J/mol·K²",     0.1967e-2),
            _i("c",  "Cp coefficient c",      "J/mol·K³",     0.4802e-5),
            _i("d",  "Cp coefficient d",      "J/mol·K⁴",    -1.966e-9),
            _i("T1", "Initial temperature T1", "K",            298.15),
            _i("T2", "Final temperature T2",   "K",            673.15),
            _i("n",  "Moles n (or molar flow)", "mol or mol/s", 1.0),
        ],
        "compute": balance.cp_polynomial_enthalpy,
    },
    "eb_hess": {
        "title": "Heat of Reaction (Hess's Law)",
        "category": "Mass & Energy Balance",
        "description": "ΔH_rxn from heats of formation. One species per line: 'name, ΔHf° (kJ/mol), ν'.",
        "inputs": [
            _i("reactants", "Reactants",  "",
               "CH4(g), -74.85, 1\nO2(g), 0, 2", "textarea"),
            _i("products",  "Products",   "",
               "CO2(g), -393.51, 1\nH2O(l), -285.83, 2", "textarea"),
        ],
        "compute": balance.heat_of_reaction_hess,
    },
    "eb_flame_temp": {
        "title": "Adiabatic Flame Temperature (lumped)",
        "category": "Mass & Energy Balance",
        "description": "Approximate adiabatic flame temperature from LHV, flue-gas moles and average Cp.",
        "inputs": [
            _i("LHV",    "LHV per kg fuel",            "J/kg",      45e6),
            _i("n_fg",   "Flue-gas moles per kg fuel", "mol/kg",    430),
            _i("Cp_fg",  "Average Cp of flue gas",     "J/mol·K",   34),
            _i("T_ref",  "Reference (inlet) T",        "°C",        25),
            _i("Q_loss", "Heat losses",                "J/kg fuel", 0),
        ],
        "compute": balance.adiabatic_flame_temp,
    },
    "mb_recycle": {
        "title": "Recycle / Purge Material Balance",
        "category": "Mass & Energy Balance",
        "description": "Steady-state overall balance with recycle and purge: F = P + G.",
        "inputs": [
            _i("F",        "Fresh feed F", "flow", 100),
            _i("P",        "Product P",    "flow", 95),
            _i("G",        "Purge G",      "flow", 5),
            _i("R_over_F", "Recycle ratio R/F", "-", 4.0),
        ],
        "compute": balance.recycle_balance,
    },

    # ---------- Stoichiometry / Combustion -------------------------------
    "comp_wt_to_mol": {
        "title": "Composition: Weight % → Mole %",
        "category": "Stoichiometry & Combustion",
        "description": "Convert mixture weight fractions to mole fractions. One component per line: 'name, MW, wt%'.",
        "inputs": [
            _i("components", "Components (name, MW, wt%)", "",
               "N2, 28, 75\nO2, 32, 23\nAr, 40, 2", "textarea"),
        ],
        "compute": stoichiometry.wt_to_mol_percent,
    },
    "comp_mol_to_wt": {
        "title": "Composition: Mole % → Weight %",
        "category": "Stoichiometry & Combustion",
        "description": "Convert mole fractions to weight fractions. One component per line: 'name, MW, mol%'.",
        "inputs": [
            _i("components", "Components (name, MW, mol%)", "",
               "N2, 28, 78\nO2, 32, 21\nAr, 40, 1", "textarea"),
        ],
        "compute": stoichiometry.mol_to_wt_percent,
    },
    "theoretical_air": {
        "title": "Theoretical & Actual Air for Combustion",
        "category": "Stoichiometry & Combustion",
        "description": "Theoretical O₂/air, actual air with % excess, and Orsat (dry) flue-gas analysis from ultimate fuel analysis.",
        "inputs": [
            _i("C",      "Carbon C (wt%)",   "%",  85),
            _i("H",      "Hydrogen H (wt%)", "%",  12),
            _i("S",      "Sulphur S (wt%)",  "%",  1),
            _i("N",      "Nitrogen N (wt%)", "%",  0),
            _i("O",      "Oxygen O (wt%)",   "%",  1),
            _i("ash",    "Ash (wt%)",        "%",  0.5),
            _i("H2O",    "Moisture (wt%)",   "%",  0.5),
            _i("excess", "% Excess air",     "%",  20),
        ],
        "compute": combustion.theoretical_air,
    },
    "hhv_dulong": {
        "title": "HHV / LHV from Dulong's Formula",
        "category": "Stoichiometry & Combustion",
        "description": "Higher and lower heating value of a solid/liquid fuel from ultimate analysis.",
        "inputs": [
            _i("C",   "Carbon C (wt%)",   "%", 80),
            _i("H",   "Hydrogen H (wt%)", "%", 5),
            _i("O",   "Oxygen O (wt%)",   "%", 6),
            _i("S",   "Sulphur S (wt%)",  "%", 1),
            _i("H2O", "Moisture (wt%)",   "%", 4),
        ],
        "compute": combustion.hhv_dulong,
    },

    # ---------- Equipment Design ----------------------------------------
    "pump_design": {
        "title": "Pump Design (Full Datasheet)",
        "category": "Equipment Design",
        "description": "Complete centrifugal-pump hydraulic design: TDH, NPSHa, motor sizing, suction/discharge line sizing, with datasheet and schematic.",
        "inputs": [
            _i("tag",          "Tag",                       "",     "P-101", "text"),
            _i("fluid",        "Fluid",                     "",     "Water", "text"),
            _i("Q",            "Capacity Q",                "m³/h", 50),
            _i("rho",          "Density ρ",                 "kg/m³", 1000),
            _i("mu",           "Viscosity μ",               "Pa·s", 0.001),
            _i("P_suc",        "Suction pressure (abs)",   "Pa",   101325),
            _i("P_dis",        "Discharge pressure (abs)", "Pa",   400000),
            _i("H_stat",       "Static head (ΔZ)",          "m",    15),
            _i("L_suc",        "Suction line length",      "m",    8),
            _i("L_dis",        "Discharge line length",    "m",    30),
            _i("K_suc",        "ΣK suction fittings",       "-",    2.5),
            _i("K_dis",        "ΣK discharge fittings",     "-",    8.0),
            _i("Pv",           "Vapour pressure Pv",       "Pa",   3170),
            _i("h_static_suc", "Suction tank head above pump", "m", 1.0),
            _i("NPSHr",        "NPSH required (vendor)",   "m",    3.0),
            _i("v_suc",        "Target suction velocity",  "m/s",  1.5),
            _i("v_dis",        "Target discharge velocity","m/s",  2.5),
            _i("eta_pump",     "Pump efficiency",          "-",    0.70),
            _i("eta_motor",    "Motor efficiency",         "-",    0.92),
            _i("margin",       "Design margin",            "%",    15),
            _i("N_rpm",        "Speed",                    "rpm",  2950),
            _i("T_op",         "Operating temperature",    "°C",   25),
        ],
        "compute": equipment.pump_design,
    },
    "hx_design": {
        "title": "Heat Exchanger Design (TEMA Datasheet)",
        "category": "Equipment Design",
        "description": "Shell & tube heat-exchanger design (Kern method) with full TEMA-style datasheet and schematic.",
        "inputs": [
            _i("tag",     "Tag",                   "",      "E-101", "text"),
            _i("hot",     "Hot fluid",            "",      "Process",       "text"),
            _i("cold",    "Cold fluid",           "",      "Cooling water", "text"),
            _i("method",  "Design method",        "",      "LMTD",  "select",
               ["LMTD", "NTU"]),
            _i("arrangement", "Flow arrangement", "",      "Counter-current", "select",
               ["Counter-current", "Parallel", "Shell-and-tube 1-2", "Cross-flow"]),
            _i("TEMA",    "TEMA type",            "",      "AES",   "select",
               ["AES", "BEM", "BES", "AET", "AKT", "NEN"]),
            _i("pos",     "Position",             "",      "Horizontal", "select",
               ["Horizontal", "Vertical"]),
            _i("m_hot",   "Hot mass flow",        "kg/s",  2.5),
            _i("Cp_hot",  "Hot Cp",               "J/kg·K",4180),
            _i("Th_in",   "Hot inlet T",          "°C",    120),
            _i("Th_out",  "Hot outlet T",         "°C",    60),
            _i("m_cold",  "Cold mass flow",       "kg/s",  3.0),
            _i("Cp_cold", "Cold Cp",              "J/kg·K",4180),
            _i("Tc_in",   "Cold inlet T",         "°C",    30),
            _i("Tc_out",  "Cold outlet T (0=calc)","°C",   0),
            _i("U",       "Clean U",              "W/m²K", 500),
            _i("Ft",      "Ft correction",        "-",     0.92),
            _i("fouling", "Combined fouling Rd",  "m²K/W", 0.00035),
            _i("do",      "Tube OD",              "mm",    19.05),
            _i("BWG",     "Tube BWG",             "-",     14),
            _i("L_tube",  "Tube length",          "m",     6.0),
            _i("PT",      "Pitch ratio Pt/do",    "-",     1.25),
            _i("layout",  "Tube layout",          "",      "Triangular", "select",
               ["Triangular", "Square"]),
            _i("n_pass",  "Tube passes",          "-",     2),
        ],
        "compute": equipment.hx_design,
    },
    "column_design": {
        "title": "Distillation Column Design (Datasheet)",
        "category": "Equipment Design",
        "description": "Binary distillation shortcut design (Fenske–Underwood–Gilliland–Kirkbride) with column diameter, height and datasheet.",
        "inputs": [
            _i("tag",     "Tag",                  "",       "T-101", "text"),
            _i("service", "Service",              "",       "Binary separation", "text"),
            _i("method",  "Design method",        "",       "FUG (shortcut)", "select",
               ["FUG (shortcut)", "McCabe-Thiele"]),
            _i("F",       "Feed flow F",          "kmol/h", 100),
            _i("zF",      "Feed mole frac zF",    "-",      0.4),
            _i("xD",      "Distillate xD",        "-",      0.95),
            _i("xB",      "Bottoms xB",           "-",      0.05),
            _i("q",       "Feed thermal cond. q", "-",      1.0),
            _i("alpha",   "Relative volatility α","-",     2.5),
            _i("R_mult",  "R / Rmin",             "-",      1.5),
            _i("eta_tray","Tray efficiency",      "-",      0.65),
            _i("HETP",    "Tray spacing / HETP",  "m",      0.6),
            _i("rho_L",   "Liquid density",       "kg/m³",  750),
            _i("rho_V",   "Vapour density",       "kg/m³",  3.0),
            _i("MW",      "Average MW",           "g/mol",  50),
            _i("K_SB",    "Souders–Brown K",      "m/s",    0.06),
            _i("P_top",   "Top pressure",         "Pa",     101325),
        ],
        "compute": equipment.column_design,
    },
    "separator_design": {
        "title": "Vertical 2-Phase Separator (KO Drum)",
        "category": "Equipment Design",
        "description": "Vertical knock-out drum sized by Souders–Brown vapour velocity and liquid residence time.",
        "inputs": [
            _i("tag",   "Tag",                       "",      "V-101", "text"),
            _i("Q_gas", "Gas volumetric flow (actual)", "m³/s", 0.5),
            _i("m_liq", "Liquid mass flow",          "kg/s",  5.0),
            _i("rho_g", "Gas density",               "kg/m³", 3.0),
            _i("rho_l", "Liquid density",            "kg/m³", 750),
            _i("K",     "Souders K (mist pad)",      "m/s",   0.107),
            _i("t_res", "Liquid residence time",     "s",     300),
        ],
        "compute": equipment.separator_design,
    },

    # ---------- Piping & Valves -----------------------------------------
    "line_sizing": {
        "title": "Advanced Line Sizing (NPS + ΔP)",
        "category": "Piping & Valves",
        "description": "Pick economic NPS for a liquid or gas line and check Reynolds + Darcy–Weisbach ΔP / 100 m against Branan limits.",
        "inputs": [
            _i("tag",      "Line tag",            "",     "L-101", "text"),
            _i("phase",    "Phase",               "",     "Liquid", "select",
               ["Liquid", "Gas", "Two-phase"]),
            _i("m",        "Mass flow",           "kg/s", 10),
            _i("rho",      "Density ρ",           "kg/m³",1000),
            _i("mu",       "Viscosity μ",         "Pa·s", 0.001),
            _i("L",        "Pipe length",         "m",    100),
            _i("eps",      "Roughness ε",         "m",    4.5e-5),
            _i("K_fit",    "ΣK fittings",          "-",    4.0),
            _i("v_target", "Target velocity",     "m/s",  2.0),
        ],
        "compute": piping.line_sizing,
    },
    "control_valve": {
        "title": "Control Valve Cv",
        "category": "Piping & Valves",
        "description": "Liquid (cavitation-aware) or gas (Crane form) control-valve Cv sizing.",
        "inputs": [
            _i("tag",   "Tag",        "",   "FV-101", "text"),
            _i("name",  "Fluid name", "",   "Water",  "text"),
            _i("fluid", "Service",    "",   "Liquid", "select", ["Liquid","Gas"]),
            _i("Q",     "Flow (liquid m³/h, gas scfh)", "", 50),
            _i("P1",    "P1 (abs)",   "Pa", 600000),
            _i("P2",    "P2 (abs)",   "Pa", 400000),
            _i("rho",   "Liquid density", "kg/m³", 1000),
            _i("Pv",    "Pv (liquid)",     "Pa",   3170),
            _i("Pc",    "Pc (liquid)",     "Pa",   2.21e7),
            _i("FL",    "FL recovery factor","-",   0.9),
            _i("SG",    "SG (gas, air = 1)", "-",   0.65),
            _i("T",     "T (gas)",            "K",   293.15),
        ],
        "compute": piping.control_valve_cv,
    },
    "relief_valve": {
        "title": "Pressure Relief Valve (API 520)",
        "category": "Piping & Valves",
        "description": "PSV orifice area for gas/vapour or liquid relief per API 520, with API standard orifice selection.",
        "inputs": [
            _i("tag",     "Tag",         "",      "PSV-101", "text"),
            _i("service", "Service",     "",      "Gas overpressure", "text"),
            _i("fluid",   "Phase",       "",      "Gas", "select", ["Gas","Liquid"]),
            _i("Kd",      "Kd discharge coeff.", "-", 0.975),
            _i("Kb",      "Kb back-pressure",    "-", 1.0),
            _i("Kc",      "Kc combination",       "-", 1.0),
            _i("Kw",      "Kw (liquid)",          "-", 1.0),
            _i("Kv",      "Kv (liquid Re)",       "-", 0.98),
            _i("W",       "W relieving (gas)",    "kg/h", 5000),
            _i("Q",       "Q relieving (liquid)", "m³/h", 50),
            _i("SG",      "SG (liquid)",          "-",    1.0),
            _i("MW",      "MW (gas)",             "-",    29),
            _i("k",       "k = Cp/Cv (gas)",      "-",    1.4),
            _i("Z",       "Z (gas)",              "-",    1.0),
            _i("T",       "T relieving (gas)",    "K",    373.15),
            _i("P1",      "P1 relieving (abs)",   "Pa",   1.1e6),
            _i("P2",      "P2 back (abs)",        "Pa",   101325),
        ],
        "compute": piping.relief_valve,
    },
}
# Order categories nicely in the sidebar
CATEGORY_ORDER = [
    "Equipment Design",
    "Piping & Valves",
    "Fluid Mechanics",
    "Heat Transfer",
    "Mass Transfer",
    "Thermodynamics",
    "Reaction Engineering",
    "Mass & Energy Balance",
    "Stoichiometry & Combustion",
    "Unit Conversions",
    "Process Economics",
]


def grouped():
    """Return list of (category, [(id, spec), ...]) in display order."""
    out = []
    for cat in CATEGORY_ORDER:
        items = [(k, v) for k, v in CALCULATORS.items() if v["category"] == cat]
        if items:
            out.append((cat, items))
    return out
