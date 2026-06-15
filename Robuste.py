import streamlit as st
import numpy as np
import pandas as pd

def fun_compute_flowshop(seq, P, Ts, n, m):
    """حساب وقت الإتمام الأقصى (Cmax) بدون أعطال (0-indexed)"""
    comp_times = np.zeros((n, m))
    for j in range(m):
        for i in range(n):
            task = int(seq[i]) - 1  # تحويل التسلسل من 1-based إلى 0-based
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
                ready_on_machine = comp_times[i-1, j] + st_time
                ready_from_prev_mic = comp_times[i, j-1]
                comp_times[i, j] = max(ready_on_machine, ready_from_prev_mic) + p_time
                
    return comp_times[n-1, m-1]


def fun_compute_flowshop_with_breakdown(seq, P, Ts, n, m, breakdown_map):
    """حساب وقت الإتمام الأقصى (Cmax) مع الأخذ في الاعتبار الأعطال المفاجئة"""
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
                b_start = b[1]
                b_dur = b[2]
                if b_start < finish_time and (b_start + b_dur) > start_time:
                    finish_time += b_dur
                    
            comp_times[i, j] = finish_time
            
    return comp_times[n-1, m-1]


def run_robust_ga_interface(P_df, Ts_df, Incompat_df):
    """دالة الواجهة وتشغيل الخوارزمية المتينة"""
    st.markdown("#### ⚙️ إعدادات الخوارزمية الجينية المتينة (Robust GA)")
    
    # تهيئة متغيرات الحالة لمنع التصفير عند التحديث التلقائي
    if "rob_pop_size" not in st.session_state: st.session_state.rob_pop_size = 20
    if "rob_generations" not in st.session_state: st.session_state.rob_generations = 10
    if "rob_mutation" not in st.session_state: st.session_state.rob_mutation = 0.05
    if "rob_crossover" not in st.session_state: st.session_state.rob_crossover = 0.80
    if "rob_tournament" not in st.session_state: st.session_state.rob_tournament = 3
    if "rob_lambda" not in st.session_state: st.session_state.rob_lambda = 0.5
    if "rob_scenarios" not in st.session_state: st.session_state.rob_scenarios = 4

    # عناصر واجهة المستخدم لإدخال الإعدادات
    pop_size = st.number_input("Population Size", 4, 200, key="rob_pop_size", step=2)
    generations = st.number_input("N de Generations", 1, 500, key="rob_generations", step=5)
    crossover_rate = st.slider("Crossover Rate", 0.0, 1.0, key="rob_crossover", step=0.05)
    mutation_rate = st.slider("Mutation Rate", 0.0, 1.0, key="rob_mutation", step=0.01)
    tournament_size = st.slider("Tournament Size", 2, 10, key="rob_tournament")
    lambda_val = st.slider("Lambda ", 0.0, 1.0, key="rob_lambda", step=0.1)
    num_scenarios = st.slider("N des Senarios", 2, 30, key="rob_scenarios")

    if st.button("Run Algorithm", type="secondary", key="execute_robust_ga_btn"):
        P = P_df.values.astype(float)
        Ts = Ts_df.values.astype(float)
        n, m = P.shape

        total_solutions = pop_size * generations
        All_seq = np.zeros((total_solutions, n), dtype=int)
        All_fr = np.zeros(total_solutions)
        
        # تهيئة المجتمع الأولي (التسلسلات تبدأ من 1 لتتوافق مع نظام العرض لديك)
        population = np.zeros((pop_size, n), dtype=int)
        for i in range(pop_size):
            population[i, :] = np.random.permutation(n) + 1

        counter = 0
        progress_bar = st.progress(0.0)
        
        for g in range(generations):
            fr_pop = np.zeros(pop_size)
            
            for i in range(pop_size):
                seq = population[i, :]
                Cmax_I = fun_compute_flowshop(seq, P, Ts, n, m)
                perturbed_cmax = np.zeros(num_scenarios)
                
                for k in range(num_scenarios):
                    # 1. اضطراب أوقات المعالجة
                    P_pert = P.copy()
                    num_faulty_cols = np.random.randint(1, m + 1)
                    faulty_cols = np.random.choice(m, num_faulty_cols, replace=False)
                    for col_idx in faulty_cols:
                        ratio_p = (0.02 + 0.23 * np.random.rand()) if np.random.rand() < 0.75 else (-0.01 - 0.04 * np.random.rand())
                        P_pert[:, col_idx] *= (1 + ratio_p)
                
                    # 2. اضطراب أوقات التعقيم
                    Ts_pert = Ts.copy()
                    max_changes = int(np.floor(0.30 * n * n))
                    for _ in range(max_changes):
                        r, c = np.random.randint(0, n), np.random.randint(0, n)
                        if r != c:
                            ratio_Ts = (0.01 + 0.25 * np.random.rand()) if np.random.rand() < 0.75 else (-0.01 - 0.06 * np.random.rand())
                            Ts_pert[r, c] *= (1 + ratio_Ts)
                            Ts_pert[c, r] = Ts_pert[r, c]
                            
                    # 3. دمج الأعطال (Breakdowns)
                    num_faulty_machines = max(1, int(np.round((0.02 + 0.33 * np.random.rand()) * m)))
                    faulty_machines = np.random.choice(m, num_faulty_machines, replace=False)
                    breakdown_map = []
                    
                    for machine_idx in faulty_machines:
                        start_time = np.random.rand() * np.sum(P[:, machine_idx])
                        duration = 1 + 199 * np.random.rand()
                        breakdown_map.append([machine_idx, start_time, duration])
                        if np.random.rand() < 0.25:
                            breakdown_map.append([machine_idx, start_time + duration + 50, 1 + 29 * np.random.rand()])
                    
                    perturbed_cmax[k] = fun_compute_flowshop_with_breakdown(seq, P_pert, Ts_pert, n, m, breakdown_map)
                
                # الحسابات الرياضية للمتانة وقيمة الدالة الـ Robust
                robust = np.sqrt(np.mean((perturbed_cmax - Cmax_I) ** 2))
                fr = lambda_val * Cmax_I + (1 - lambda_val) * robust
                fr_pop[i] = fr
                
                All_seq[counter, :] = seq
                All_fr[counter] = fr
                counter += 1
                
            # الاختيار الطبيعي (Tournament Selection)
            num_parents = int(np.round(pop_size / 2))
            parents = np.zeros((num_parents, n), dtype=int)
            for p in range(num_parents):
                candidates = np.random.choice(pop_size, tournament_size, replace=False)
                best_idx = candidates[np.argmin(fr_pop[candidates])]
                parents[p, :] = population[best_idx, :]
                
            # التزاوج (Crossover)
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
                
            # الطفرة (Mutation)
            for i in range(children.shape[0]):
                if np.random.rand() < mutation_rate:
                    pos = np.random.choice(n, 2, replace=False)
                    children[i, pos[0]], children[i, pos[1]] = children[i, pos[1]], children[i, pos[0]]
                    
            population = np.vstack([parents, children])
            progress_bar.progress((g + 1) / generations)

        # فلترة التكرارات واستخراج أفضل الحلول
        _, unique_indices = np.unique(All_seq[:counter], axis=0, return_index=True)
        unique_seq = All_seq[unique_indices]
        unique_fr = All_fr[unique_indices]
        
        sorted_idx = np.argsort(unique_fr)
        
        if len(sorted_idx) > 0:
            best_idx = sorted_idx[0]
            optimized_seq = list(unique_seq[best_idx])
            
            # حفظ الحل الأفضل المكتشف لتحديث جدول الواجهة الرئيسية
            st.session_state.optimized_robust_seq = optimized_seq
            st.session_state.optimized_robust_fr = unique_fr[best_idx]
            st.success(f"🏆 تم العثور على أفضل تسلسل متين بنجاح! قيمة دالة الهدف: {unique_fr[best_idx]:.2f}")
            st.rerun()
        else:
            st.error("لم يتم العثور على حلول فريدة.")
