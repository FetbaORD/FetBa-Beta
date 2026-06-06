import numpy as np
import pandas as pd
import streamlit as st

# استيراد دالة run_g_neh_s_interface للحصول على السلسلة المهيأة (المولدة بـ G-NEH-S)
from G_NEH_S import run_g_neh_s_interface


def run_ga_g_neh_s_interface(P_df, Ts_df, Incompat_df, popSize=100, nGen=200, pc=0.85, pm=0.06):
    """تنفيذ الخوارزمية الهجينة (GA + G-NEH-S) حيث يتم استخدام G-NEH-S لتهيئة الجيل الأول"""

    # 1. استخراج المصفوفات كـ Numpy Arrays
    P = P_df.values
    Ts = Ts_df.values
    Incompat = Incompat_df.values

    nJobs, nMachines = P.shape

    # 2. إعدادات الخوارزمية الجينية (Parameters)
    popSize = 40  # تم تكييفها لتناسب سرعة الاستجابة في الويب
    nGen = 100
    pc = 0.85
    pm = 0.06

    # 3. خطوة التهيئة المهجنة (G-NEH-S Initialization)
    # الحصول على السلسلة المحسنة من G-NEH-S
    optimized_neh_seq, _ = run_g_neh_s_interface(P_df, Ts_df, Incompat_df)

    population = np.zeros((popSize, nJobs), dtype=int)

    # وضع السلسلة الناتجة من G-NEH-S كأول فرد في المجتمع (Index 0)
    population[0, :] = np.array(optimized_neh_seq)

    # توليد بقية الأفراد (من 1 إلى popSize) عبر طفرات عشوائية من سلسلة G-NEH-S أو عشوائياً بالكامل لضمان التنوع
    for i in range(1, popSize):
        population[i, :] = np.random.permutation(nJobs) + 1  # 1-based indexing

    bestOverallCmax = float("inf")
    bestOverallSeq = []

    # 4. حلقة الأجيال (Genetic Algorithm Loop)
    for gen in range(nGen):
        fitness = np.zeros(popSize)

        for i in range(popSize):
            fitness[i] = computeCmax_local(population[i, :], P, Incompat, Ts)

        # البحث عن أفضل حل في الجيل الحالي
        minIdx = np.argmin(fitness)
        if fitness[minIdx] < bestOverallCmax:
            bestOverallCmax = fitness[minIdx]
            bestOverallSeq = population[minIdx, :].copy()

        # بناء الجيل الجديد
        newPop = np.zeros_like(population)
        newPop[0, :] = bestOverallSeq  # الاحتفاظ بالنخبة (Elitist)

        for i in range(1, popSize, 2):
            parent1 = tournamentSelection_local(population, fitness, 3)
            parent2 = tournamentSelection_local(population, fitness, 3)

            if np.random.rand() < pc:
                child1, child2 = orderCrossover_local(parent1, parent2)
            else:
                child1, child2 = parent1.copy(), parent2.copy()

            child1 = smartSwapMutation_local(child1, pm, P, Incompat, Ts)
            child2 = smartSwapMutation_local(child2, pm, P, Incompat, Ts)

            newPop[i, :] = child1
            if i + 1 < popSize:
                newPop[i + 1, :] = child2

        population = newPop

    return list(bestOverallSeq), int(bestOverallCmax)


# ==========================================================
#                      FUNCTIONS AREA
# ==========================================================


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

            startTime = max(
                machineReadyTime[m] + cleaningTime, jobReadyTime[job]
            )
            endTime = startTime + P[job - 1, m]

            machineReadyTime[m] = endTime
            jobReadyTime[job] = endTime
            lastJobOnM[m] = job
    return np.max(machineReadyTime)


def tournamentSelection_local(pop, fitness, k):
    idx = np.random.choice(pop.shape[0], k, replace=False)
    bIdx = np.argmin(fitness[idx])
    return pop[idx[bIdx]].copy()


def orderCrossover_local(p1, p2):
    n = len(p1)
    pts = np.sort(np.random.choice(n, 2, replace=False))
    child1 = fillChild_local(p1[pts[0] : pts[1] + 1], p2, pts)
    child2 = fillChild_local(p2[pts[0] : pts[1] + 1], p1, pts)
    return child1, child2


def fillChild_local(sub, parent, pts):
    n = len(parent)
    child = np.zeros(n, dtype=int)
    child[pts[0] : pts[1] + 1] = sub
    remaining = [item for item in parent if item not in sub]
    all_idx = list(range(pts[1] + 1, n)) + list(range(0, pts[0]))
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
            prevJob = int(seq[jIdx - 1])
            if Incompat[prevJob - 1, currJob - 1] == 1:
                currentCleaning = Ts[prevJob - 1, currJob - 1]
                if currentCleaning > maxTsVal:
                    maxTsVal = currentCleaning
                    targetIdx = jIdx
        if targetIdx > 0:
            swapIdx = targetIdx - 1
            mutated[swapIdx], mutated[targetIdx] = (
                mutated[targetIdx],
                mutated[swapIdx],
            )
    return mutated
