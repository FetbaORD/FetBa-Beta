import numpy as np
import pulp

def solve_algorithm5(Pij, Ts, Incompatibilite):
    """
    حل نموذج MILP باستعمال مكتبة PuLP المجهزة بحلّال CBC الأسرع مع مهلة زمنية.
    """
    # تحويل المدخلات إلى مصفوفات NumPy
    P = np.asarray(Pij, dtype=float)
    ts = np.asarray(Ts, dtype=float)
    Y = np.asarray(Incompatibilite, dtype=float)

    n, m = P.shape

    # 1. إنشاء مسألة التجميع الرياضي
    prob = pulp.LpProblem("FlowShop_MILP", pulp.LpMinimize)

    # 2. تعريف المتغيرات
    # X[i, k] = 1 إذا تم وضع المنتج i في الترتيب رقم k
    X = pulp.LpVariable.dicts("X", ((i, k) for i in range(n) for k in range(n)), cat=pulp.LpBinary)
    
    # W[i, i2, k] = 1 إذا كان المنتج i متبوعاً بالمنتج i2 في الترتيب k و k+1
    W = pulp.LpVariable.dicts("W", ((i, i2, k) for i in range(n) for i2 in range(n) for k in range(n-1)), cat=pulp.LpBinary)
    
    # S[k, j] = وقت بدء الموقع k على الآلة j
    S = pulp.LpVariable.dicts("S", ((k, j) for k in range(n) for j in range(m)), lowBound=0, cat=pulp.LpContinuous)
    
    # دالة الهدف: Makespan
    Cmax = pulp.LpVariable("Cmax", lowBound=0, cat=pulp.LpContinuous)

    # 3. دالة الهدف
    prob += Cmax

    # 4. إضافة القيود
    # أ) كل منتج يظهر مرة واحدة فقط في التسلسل
    for i in range(n):
        prob += pulp.lpSum([X[i, k] for k in range(n)]) == 1

    # ب) كل موقع في التسلسل يحتوي على منتج واحد فقط
    for k in range(n):
        prob += pulp.lpSum([X[i, k] for i in range(n)]) == 1

    # ج) ربط متغيرات التتابع W بالمتغيرات X
    for k in range(n - 1):
        for i in range(n):
            for i2 in range(n):
                prob += W[i, i2, k] >= X[i, k] + X[i2, k + 1] - 1

    # د) بداية العمل الأول على الآلة الأولى تساوي 0
    prob += S[0, 0] == 0

    # هـ) الانتقال بين المنتجات على نفس الآلة (مع مراعاة زمن التجهيز Ts وعطل/عدم التوافق Incompatibilite)
    for k in range(n - 1):
        for j in range(m):
            proc_k = pulp.lpSum([X[i, k] * P[i, j] for i in range(n)])
            setup_k = pulp.lpSum([W[i, i2, k] * Y[i, i2] * ts[i, i2] for i in range(n) for i2 in range(n)])
            prob += S[k + 1, j] >= S[k, j] + proc_k + setup_k

    # و) الانتقال بين الآلات لنفس المنتج
    for k in range(n):
        for j in range(1, m):
            proc_prev_m = pulp.lpSum([X[i, k] * P[i, j - 1] for i in range(n)])
            prob += S[k, j] >= S[k, j - 1] + proc_prev_m

    # ز) حساب Cmax الكلي
    for k in range(n):
        for j in range(m):
            proc_k_j = pulp.lpSum([X[i, k] * P[i, j] for i in range(n)])
            prob += Cmax >= S[k, j] + proc_k_j

    # 5. تشغيل الحلّال مع وضع مهلة زمنية (مثلاً 20 ثانية) لتفادي تجمد Streamlit
    solver = pulp.PULP_CBC_CMD(timeLimit=20, msg=False)
    prob.solve(solver)

    # 6. استخراج التسلسل الأفضل الناتج
    sequence = []
    for k in range(n):
        for i in range(n):
            if pulp.value(X[i, k]) is not None and pulp.value(X[i, k]) > 0.5:
                sequence.append(i + 1)
                break

    # في حال لم يكتمل التسلسل بسبب انتهاء الوقت، نمرر التسلسل المكتشف أو الافتراضي
    if len(sequence) != n:
        sequence = list(range(1, n + 1))

    best_cmax = pulp.value(Cmax) if pulp.value(Cmax) is not None else 0.0
    return sequence, float(best_cmax)
