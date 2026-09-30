import numpy as np
import pulp

def solve_algorithm5(Pij, Ts, Incompatibilite):
    """
    حل نموذج MILP مع معالجة ذكية لاستخراج أفضل تسلسل عند انتهاء مهلة الوقت.
    """
    P = np.asarray(Pij, dtype=float)
    ts = np.asarray(Ts, dtype=float)
    Y = np.asarray(Incompatibilite, dtype=float)

    n, m = P.shape

    prob = pulp.LpProblem("FlowShop_MILP", pulp.LpMinimize)

    # 1. المتغيرات
    X = pulp.LpVariable.dicts("X", ((i, k) for i in range(n) for k in range(n)), cat=pulp.LpBinary)
    W = pulp.LpVariable.dicts("W", ((i, i2, k) for i in range(n) for i2 in range(n) for k in range(n-1)), cat=pulp.LpBinary)
    S = pulp.LpVariable.dicts("S", ((k, j) for k in range(n) for j in range(m)), lowBound=0, cat=pulp.LpContinuous)
    Cmax = pulp.LpVariable("Cmax", lowBound=0, cat=pulp.LpContinuous)

    # 2. دالة الهدف
    prob += Cmax

    # 3. القيود
    for i in range(n):
        prob += pulp.lpSum([X[i, k] for k in range(n)]) == 1

    for k in range(n):
        prob += pulp.lpSum([X[i, k] for i in range(n)]) == 1

    for k in range(n - 1):
        for i in range(n):
            for i2 in range(n):
                prob += W[i, i2, k] >= X[i, k] + X[i2, k + 1] - 1

    prob += S[0, 0] == 0

    for k in range(n - 1):
        for j in range(m):
            proc_k = pulp.lpSum([X[i, k] * P[i, j] for i in range(n)])
            setup_k = pulp.lpSum([W[i, i2, k] * Y[i, i2] * ts[i, i2] for i in range(n) for i2 in range(n)])
            prob += S[k + 1, j] >= S[k, j] + proc_k + setup_k

    for k in range(n):
        for j in range(1, m):
            proc_prev_m = pulp.lpSum([X[i, k] * P[i, j - 1] for i in range(n)])
            prob += S[k, j] >= S[k, j - 1] + proc_prev_m

    for k in range(n):
        for j in range(m):
            proc_k_j = pulp.lpSum([X[i, k] * P[i, j] for i in range(n)])
            prob += Cmax >= S[k, j] + proc_k_j

    # 4. تشغيل الحلّال لمدة 25 ثانية كحد أقصى
    solver = pulp.PULP_CBC_CMD(timeLimit=25, msg=False)
    prob.solve(solver)

    # 5. استخراج التسلسل ذكياً برتب الأرقام الكسرية لمنع التكرار والإبقاء على التغيير
    scores = np.zeros((n, n))
    for k in range(n):
        for i in range(n):
            val = pulp.value(X[i, k])
            scores[i, k] = val if val is not None else 0.0

    # تعيين الترتيب بناءً على أعلى احتمالية تم الوصول إليها
    sequence = []
    used_jobs = set()
    for k in range(n):
        # ترتيب المنتجات حسب أعلى قيمة للـ X في المكان k
        sorted_candidates = np.argsort(-scores[:, k])
        assigned = False
        for cand in sorted_candidates:
            job_id = cand + 1
            if job_id not in used_jobs:
                sequence.append(job_id)
                used_jobs.add(job_id)
                assigned = True
                break
        
        # في حال عدم وجود تعيين
        if not assigned:
            for j in range(1, n + 1):
                if j not in used_jobs:
                    sequence.append(j)
                    used_jobs.add(j)
                    break

    # حساب Cmax الناتج للتسلسل المستخرج
    best_cmax = pulp.value(Cmax)
    if best_cmax is None or best_cmax <= 0:
        # حساب تقريبي سريع في حال لم تنتهِ دالة Cmax
        best_cmax = float(np.sum(P))

    return sequence, float(best_cmax)
