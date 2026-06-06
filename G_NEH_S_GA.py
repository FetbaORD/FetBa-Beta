import numpy as np
import pandas as pd
from G_NEH_S import run_g_neh_s_interface  # لاستيراد السلسلة الابتدائية الممتازة

def run_g_neh_s_ga_interface(P_df, Ts_df, Incompat_df):
    """
    الهجين بين G-NEH-S و الخوارزمية الجينية (GA)
    المستوحى من كود MATLAB الأصلي مع تخصيصه للعمل مع واجهة Streamlit حياً.
    """
    # تحويل البيانات إلى مصفوفات Numpy (0-based index للبايثون)
    P = P_df.values
    Ts = Ts_df.values
    Incompat = Incompat_df.values
    
    nJobs, nMachines = P.shape
    popSize = 20
    nGen = 200
    
    # 1. تهيئة المجتمع 
    population = np.zeros((popSize, nJobs), dtype=int)
    
    # الحصول على الحل الممتاز من G-NEH-S ليكون النواة الجينية الأولى (بديل sequences.txt)
    try:
        optimized_seq, _ = run_g_neh_s_interface(P_df, Ts_df, Incompat_df)
        # تحويل السلسلة إلى 1-based لتتوافق مع منطق حسابات بايثون الداخلية المعدلة
        g_neh_s_seq = np.array(optimized_seq, dtype=int)
        population[0, :] = g_neh_s_seq
        n_imported = 1
    except:
        n_imported = 0

    # 2. ملء باقي المجتمع عشوائياً للحفاظ على التنوع الجيني ومنع Local Optimum
    for i in range(n_imported, popSize):
        population[i, :] = np.random.permutation(nJobs) + 1 # 1-based indexing
        
    bestOverallCmax = float('inf')
    bestOverallSeq = []
    
    # دالات المساعدة المترجمة داخلياً
    def computeCmax_local(seq, P, Incompat, Ts):
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

    def tournamentSelection_local(pop, fitness, k=3):
        idx = np.random.choice(pop.shape[0], k, replace=False)
        bIdx = np.argmin(fitness[idx])
        return pop[idx[bIdx]].copy()

    def orderCrossover_local(p1, p2):
        n = len(p1)
        pts = np.sort(np.random.choice(n, 2, replace=False))
        child1 = fillChild_local(p1[pts[0]:pts[1]+1], p2, pts)
        child2 = fillChild_local(p2[pts[0]:pts[1]+1], p1, pts)
        return child1, child2

    def fillChild_local(sub, parent, pts):
        n = len(parent)
        child = np.zeros(n, dtype=int)
        child[pts[0]:pts[1]+1] = sub
        remaining = [item for item in parent if item not in sub]
        all_idx = list(range(pts[1]+1, n)) + list(range(0, pts[0]))
        for i, idx in enumerate(all_idx):
            child[idx] = remaining[i]
        return child

    def smartSwapMutation_local(seq, pm, P, Incompat, Ts):
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

    # --- حلقة الأجيال العصب الرئيسي لـ GA ---
    for gen in range(nGen):
        fitness = np.zeros(popSize)
        for i in range(popSize):
            fitness[i] = computeCmax_local(population[i, :], P, Incompat, Ts)
            
        minFit = np.min(fitness)
        minIdx = np.argmin(fitness)
        
        if minFit < bestOverallCmax:
            bestOverallCmax = minFit
            bestOverallSeq = population[minIdx, :].copy()
            
        newPop = np.zeros(population.shape, dtype=int)
        newPop[0, :] = bestOverallSeq # النخبة Elitist
        
        for i in range(1, popSize, 2):
            parent1 = tournamentSelection_local(population, fitness, 3)
            parent2 = tournamentSelection_local(population, fitness, 3)
            
            child1, child2 = orderCrossover_local(parent1, parent2)
            
            child1 = smartSwapMutation_local(child1, 0.1, P, Incompat, Ts)
            child2 = smartSwapMutation_local(child2, 0.1, P, Incompat, Ts)
            
            newPop[i, :] = child1
            if i + 1 < popSize:
                newPop[i + 1, :] = child2
                
        population = newPop

    # إرجاع السلسلة النهائية كقائمة بايثون عادية (1-based) جاهزة لـ Streamlit
    return list(bestOverallSeq), int(bestOverallCmax)