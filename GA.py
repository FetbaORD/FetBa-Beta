import streamlit as st
import numpy as np
import pandas as pd

# ==========================================================
# ================== GA FUNCTIONS AREA =====================
# ==========================================================

def computeCmax(seq, P, Incompat, Ts):
    nM = P.shape[1]
    nJ = len(seq)
    machineReadyTime = np.zeros(nM)
    jobReadyTime = np.zeros(int(np.max(seq)) + 1)
    lastJobOnM = np.zeros(nM, dtype=int)

    for jIdx in range(nJ):
        job = int(seq[jIdx])
        for m in range(nM):
            cleaningTime = 0
            if lastJobOnM[m] != 0:
                prevJob = lastJobOnM[m]
                cleaningTime = Ts[prevJob - 1, job - 1]

            startTime = max(machineReadyTime[m] + cleaningTime, jobReadyTime[job])
            endTime = startTime + P[job - 1, m]

            machineReadyTime[m] = endTime
            jobReadyTime[job] = endTime
            lastJobOnM[m] = job
    return np.max(machineReadyTime)

def tournamentSelection(pop, fitness, k):
    idx = np.random.choice(pop.shape[0], k, replace=False)
    bIdx = np.argmin(fitness[idx])
    return pop[idx[bIdx]].copy()

def orderCrossover(p1, p2):
    n = len(p1)
    pts = np.sort(np.random.choice(n, 2, replace=False))
    child1 = fillChild(p1[pts[0]:pts[1]+1], p2, pts)
    child2 = fillChild(p2[pts[0]:pts[1]+1], p1, pts)
    return child1, child2

def fillChild(sub, parent, pts):
    n = len(parent)
    child = np.zeros(n, dtype=int)
    child[pts[0]:pts[1]+1] = sub
    remaining = [item for item in parent if item not in sub]
    all_idx = list(range(pts[1]+1, n)) + list(range(0, pts[0]))
    for i, idx in enumerate(all_idx):
        child[idx] = remaining[i]
    return child

def smartSwapMutation(seq, pm, P, Incompat, Ts):
    mutated = seq.copy()
    if np.random.rand() < pm:
        nJ = len(seq)
        maxTsVal = -1
        targetIdx = np.random.randint(0, nJ)
        for jIdx in range(1, nJ):
            currJob = int(seq[jIdx])
            prevJob = int(seq[jIdx-1])
            if Incompat[prevJob - 1, currJob - 1] == 1:
                currentCleaning = Ts[prevJob - 1, currJob - 1]
                if currentCleaning > maxTsVal:
                    maxTsVal = currentCleaning
                    targetIdx = jIdx
        if targetIdx > 0:
            swapIdx = targetIdx - 1
            mutated[swapIdx], mutated[targetIdx] = mutated[targetIdx], mutated[swapIdx]
    return mutated

# ==========================================================
# ================= MAIN INTERACTION FUNCTION =============
# ==========================================================

def run_ga_interface():
    """هذه الدالة ترسم الإعدادات وتشغل الخوارزمية وتحدث الجلسة"""
    if st.button("GA", type="primary") or st.session_state.get("ga_active", False):
        st.session_state.ga_active = True
        
        st.markdown("#### ⚙️ إعدادات الخوارزمية الجينية (GA)")
        
        # عناصر التحكم بالإعدادات
        popSize = st.number_input("حجم المجتمع (popSize)", 10, 500, 50, key="ga_pop")
        nGen = st.number_input("عدد الأجيال (nGen)", 10, 1000, 100, key="ga_gen")
        pc = st.slider("احتمالية العبور (pc)", 0.0, 1.0, 0.85, key="ga_pc")
        pm = st.slider("احتمالية الطفرة (pm)", 0.0, 1.0, 0.055, key="ga_pm")
        
        if st.button("تأكيد وتشغيل الخوارزمية", icon=":material/hub:", type="secondary", use_container_width=True):
            # سحب المصفوفات حية من الجلسة
            GA_Ts = st.session_state.Ts.values
            GA_P = st.session_state.Pij.values
            GA_Incompat = st.session_state.Incompatibilite.values
            current_nJobs = GA_P.shape[0]
            
            st.info("🧬 جاري تشغيل خوارزمية الجينات للجدولة المثالية...")
            
            # توليد المجتمع الابتدائي
            population = np.zeros((int(popSize), current_nJobs), dtype=int)
            for i in range(int(popSize)):
                population[i, :] = np.random.permutation(current_nJobs) + 1

            bestOverallCmax = float('inf')
            bestOverallSeq = []

            # حلقة الأجيال
            for gen in range(int(nGen)):
                fitness = np.zeros(int(popSize))
                for i in range(int(popSize)):
                    fitness[i] = computeCmax(population[i, :], GA_P, GA_Incompat, GA_Ts)

                minIdx = np.argmin(fitness)
                if fitness[minIdx] < bestOverallCmax:
                    bestOverallCmax = fitness[minIdx]
                    bestOverallSeq = population[minIdx, :].copy()

                newPop = np.zeros((int(popSize), current_nJobs), dtype=int)
                newPop[0, :] = bestOverallSeq

                for i in range(1, int(popSize), 2):
                    parent1 = tournamentSelection(population, fitness, 3)
                    parent2 = tournamentSelection(population, fitness, 3)
                    
                    if np.random.rand() < pc:
                        child1, child2 = orderCrossover(parent1, parent2)
                    else:
                        child1 = parent1.copy()
                        child2 = parent2.copy()

                    child1 = smartSwapMutation(child1, pm, GA_P, GA_Incompat, GA_Ts)
                    child2 = smartSwapMutation(child2, pm, GA_P, GA_Incompat, GA_Ts)

                    newPop[i, :] = child1
                    if i + 1 < int(popSize):
                        newPop[i + 1, :] = child2

                population = newPop.copy()

            # تحديث النتيجة في الجلسة الرئيسية لإعادة الرسم
            final_sequence = list(bestOverallSeq)
            st.session_state.sequence = final_sequence
            st.session_state.sequence_df = pd.DataFrame(
                [final_sequence], 
                columns=[f"J{idx+1}" for idx in range(current_nJobs)]
            )
            
            st.session_state.ga_active = False
            st.success(f"🏆 تم التحديث بنجاح! قيمة Makespan المثالية: {int(bestOverallCmax)}")
            st.rerun()
