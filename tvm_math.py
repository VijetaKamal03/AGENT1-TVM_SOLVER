"""
tvm_math.py — Deterministic TVM calculation backend.

Sign convention:
  Cash INFLOWS  → positive  (money received)
  Cash OUTFLOWS → negative  (money paid out)

All rate inputs/outputs are per-period decimals unless stated otherwise.
"""

import math
from typing import Optional


# ── Rate Conversions ──────────────────────────────────────────────────────────

def nominal_to_effective(i_nominal: float, m: int) -> float:
    """Convert nominal annual rate compounded m times/year → effective annual rate.
    i_eff = (1 + i_nom/m)^m - 1
    """
    return (1 + i_nominal / m) ** m - 1


def effective_to_nominal(i_eff: float, m: int) -> float:
    """Convert effective annual rate → nominal annual rate compounded m times/year.
    i_nom = m * ((1 + i_eff)^(1/m) - 1)
    """
    return m * ((1 + i_eff) ** (1 / m) - 1)


def effective_to_force(i_eff: float) -> float:
    """Convert effective annual rate → force of interest (continuous).
    δ = ln(1 + i)
    """
    return math.log(1 + i_eff)


def force_to_effective(delta: float) -> float:
    """Convert force of interest → effective annual rate.
    i = e^δ - 1
    """
    return math.exp(delta) - 1


def rate_per_period(i_annual: float, m: int) -> float:
    """Convert effective annual rate → effective rate per sub-period.
    i_period = (1 + i_annual)^(1/m) - 1
    """
    return (1 + i_annual) ** (1 / m) - 1


def periods_to_years(n_periods: float, m: int) -> float:
    """Convert number of compounding periods → years."""
    return n_periods / m


def years_to_periods(years: float, m: int) -> float:
    """Convert years → number of compounding periods."""
    return years * m


# ── Core TVM Functions ────────────────────────────────────────────────────────

def future_value(pv: float, i: float, n: float) -> float:
    """FV = PV * (1 + i)^n  (single lump sum, compound interest).
    
    Args:
        pv: Present value (negative = outflow)
        i:  Interest rate per period (decimal)
        n:  Number of periods
    Returns:
        FV (same sign convention: positive = inflow to holder)
    """
    return pv * (1 + i) ** n


def present_value(fv: float, i: float, n: float) -> float:
    """PV = FV / (1 + i)^n  (single lump sum, compound interest).
    
    Args:
        fv: Future value
        i:  Interest rate per period (decimal)
        n:  Number of periods
    Returns:
        PV
    """
    return fv / (1 + i) ** n


def solve_rate(pv: float, fv: float, n: float) -> float:
    """Solve for the per-period rate given PV, FV, and n.
    i = (FV/PV)^(1/n) - 1
    
    Note: pv and fv must have OPPOSITE signs (one in, one out).
    """
    if pv == 0:
        raise ValueError("PV cannot be zero when solving for rate.")
    ratio = abs(fv) / abs(pv)
    return ratio ** (1 / n) - 1


def solve_periods(pv: float, fv: float, i: float) -> float:
    """Solve for n given PV, FV, and per-period rate i.
    n = ln(FV/PV) / ln(1+i)
    
    Note: pv and fv must have opposite signs.
    """
    if i <= -1:
        raise ValueError("Interest rate must be > -100%.")
    if pv == 0:
        raise ValueError("PV cannot be zero.")
    ratio = abs(fv) / abs(pv)
    return math.log(ratio) / math.log(1 + i)


# ── Equation of Value ─────────────────────────────────────────────────────────

def equation_of_value(
    cashflows: list[tuple[float, float]],
    i: float,
    valuation_date: float = 0.0,
) -> float:
    """Accumulate / discount all cashflows to a common valuation date.
    
    Args:
        cashflows: List of (amount, time) tuples. Positive = inflow.
        i:         Effective rate per period
        valuation_date: The time point to bring everything to (default t=0)
    Returns:
        Net present/accumulated value at valuation_date.
        A result of 0 means the equation of value is satisfied.
    """
    total = 0.0
    for amount, t in cashflows:
        # Discount/accumulate from time t to valuation_date
        total += amount * (1 + i) ** (valuation_date - t)
    return total


def solve_unknown_payment(
    known_cashflows: list[tuple[float, float]],
    unknown_time: float,
    i: float,
    valuation_date: float = 0.0,
) -> float:
    """Find the unknown payment X at `unknown_time` that makes the equation of value = 0.
    
    The known cashflows are accumulated/discounted to valuation_date.
    X * (1+i)^(valuation_date - unknown_time) = -sum(known accumulated values)
    → X = -EoV(known) / (1+i)^(valuation_date - unknown_time)
    """
    known_pv = equation_of_value(known_cashflows, i, valuation_date)
    factor = (1 + i) ** (valuation_date - unknown_time)
    if factor == 0:
        raise ValueError("Accumulation factor is zero — check inputs.")
    return -known_pv / factor


# ── Continuous Compounding ────────────────────────────────────────────────────

def fv_continuous(pv: float, delta: float, t: float) -> float:
    """FV under continuous compounding.
    FV = PV * e^(δ·t)
    """
    return pv * math.exp(delta * t)


def pv_continuous(fv: float, delta: float, t: float) -> float:
    """PV under continuous compounding.
    PV = FV * e^(-δ·t)
    """
    return fv * math.exp(-delta * t)


# ── Simple Interest ───────────────────────────────────────────────────────────

def fv_simple(pv: float, i: float, n: float) -> float:
    """FV under simple interest. FV = PV * (1 + i*n)."""
    return pv * (1 + i * n)


def pv_simple(fv: float, i: float, n: float) -> float:
    """PV under simple interest. PV = FV / (1 + i*n)."""
    return fv / (1 + i * n)


# ── Discount Rates ────────────────────────────────────────────────────────────

def discount_rate_from_interest(i: float) -> float:
    """Annual effective discount rate d from annual effective interest rate i.
    d = i / (1 + i)
    """
    return i / (1 + i)


def interest_rate_from_discount(d: float) -> float:
    """Annual effective interest rate i from annual effective discount rate d.
    i = d / (1 - d)
    """
    if d >= 1:
        raise ValueError("Discount rate must be < 1.")
    return d / (1 - d)
