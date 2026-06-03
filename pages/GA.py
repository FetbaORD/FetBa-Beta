import streamlit as st
import numpy as np
import time

# ==========================================================
# ================== FUNCTIONS AREA ========================
# ==========================================================

def computeCmax(seq, P, Incompat, Ts):
    nM = P.shape[1]
    nJ = len(seq)

    machineReadyTime = np.zeros(nM)
    jobReadyTime = np.zeros(int(np.max(seq)) + 1) # +1 لتفادي مشكلة الـ Index في بايثون (0-indexed)
    lastJobOnM = np.zeros(nM, dtype=int)

    for jIdx in range(nJ):
        job = int(seq[jIdx])

        for m in range(nM):
            cleaningTime = 0
            if lastJobOnM[m] != 0:
                prevJob = lastJobOnM[m]
                # تعديل الـ index ليتناسب مع بايثون (طرح 1)
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

    # جلب العناصر المتبقية التي ليست في الابن الجزئي
    remaining = [item for item in parent if item not in sub]
    
    # بناء الترتيب الدائري للمؤشرات بعد نقطة القطع الثانية ثم من البداية
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
# =================== STREAMLIT INTERFACE ===================
# ==========================================================

st.set_page_config(page_title="Genetic Algorithm Optimizer", layout="centered")
st.title("🧬 خوارزمية الجينات للجدولة (Genetic Algorithm)")

st.sidebar.header("⚙️ المعاملات (Parameters)")
nJobs = st.sidebar.number_input("عدد الوظائف (nJobs)", value=20)
nMachines = st.sidebar.number_input("عدد الآلات (nMachines)", value=20)
popSize = st.sidebar.number_input("حجم المجتمع (popSize)", value=75)
nGen = st.sidebar.number_input("عدد الأجيال (nGen)", value=220)
pc = st.sidebar.slider("احتمالية العبور (pc)", 0.0, 1.0, 0.85)
pm = st.sidebar.slider("احتمالية الطفرة (pm)", 0.0, 1.0, 0.055)

st.header("📂 رفع ملفات المصفوفات (TXT)")

# رفع الملفات مباشرة من الصفحة دون استيراد محلي
ts_file = st.file_uploader("قم برفع ملف مصفوفة الأوقات الانتقالية (Ts.txt)", type=["txt"])
pij_file = st.file_uploader("قم برفع ملف مصفوفة أوقات المعالجة (Pij.txt)", type=["txt"])
incompat_file = st.file_uploader("قم برفع ملف مصفوفة عدم التوافق (Incompat.txt)", type=["txt"])

if st.button("🚀 تشغيل الخوارزمية الجينية", type="primary"):
    if ts_file and pij_file and incompat_file:
        
        # قراءة البيانات مباشرة من الملفات المرفوعة باستخدام numpy
        Ts = np.loadtxt(ts_file)
        P = np.loadtxt(pij_file)
        Incompat = np.loadtxt(incompat_file)
        
        nJobs, nMachines = P.shape
        
        st.info("جاري الحساب... يرجى الانتظار")
        start_time = time.time()
        
        # --- Initialization ---
        # توليد تبديلات عشوائية تبدأ من 1 إلى nJobs (مثل ماتلاب لتتوافق مع الدوال)
        population = np.zeros((popSize, nJobs), dtype=int)
        for i in range(popSize):
            population[i, :] = np.random.permutation(nJobs) + 1

        bestOverallCmax = float('inf')
        bestOverallSeq = []

        allSolutions = []
        allFitness = []

        # شريط تقدم تفاعلي في Streamlit
        progress_bar = st.progress(0)

        # --- Genetic Algorithm Loop ---
        for gen in range(int(nGen)):
            fitness = np.zeros(popSize)

            for i in range(popSize):
                fitness[i] = computeCmax(population[i, :], P, Incompat, Ts)

            # حفظ جميع الحلول والـ fitness
            if len(allSolutions) == 0:
                allSolutions = population.copy()
                allFitness = fitness.copy()
            else:
                allSolutions = np.vstack((allSolutions, population))
                allFitness = np.concatenate((allFitness, fitness))

            minIdx = np.argmin(fitness)
            minFit = fitness[minIdx]
            
            if minFit < bestOverallCmax:
                bestOverallCmax = minFit
                bestOverallSeq = population[minIdx, :].copy()

            newPop = np.zeros((popSize, nJobs), dtype=int)
            newPop[0, :] = bestOverallSeq

            for i in range(1, popSize, 2):
                parent1 = tournamentSelection(population, fitness, 3)
                parent2 = tournamentSelection(population, fitness, 3)
                
                if np.random.rand() < pc:
                    child1, child2 = orderCrossover(parent1, parent2)
                else:
                    child1 = parent1.copy()
                    child2 = parent2.copy()

                child1 = smartSwapMutation(child1, pm, P, Incompat, Ts)
                child2 = smartSwapMutation(child2, pm, P, Incompat, Ts)

                newPop[i, :] = child1
                if i + 1 < popSize:
                    newPop[i + 1, :] = child2

            population = newPop.copy()
            # تحديث شريط التقدم
            progress_bar.progress((gen + 1) / int(nGen))

        end_time = time.time()
        st.success(f"✨ تم الانتهاء من الحساب في {end_time - start_time:.4f} ثانية!")

        # --- GLOBAL BEST ---
        st.subheader("🏆 أفضل حل تم الوصول إليه (GLOBAL BEST)")
        st.write(f"**أفضل تتابع للوظائف (Best Sequence):** {list(bestOverallSeq)}")
        st.markdown(f"🎯 **قيمة الـ Makespan الأفضل ($C_{{max}}$):** <span style='color:green; font-size:20px; font-weight:bold;'>{int(bestOverallCmax)}</span>", unsafe_allow_html=True)

        # --- TOP 20 UNIQUE SOLUTIONS ---
        st.subheader("📊 أفضل 20 حلاً فريداً (Top 20 Unique Solutions)")
        
        sorted_indices = np.argsort(allFitness)
        sortedSolutions = allSolutions[sorted_indices]
        sortedFitness = allFitness[sorted_indices]

        # استخراج الحلول الفريدة مع الحفاظ على الترتيب (مثل unique في ماتلاب مع 'stable')
        _, unique_indices = np.unique(sortedSolutions, axis=0, return_index=True)
        unique_indices = np.sort(unique_indices) # للحفاظ على الترتيب الأصلي للتصفية
        
        uniqueSolutions = sortedSolutions[unique_indices]
        uniqueFitness = sortedFitness[unique_indices]

        # عرض النتائج في جدول أنيق داخل Streamlit
        nDisplay = min(20, len(uniqueSolutions))
        results_data = []
        for i in range(nDisplay):
            results_data.append({
                "Rank": f"#{i+1}",
                "Sequence": str(list(uniqueSolutions[i])),
                "Cmax": int(uniqueFitness[i])
            })
            
        st.table(results_data)
        
    else:
        st.error("⚠️ من فضلك قم برفع الملفات الثلاثة أولاً لتشغيل الخوارزمية.")