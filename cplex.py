import numpy as np
from pulp import (
    LpProblem,
    LpMinimize,
    LpVariable,
    LpBinary,
    LpContinuous,
    lpSum,
    value,
    PULP_CBC_CMD,
)

def solve_algorithm5(Pij, Ts, Incompatibilite):
    """
    حل نموذج MILP باستعمال مكتبة PuLP مع استيراد آمن لتفادي أخطاء Attributes.
    """
    P = np.asarray(Pij, dtype=float)
    ts = np.asarray(Ts, dtype=float)
    Y = np.asarray(Incompatibilite, dtype=float)

    n, m = P.shape

    prob = LpProblem("FlowShop_MILP", LpMinimize)

    # 1. تعريف المتغيرات باستخدام LpVariable.dicts مباشرة كـ Function
    X = LpVariable.dicts("X", ((i, k) for i in range(n) for k in range(n)), cat=LpBinary)
    W = LpVariable.dicts("W", ((i, i2, k) for i in range(n) for i2 in range(n) for k in range(n-1)), cat=LpBinary)
    S = LpVariable.dicts("S", ((k, j) for k in range(n) for j in range(m)), lowBound=0, cat=LpContinuous)
    Cmax = LpVariable("Cmax", lowBound=0, cat=LpContinuous)

    # 2. دالة الهدف
    prob += Cmax

    # 3. القيود
    # كل منتج يظهر مرة واحدة
    for i in range(n):
        prob += lpSum([X[i, k] for k in range(n)]) == 1

    # كل موقع يحتوي على منتج واحد
    for k in range(n):
        prob += lpSum([X[i, k] for i in range(n)]) == 1

    # قيود الربط المتسلسل
    for k in range(n - 1):
        for i in range(n):
            for i2 in range(n):
                prob += W[i, i2, k] >= X[i, k] + X[i2, k + 1] - 1

    # القيد المبدئي
    prob += S[0, 0] == 0

    # الانتقال بين المنتجات على نفس الآلة
    for k in range(n - 1):
        for j in range(m):
            proc_k = lpSum([X[i, k] * P[i, j] for i in range(n)])
            setup_k = lpSum([W[i, i2, k] * Y[i, i2] * ts[i, i2] for i in range(n) for i2 in range(n)])
            prob += S[k + 1, j] >= S[k, j] + proc_k + setup_k

    # الانتقال بين الآلات لنفس المنتج
    for k in range(n):
        for j in range(1, m):
            proc_prev_m = lpSum([X[i, k] * P[i, j - 1] for i in range(n)])
            prob += S[k, j] >= S[k, j - 1] + proc_prev_m

    # حساب Cmax
    for k in range(n):
        for j in range(m):
            proc_k_j = lpSum([X[i, k] * P[i, j] for i in range(n)])
            prob += Cmax >= S[k, j] + proc_k_j

    # 4. تشغيل الحلّال بمهلة زمنية (25 ثانية)
    solver = PULP_CBC_CMD(timeLimit=25, msg=False)
    prob.solve(solver)

    # 5. استخراج النتائج والتسلسل ذكياً برتب الأرقام الكسرية لمنع التكرار
    scores = np.zeros((n, n))
    for k in range(n):
        for i in range(n):
            val = value(X[i, k])
            scores[i, k] = val if val is not None else 0.0

    sequence = []
    used_jobs = set()
    for k in range(n):
        sorted_candidates = np.argsort(-scores[:, k])
        assigned = False
        for cand in sorted_candidates:
            job_id = cand + 1
            if job_id not in used_jobs:
                sequence.append(job_id)
                used_jobs.add(job_id)
                assigned = True
                break
        
        if not assigned:
            for j in range(1, n + 1):
                if j not in used_jobs:
                    sequence.append(j)
                    used_jobs.add(j)
                    break

    best_cmax = value(Cmax)
    if best_cmax is None or best_cmax <= 0:
        best_cmax = float(np.sum(P))

    return sequence, float(best_cmax)
