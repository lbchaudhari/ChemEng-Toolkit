"""Process economics calculations."""
from __future__ import annotations


def _r(value, unit, label):
    return {"label": label, "value": value, "unit": unit}


def _parse_flows(text):
    """Accept comma- or space-separated cash flows."""
    parts = [p for p in text.replace(",", " ").split() if p]
    return [float(p) for p in parts]


def npv(inp):
    """NPV with year-0 investment included in cash-flow list."""
    rate = float(inp["rate"]) / 100.0
    flows = _parse_flows(inp["flows"])
    if not flows:
        raise ValueError("Provide at least one cash flow (year 0 first).")
    npv_val = sum(cf / (1 + rate) ** t for t, cf in enumerate(flows))
    pv_list = [cf / (1 + rate) ** t for t, cf in enumerate(flows)]
    return {
        "results": [
            _r(round(npv_val, 2), "$", "Net Present Value"),
            _r(len(flows) - 1, "yr", "Project horizon"),
            _r(round(rate * 100, 3), "%", "Discount rate"),
        ],
        "notes": [
            "NPV = Σ CF_t / (1 + r)^t  for t = 0..N",
            "Year 0 cash flow is the initial investment (typically negative).",
            "Discounted CFs: " + ", ".join(f"{x:,.2f}" for x in pv_list),
        ],
    }


def payback_period(inp):
    flows = _parse_flows(inp["flows"])
    if not flows or flows[0] >= 0:
        raise ValueError("Year 0 cash flow must be negative (initial investment).")
    cum = 0.0
    for t, cf in enumerate(flows):
        prev = cum
        cum += cf
        if cum >= 0:
            # linear interpolation within year
            frac = -prev / cf if cf != 0 else 0
            pb = (t - 1) + frac
            return {
                "results": [
                    _r(round(pb, 3), "yr", "Payback period"),
                    _r(round(cum, 2), "$", "Cumulative CF at payback"),
                ],
                "notes": ["Simple (undiscounted) payback period."],
            }
    return {
        "results": [_r("Not recovered within horizon", "", "Payback period")],
        "notes": [f"Cumulative cash flow after year {len(flows)-1}: {cum:,.2f}"],
    }


def lang_capex(inp):
    """Total fixed CAPEX from purchased equipment cost via Lang factor."""
    pec = float(inp["pec"])
    factor = float(inp.get("lang", 4.74))
    capex = pec * factor
    return {
        "results": [
            _r(round(capex, 2), "$", "Total fixed CAPEX"),
            _r(round(capex - pec, 2), "$", "Installation + indirect costs"),
            _r(round(factor, 3), "-", "Lang factor used"),
        ],
        "notes": [
            "CAPEX_total ≈ Lang_factor × Σ(Purchased Equipment Cost)",
            "Typical Lang factors: 3.10 (solids), 3.63 (solid-fluid), 4.74 (fluids).",
        ],
    }
