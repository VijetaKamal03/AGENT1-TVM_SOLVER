"""
test_tvm_math.py — Verified test suite for tvm_math.py

All expected values cross-checked against textbook FM formulas.
Run: python test_tvm_math.py
"""

import sys, math
sys.path.insert(0, '.')
from tools.tvm_math import *


def check(name, result, expected, tol=1e-4):
    ok = abs(result - expected) < tol
    status = "PASS ✓" if ok else f"FAIL ✗  got={result:.8f}  exp={expected:.8f}"
    print(f"  {name}: {status}")
    return ok


print("=" * 60)
print("TVM MATH VERIFICATION SUITE")
print("=" * 60)
passed = 0
total = 0

print("\n── Future Value ──")
# FV = 1000 * 1.06^5 = 1338.2256
r = future_value(1000, 0.06, 5); total += 1; passed += check("FV(1000, 6%, 5y)", r, 1338.2256)
r = future_value(-2500, 0.08, 10); total += 1; passed += check("FV(-2500, 8%, 10y)", r, -2500 * 1.08**10)

print("\n── Present Value ──")
r = present_value(1338.2256, 0.06, 5); total += 1; passed += check("PV(1338.2256, 6%, 5y)", r, 1000.0)
r = present_value(10000, 0.05, 20); total += 1; passed += check("PV(10000, 5%, 20y)", r, 10000/1.05**20)

print("\n── Solve for Rate ──")
# (2000/1000)^(1/10) - 1 = 7.177% to double in 10y
i = solve_rate(1000, 2000, 10); total += 1; passed += check("Rate to double in 10y", i, 2**0.1 - 1, 1e-8)
i = solve_rate(5000, 8000, 6); total += 1; passed += check("Rate: 5000→8000 in 6y", i, (8000/5000)**(1/6)-1, 1e-8)

print("\n── Solve for Periods ──")
n = solve_periods(1000, 2000, 2**0.1 - 1); total += 1; passed += check("n to double at correct rate", n, 10.0)
n = solve_periods(100, 200, 0.07); total += 1; passed += check("n to double at 7%", n, math.log(2)/math.log(1.07), 1e-8)

print("\n── Rate Conversions ──")
# 12% nom monthly → eff annual: (1.01)^12 - 1 = 12.6825%
r = nominal_to_effective(0.12, 12); total += 1; passed += check("12% nom/m → eff annual", r, 1.01**12 - 1, 1e-10)
r = nominal_to_effective(0.06, 2);  total += 1; passed += check("6% nom semi → eff annual", r, 1.03**2 - 1, 1e-10)

r = effective_to_nominal(0.126825, 12); total += 1; passed += check("eff 12.6825% → nom/m", r * 100, 12.0, 0.001)

print("\n── Force of Interest ──")
d = effective_to_force(0.05); total += 1; passed += check("δ for i=5%", d, math.log(1.05), 1e-12)
d = effective_to_force(0.10); total += 1; passed += check("δ for i=10%", d, math.log(1.10), 1e-12)
i = force_to_effective(math.log(1.05)); total += 1; passed += check("δ=ln(1.05) → i=5%", i, 0.05, 1e-10)

print("\n── Continuous Compounding ──")
fv = fv_continuous(1000, 0.05, 10); total += 1; passed += check("FV cont. δ=5% 10y", fv, 1000*math.exp(0.5), 1e-6)
pv = pv_continuous(math.exp(0.5)*1000, 0.05, 10); total += 1; passed += check("PV cont. reversal", pv, 1000.0, 1e-6)

print("\n── Simple Interest ──")
fv = fv_simple(1000, 0.06, 5); total += 1; passed += check("FV simple i=6% 5y", fv, 1000*(1+0.06*5))
pv = pv_simple(1300, 0.06, 5); total += 1; passed += check("PV simple i=6% 5y", pv, 1300/(1+0.06*5))

print("\n── Discount Rates ──")
d = discount_rate_from_interest(0.08); total += 1; passed += check("d from i=8%", d, 0.08/1.08, 1e-10)
i = interest_rate_from_discount(d); total += 1; passed += check("i from d (inverse)", i, 0.08, 1e-10)

print("\n── Equation of Value ──")
# Net value of [receive 1000 at t=0, pay 1000 at t=0] = 0
r = equation_of_value([(1000, 0), (-1000, 0)], 0.08, 0)
total += 1; passed += check("EoV balanced at t=0", r, 0.0, 1e-10)

# FV of 1000 at i=10% for 1 year = 1100
r = equation_of_value([(1000, 0)], 0.10, 1)
total += 1; passed += check("EoV: FV of 1000 at t=1", r, 1100.0, 1e-6)

print("\n── Solve Unknown Payment ──")
# Borrower receives 10000 at t=0, pays 4000 at t=3, pays X at t=7 at 8%
# X (outflow) = -(10000 - 4000/1.08^3) * 1.08^7
X = solve_unknown_payment([(10000, 0), (-4000, 3)], 7, 0.08, 0)
X_expected = -(10000 - 4000/1.08**3) * 1.08**7
total += 1; passed += check("Loan repayment X at t=7", X, X_expected, 0.001)

# Verify by substituting back: PV of (4000 at t=3) + PV of |X| at t=7 = 10000
check_pv = 4000/1.08**3 + abs(X)/1.08**7
total += 1; passed += check("EoV verification (PV check = 10000)", check_pv, 10000.0, 0.001)

print()
print("=" * 60)
print(f"RESULTS: {passed}/{total} tests passed")
if passed == total:
    print("ALL TESTS PASS ✓")
else:
    print(f"WARNING: {total - passed} test(s) FAILED")
print("=" * 60)
