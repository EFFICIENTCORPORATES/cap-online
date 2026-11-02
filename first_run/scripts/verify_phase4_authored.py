"""Re-derives every number in phase4_authored_questions.py independently and
checks the marks per chapter. Run before building: python verify_phase4_authored.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import phase4_authored_questions as a

ok = True


def check(label, got, want):
    global ok
    good = abs(got - want) < 1e-9
    ok &= good
    print(("PASS " if good else "FAIL ") + f"{label}: {got} (expected {want})")


# AS 1 Q1: 800 @25, sold 600 @40, NRV 32 / 20
sales, purchases = 600 * 40, 800 * 25
check("AS1 profit NRV32", sales - (purchases - 200 * min(25, 32)), 9000)
check("AS1 profit NRV20", sales - (purchases - 200 * min(25, 20)), 8000)
check("AS1 anticipated profit", 200 * (32 - 25), 1400)
check("AS1 loss recognised", 200 * (25 - 20), 1000)
check("AS1 policy change effect", 500000 - 460000, 40000)

# AS 17 Q1
rev = dict(A=450, B=260, C=150, D=70, E=70)
res = dict(A=70, B=-30, C=20, D=6, E=-4)
ast = dict(A=320, B=190, C=110, D=45, E=35)
check("AS17 total revenue", sum(rev.values()), 1000)
check("AS17 total result", sum(res.values()), 62)
check("AS17 total assets", sum(ast.values()), 700)
prof = sum(v for v in res.values() if v > 0)
loss = -sum(v for v in res.values() if v < 0)
check("AS17 profit pool", prof, 96)
check("AS17 loss pool", loss, 34)
base = max(prof, loss)
rep = {k for k in rev if rev[k] >= 0.1 * 1000 or abs(res[k]) >= 0.1 * base or ast[k] >= 0.1 * 700}
print("reportable:", sorted(rep))
ok &= rep == {"A", "B", "C"}
ext = dict(rev, A=450 - 50, B=260 - 10)
check("AS17 enterprise external revenue", sum(ext.values()), 940)
check("AS17 reportable external revenue", sum(ext[k] for k in rep), 800)
check("AS17 75% test pct", round(800 / 940 * 100, 1), 85.1)

# AS 17 Q3
check("AS17 segment revenue", 500 + 60, 560)
check("AS17 segment expense", 380 + 40, 420)
check("AS17 segment result", 560 - 420, 140)
check("AS17 segment assets", 600 + 150 + (120 - 20), 850)

# marks per chapter
need = {"applicability": 50, "intro-to-as": 29, "as01": 22, "as17": 27}
for k, rows in a.AUTHORED.items():
    m = sum(r["marks"] for r in rows)
    if k == "applicability":
        m += len(a.APPLICABILITY_MCQS)
    check(f"{k} authored marks", m, need[k])
    for r in rows:
        ok &= 5 <= r["marks"] <= 15
print("\nALL OK" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
