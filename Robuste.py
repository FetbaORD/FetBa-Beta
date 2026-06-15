import streamlit as st
import numpy as np
import pandas as pd
import threading

def fun_compute_flowshop(seq, P, Ts, n, m):
    comp_times = np.zeros((n, m))
    for j in range(m):
        for i in range(n):
            task = int(seq[i]) - 1
            p_time = P[task, j]
            st_time = 0
            if i > 0:
                prev_task = int(seq[i-1]) - 1
                st_time = Ts[prev_task, task]
            if i == 0 and j == 0:
                comp_times[i, j] = p_time
            elif i == 0:
                comp_times[i, j] = comp_times[i, j-1] + p_time
            elif j == 0:
                comp_times[i, j] = comp_times[i-1, j] + st_time + p_time
            else:
                comp_times[i, j] = max(comp_times[i-1, j] + st_time, comp_times[i, j-1]) + p_time
    return comp_times[n-1, m-1]

def fun_compute_flowshop_with_breakdown(seq, P, Ts, n, m, breakdown_map):
    comp_times = np.zeros((n, m))
    for j in range(m):
        machine_breakdowns = [b for b in breakdown_map if int(b[0]) == j]
        for i in range(n):
            task = int(seq[i]) - 1
            p_time = P[task, j]
            st_time = 0
            if i > 0:
                prev_task = int(seq[i-1]) - 1
                st_time = Ts[prev_task, task]
            if i == 0 and j == 0:
                start_time = 0
            elif i == 0:
                start_time = comp_times[i, j-1]
            elif j == 0:
                start_time = comp_times[i-1, j] + st_time
            else:
                start_time = max(comp_times[i-1, j] + st_time, comp_times[i, j-1])
            finish_time = start_time + p_time
            for b in machine_breakdowns:
                if b[1] < finish_time and (b[1] + b[2]) > start_time:
                    finish_time += b[2]
            comp_times[i, j] = finish_time
    return comp_times[n-1, m-1]

def robust_ga_worker(P, Ts, n, m, pop_size, generations, crossover_rate, mutation_rate, tournament_size, lambda_val, num_scenarios, state_holder):
    """الدالة التي تعمل في الخلفية لحساب الخوارزمية بدون انقطاع"""
    try:
        total_solutions = pop_size * generations
        All_seq = np.zeros((total_solutions, n), dtype=int)
        All_fr = np.zeros(total_solutions)
        
        population = np.zeros((pop_size, n), dtype=int)
        for i in range(pop_size):
            population[i, :] = np.random.permutation(n) + 1

        counter = 0
        for g in range(generations):
            fr_pop = np.zeros(pop_size)
            for i in range(pop_size):
                seq = population[i, :]
                Cmax_I = fun_compute_flowshop(seq, P, Ts, n, m)
                perturbed_cmax = np.zeros(num_scenarios)
                
                for k in range(num_scenarios):
                    P_pert = P.copy()
                    num_faulty_cols = np.random.randint(1, m + 1)
                    faulty_cols = np.random.choice(m, num_faulty_cols, replace=False)
                    for col_idx in faulty_cols:
                        ratio_p = (0.02 + 0.23 * np.random.rand()) if np.random.rand() < 0.75 else (-0.01 - 0.04 * np.random.rand())
                        P_pert[:, col_idx] *= (1 + ratio_p)
                
                    Ts_pert = Ts.copy()
                    max_changes = int(np.floor(0.30 * n * n))
                    for _ in range(max_changes):
                        r, c = np.random.randint(0, n), np.random.randint(0, n)
                        if r != c:
                            ratio_Ts = (0.01 + 0.25 * np.random.rand()) if np.random.rand() < 0.75 else (-0.01 - 0.06 * np.random.rand())
                            Ts_pert[r, c] *= (1 + ratio_Ts)
                            Ts_pert[c, r] = Ts_pert[r, c]
                            
                    num_faulty_machines = max(1, int(np.round((0.02 + 0.33 * np.random.rand()) * m)))
                    faulty_machines = np.random.choice(m, num_faulty_machines, replace=False)
                    breakdown_map = []
                    for machine_idx in faulty_machines:
                        start_time = np.random.rand() * np.sum(P[:, machine_idx])
                        duration = 1 + 199 * np.random.rand()
                        breakdown_map.append([machine_idx, start_time, duration])
                    
                    perturbed_cmax[k] = fun_compute_flowshop_with_breakdown(seq, P_pert, Ts_pert, n, m, breakdown_map)
                
                robust = np.sqrt(np.mean((perturbed_cmax - Cmax_I) ** 2))
                fr = lambda_val * Cmax_I + (1 - lambda_val) * robust
                fr_pop[i] = fr
                All_seq[counter, :] = seq
                All_fr[counter] = fr
                counter += 1
                
            num_parents = int(np.round(pop_size / 2))
            parents = np.zeros((num_parents, n), dtype=int)
            for p in range(num_parents):
                candidates = np.random.choice(pop_size, tournament_size, replace=False)
                best_idx = candidates[np.argmin(fr_pop[candidates])]
                parents[p, :] = population[best_idx, :]
                
            children = np.zeros((int(pop_size / 2), n), dtype=int)
            c = 0
            while c < int(pop_size / 2):
                p1 = parents[np.random.randint(num_parents), :]
                p2 = parents[np.random.randint(num_parents), :]
                if np.random.rand() < crossover_rate:
                    cut = np.random.randint(1, n)
                    p1_cut = p1[:cut]
                    p2_remain = [item for item in p2 if item not in p1_cut]
                    child = np.concatenate([p1_cut, p2_remain])
                else:
                    child = p1.copy()
                children[c, :] = child
                c += 1
                
            for i in range(children.shape[0]):
                if np.random.rand() < mutation_rate:
                    pos = np.random.choice(n, 2, replace=False)
                    children[i, pos[0]], children[i, pos[1]] = children[i, pos[1]], children[i, pos[0]]
                    
            population = np.vstack([parents, children])
            
            # تحديث نسبة التقدم في مخزن آمن خارجي وثابت
            state_holder["progress"] = (g + 1) / generations

        _, unique_indices = np.unique(All_seq[:counter], axis=0, return_index=True)
        unique_seq = All_seq[unique_indices]
        unique_fr = All_fr[unique_indices]
        sorted_idx = np.argsort(unique_fr)
        
        if len(sorted_idx) > 0:
            state_holder["result_seq"] = list(unique_seq[sorted_idx[0]])
            state_holder["result_fr"] = unique_fr[sorted_idx[0]]
            state_holder["status"] = "FINISHED"
        else:
            state_holder["status"] = "ERROR"
    except Exception as e:
        state_holder["status"] = f"ERROR: {str(e)}"

