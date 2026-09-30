import numpy as np
from docplex.mp.model import Model


def _to_array(data, dtype=float):
    if hasattr(data, "to_numpy"):
        return np.asarray(data.to_numpy(), dtype=dtype)
    return np.asarray(data, dtype=dtype)


def solve_algorithm5_cplex(Pij, Ts, Incompatibilite, time_limit=60):
    """
    Résout le modèle de Flow Shop avec CPLEX (docplex).
    
    Parameters:
    -----------
    Pij : array-like (n, m)
        Matrix of processing times.
    Ts : array-like (n, n)
        Matrix of sequence-dependent setup times.
    Incompatibilite : array-like (n, n)
        Binary matrix for lot incompatibility (1 if incompatible, 0 otherwise).
    time_limit : int
        Time limit in seconds for CPLEX solver.
        
    Returns:
    --------
    sequence_1_based : list
        The optimal sequence of jobs (1-indexed).
    best_cmax : float
        The minimum makespan (Cmax).
    """
    P = _to_array(Pij, float)
    ts = _to_array(Ts, float)
    Y = _to_array(Incompatibilite, float)

    n, m = P.shape

    # التحقق من أبعاد المصفوفات
    if ts.shape != (n, n) or Y.shape != (n, n):
        raise ValueError(f"أبعاد المصفوفات غير متطابقة. يجب أن تكون Ts و Incompatibilite من حجم ({n}, {n}).")

    # 1. إنشاء نموذج CPLEX
    mdl = Model(name="FlowShop_Scheduling")
    mdl.time_limit = time_limit  # تحديد مهلة زمنية بالثواني

    # 2. تعريف المتغيرات
    # X[i, k] = 1 إذا وُضع المهمة i في الموقع k
    X = mdl.binary_var_matrix(n, n, name="X")

    # W[i, i2, k] = 1 إذا تم تنفيذ المهمة i ثم i2 في الموقين k و k+1
    W = mdl.binary_var_cube(n, n, range(n - 1), name="W")

    # S[k, j] : وقت بدء تشغيل الموقع k على الماكينة j
    S = mdl.continuous_var_matrix(n, m, lb=0.0, name="S")

    # Cmax : زمن الإنجاز الكلي (Makespan)
    cmax = mdl.continuous_var(lb=0.0, name="Cmax")

    # 3. صياغة دالة الهدف (تقليل Cmax)
    mdl.minimize(cmax)

    # 4. إضافة القيود (Constraints)

    # القيد 1: كل مهمة تُوضع في موقع واحد فقط
    for i in range(n):
        mdl.add_constraint(mdl.sum(X[i, k] for k in range(n)) == 1, ctname=f"job_{i}_once")

    # القيد 2: كل موقع يحتوي على مهمة واحدة فقط
    for k in range(n):
        mdl.add_constraint(mdl.sum(X[i, k] for i in range(n)) == 1, ctname=f"pos_{k}_once")

    # القيد 3: ربط متغيرات التتابع W بالمتغيرات X
    for i in range(n):
        for i2 in range(n):
            for k in range(n - 1):
                mdl.add_constraint(W[i, i2, k] >= X[i, k] + X[i2, k + 1] - 1, ctname=f"link_W_{i}_{i2}_{k}")

    # القيد 4: بداية الموقع الأول على الماكينة الأولى تساوي 0
    mdl.add_constraint(S[0, 0] == 0, ctname="start_0_0")

    # القيد 5: الانتقال بين المواقع على نفس الماكينة (يشمل وقت المعالجة والإعداد)
    for k in range(n - 1):
        for j in range(m):
            proc_time = mdl.sum(P[i, j] * X[i, k] for i in range(n))
            setup_time = mdl.sum(Y[i, i2] * ts[i, i2] * W[i, i2, k] for i in range(n) for i2 in range(n))
            mdl.add_constraint(S[k + 1, j] >= S[k, j] + proc_time + setup_time, ctname=f"seq_mach_{k}_{j}")

    # القيد 6: الانتقال بين الماكينات لنفس الموقع
    for k in range(n):
        for j in range(1, m):
            proc_time_prev = mdl.sum(P[i, j - 1] * X[i, k] for i in range(n))
            mdl.add_constraint(S[k, j] >= S[k, j - 1] + proc_time_prev, ctname=f"seq_job_{k}_{j}")

    # القيد 7: تحديد Cmax بناءً على وقت انتهاء الموقع الأخيرة على كل الماكينات
    for k in range(n):
        for j in range(m):
            proc_time = mdl.sum(P[i, j] * X[i, k] for i in range(n))
            mdl.add_constraint(cmax >= S[k, j] + proc_time, ctname=f"cmax_bound_{k}_{j}")

    # 5. تشغيل المنظم (Solve)
    solution = mdl.solve(log_output=True)

    if solution is None:
        raise RuntimeError("لم يستطع CPLEX إيجاد حل مقبول ضمن القيود والوقت المتاح.")

    # 6. استخراج التتابع الناجح (Sequence)
    sequence = []
    for k in range(n):
        for i in range(n):
            if solution.get_value(X[i, k]) > 0.5:
                sequence.append(i + 1)  # 1-indexed
                break

    best_cmax = solution.get_value(cmax)
    return sequence, best_cmax


# ==========================================
# تجربة الكود على حالة 10x5
# ==========================================
if __name__ == "__main__":
    np.random.seed(42)

    n_jobs = 10
    n_machines = 5

    # توليد بيانات اختبارية
    Pij = np.random.randint(10, 50, size=(n_jobs, n_machines))
    Ts = np.random.randint(1, 10, size=(n_jobs, n_jobs))
    np.fill_diagonal(Ts, 0)
    Incompatibilite = np.random.randint(0, 2, size=(n_jobs, n_jobs))
    np.fill_diagonal(Incompatibilite, 0)

    print(f"--- جاري حل حالة {n_jobs}x{n_machines} باستخدام CPLEX ---")
    try:
        seq, cmax_val = solve_algorithm5_cplex(Pij, Ts, Incompatibilite, time_limit=30)
        print("\n" + "=" * 40)
        print(f"التسلسل الناتح (Sequence): {seq}")
        print(f"أفضل قيمة لـ Cmax: {cmax_val}")
        print("=" * 40)
    except Exception as e:
        print(f"حدث خطأ أثناء الحل: {e}")