def run_robust_ga_interface(P_df, Ts_df, Incompat_df):
    st.markdown("#### ⚙️ إعدادات الخوارزمية الجينية المتينة (Robust GA)")
    
    if "rob_pop_size" not in st.session_state: st.session_state.rob_pop_size = 20
    if "rob_generations" not in st.session_state: st.session_state.rob_generations = 10
    if "rob_mutation" not in st.session_state: st.session_state.rob_mutation = 0.05
    if "rob_crossover" not in st.session_state: st.session_state.rob_crossover = 0.80
    if "rob_tournament" not in st.session_state: st.session_state.rob_tournament = 3
    if "rob_lambda" not in st.session_state: st.session_state.rob_lambda = 0.5
    if "rob_scenarios" not in st.session_state: st.session_state.rob_scenarios = 4
    
    # تهيئة قاموس تتبع الخيط الخلفي في جلسة Streamlit
    if "robust_worker_state" not in st.session_state:
        st.session_state.robust_worker_state = {"status": "IDLE", "progress": 0.0, "result_seq": None, "result_fr": None}

    pop_size = st.number_input("حجم المجتمع (Population Size)", 4, 200, key="rob_pop_size", step=2)
    generations = st.number_input("عدد الأجيال (Generations)", 1, 500, key="rob_generations", step=5)
    crossover_rate = st.slider("معدل العبور (Crossover Rate)", 0.0, 1.0, key="rob_crossover", step=0.05)
    mutation_rate = st.slider("معدل الطفرة (Mutation Rate)", 0.0, 1.0, key="rob_mutation", step=0.01)
    tournament_size = st.slider("حجم البطولة (Tournament Size)", 2, 10, key="rob_tournament")
    lambda_val = st.slider("معامل الأهمية (Lambda)", 0.0, 1.0, key="rob_lambda", step=0.1)
    num_scenarios = st.slider("عدد السيناريوهات المضطربة للمحاكاة", 2, 30, key="rob_scenarios")

    current_status = st.session_state.robust_worker_state["status"]

    if current_status == "IDLE":
        if st.button("🚀 تشغيل الحساب المتين في الخلفية", type="secondary", key="execute_robust_ga_btn"):
            st.session_state.robust_worker_state = {"status": "RUNNING", "progress": 0.0, "result_seq": None, "result_fr": None}
            
            P = P_df.values.astype(float)
            Ts = Ts_df.values.astype(float)
            n, m = P.shape
            
            # إطلاق خيط المعالجة الخلفي المستقل عن الـ Autorefresh
            t = threading.Thread(
                target=robust_ga_worker,
                args=(P, Ts, n, m, pop_size, generations, crossover_rate, mutation_rate, tournament_size, lambda_val, num_scenarios, st.session_state.robust_worker_state)
            )
            t.start()
            st.rerun()

    elif current_status == "RUNNING":
        st.info("⏳ الخوارزمية تعمل الآن في الخلفية... المخططات والعدادات بالصفحة تتحدث طبيعياً.")
        # عرض شريط تقدم حقيقي يقرأ من الخلفية كل ثانيتين مع الـ refresh
        prog_val = st.session_state.robust_worker_state["progress"]
        st.progress(prog_val)
        st.caption(f"نسبة اكتمال البحث المتين: {prog_val * 100:.1f}%")

    elif current_status == "FINISHED":
        # عند اكتمال الحساب بنجاح، يتم تمرير النتيجة للـ session_state الأساسي
        st.session_state.optimized_robust_seq = st.session_state.robust_worker_state["result_seq"]
        st.session_state.robust_worker_state["status"] = "IDLE" # إعادة تصفير الحالة للمرة القادمة
        st.rerun()

    elif "ERROR" in current_status:
        st.error(f"❌ حدث خطأ أثناء الحساب: {current_status}")
        if st.button("إعادة محاولة"):
            st.session_state.robust_worker_state["status"] = "IDLE"
            st.rerun()
