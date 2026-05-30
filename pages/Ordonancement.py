import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh
from datetime import datetime


st_autorefresh(interval=2000, key="refresh_clock")
st.set_page_config(page_title="Ordonancement de la production", layout="wide")

st.title("Ordonancement de la production")

# 🎨 استدعاء ملف الـ CSS الخارجي لتطبيق الظلال والمؤثرات الجمالية
with open("style.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if "sim_start_time" in st.session_state:

    sim_duration = (datetime.now() - st.session_state.sim_start_time).total_seconds()

    minutes = int(sim_duration // 60)
    seconds = int(sim_duration % 60)

    st.info(f"⏱️ Runtime: {minutes} min {seconds} sec")

else:
    st.warning("لم يتم تشغيل المحاكاة من الصفحة الرئيسية")





# =========================
# 1. إدخال الحجم
# =========================
st.sidebar.header("⚙️ Paramètres")

n_jobs = st.sidebar.number_input("عدد المنتجات (Jobs)", 2, 50, 5)
n_machines = st.sidebar.number_input("عدد الآلات (Machines)", 2, 10, 3)

# =========================
# 2. زر إنشاء الجداول
# =========================
if st.button("إنشاء الجداول"):

    # حفظ الحجم
    st.session_state.n_jobs = n_jobs
    st.session_state.n_machines = n_machines

    # =========================
    # 3. إنشاء Pij
    # =========================
    Pij = pd.DataFrame(
        np.random.randint(1, 99, size=(n_jobs, n_machines)),
        columns=[f"M{i+1}" for i in range(n_machines)],
        index=[f"Job {i+1}" for i in range(n_jobs)]
    )




    # =========================
    # 4. إنشاء Ts (setup matrix)
    # =========================
    Ts = pd.DataFrame(
        np.random.randint(1, 99, size=(n_jobs, n_jobs)),
        columns=[f"Job {i+1}" for i in range(n_jobs)],
        index=[f"Job {i+1}" for i in range(n_jobs)]
    )

    # =========================
    # 5. Sequence (initial)
    # =========================

    sequence = list(range(1, n_jobs + 1))
    st.session_state.sequence = sequence
    st.session_state.sequence_df = pd.DataFrame(
    [sequence],
    columns=[f"J{i+1}" for i in range(n_jobs)]
)




    # تخزين في session_state
    st.session_state.Pij = Pij
    st.session_state.Ts = Ts
    st.success("تم إنشاء الجداول بنجاح")

# =========================
# 6. عرض الجداول
# =========================


if "Pij" in st.session_state:

    st.subheader("📊 Pij (Processing Time)")
    edited_pij = st.data_editor(
        st.session_state.Pij,
        key="Pij_editor",
        use_container_width=True,
        num_rows="dynamic"
)
    st.session_state.Pij = edited_pij
    
    
if "Ts" in st.session_state:

    st.subheader("Ts (Setup / Sterilization Time)")
    edited_ts = st.data_editor(
        st.session_state.Ts,
        key="Ts_editor",
        use_container_width=True
)
    st.session_state.Ts = edited_ts


# ==========================================
# 5 & 6. Sequence (توليد وتعديل التسلسل)
# ==========================================

if "sequence_df" in st.session_state:
    st.divider() 
    
    col_title, col_btn = st.columns([3, 1])
    
    with col_title:
        st.subheader("Modifier la Séquence")
    
    with col_btn:
        # استخدام popover لإنشاء قائمة منسدلة تحتوي على الخوارزميات
        with st.popover("🔀 Choisir Algorithme"):
            st.write("Sélectionnez un Algorithme :")
            
            # إنشاء الأزرار الخمسة
            algo_choice = None
            if st.button("G-NEH-S"): algo_choice = 1
            if st.button("(GA + G-NEH-S)"): algo_choice = 2
            if st.button("Génetique Robuste"): algo_choice = 3
            if st.button("Algorithme 4"): algo_choice = 4
            if st.button("Algorithme 5"): algo_choice = 5

            if algo_choice:
                import random
                current_n_jobs = len(st.session_state.Pij)
                new_seq = list(range(1, current_n_jobs + 1))
                
                # هنا يمكنك تخصيص منطق كل خوارزمية مستقبلاً
                # حالياً جميعها تقوم بعمل Shuffle عشوائي كمثال
                random.shuffle(new_seq)
                
                # تحديث الجلسة
                st.session_state.sequence = new_seq
                st.session_state.sequence_df = pd.DataFrame(
                    [new_seq], 
                    columns=[f"J{i+1}" for i in range(current_n_jobs)]
                )
                st.success(f"C'est fait ! (Algo {algo_choice})")
                st.rerun()

    # عرض الجدول القابل للتعديل
    edited_seq = st.data_editor(
        st.session_state.sequence_df,
        key="Seq_editor",
        use_container_width=True
    )
    
    if edited_seq is not None:
        try:
            st.session_state.sequence_df = edited_seq
            st.session_state.sequence = [int(x) for x in edited_seq.values.flatten().tolist()]
        except ValueError:
            st.error("الرجاء إدخال أرقام فقط")



# =========================
# 7. حساب و عرض Gantt Chart
# =========================
if "machine_faults" not in st.session_state:
    st.session_state.machine_faults = {f"Machine {i+1}": [] for i in range(5)}

if "Pij" in st.session_state and "sequence" in st.session_state:
    st.subheader("Gantt Chart (Progressif avec gestion des pannes)")

    # استخراج البيانات من session_state
    pij_data = st.session_state.Pij.values
    ts_data = st.session_state.Ts.values
    sequence = [int(i) - 1 for i in st.session_state.sequence] # تحويل التسلسل لـ index (0-based)
    
    n_j = len(sequence)
    n_m = st.session_state.n_machines

    # مصفوفات لتخزين أوقات البدء والنهاية المعدلة
    start_times = np.zeros((n_j, n_m))
    end_times = np.zeros((n_j, n_m))

    # الحصول على الوقت الحالي للمحاكاة (ثواني)
    if "sim_start_time" in st.session_state:
        current_sim_time = (datetime.now() - st.session_state.sim_start_time).total_seconds()
    else:
        current_sim_time = 0

    # حساب الجدولة الديناميكية (Flow Shop مع إزاحة الأعطال)
    for j_idx, job_id in enumerate(sequence):
        for m in range(n_m):
            # وقت المعالجة الأصلي المطلوب
            proc_time = pij_data[job_id, m]
            
            # وقت الإعداد (Setup)
            setup_time = 0
            if j_idx > 0:
                prev_job_id = sequence[j_idx - 1]
                setup_time = ts_data[prev_job_id, job_id]

            # 1. تحديد وقت البدء المبدئي (المنطق الكلاسيكي)
            if j_idx == 0 and m == 0:
                s_t = 0
            elif j_idx == 0: 
                s_t = end_times[j_idx, m-1]
            elif m == 0: 
                s_t = end_times[j_idx-1, m] + setup_time
            else: 
                s_t = max(end_times[j_idx-1, m] + setup_time, end_times[j_idx, m-1])
            
            # 2. حـسـاب تأثير الأعطال المـتداخلة وإزاحـة الـوقـت (الجديد ومربط الفرس)
            machine_key = f"Machine {m+1}"
            if "machine_faults" in st.session_state and machine_key in st.session_state.machine_faults:
                faults = st.session_state.machine_faults[machine_key]
                
                # سنقوم بمحاكاة مرور الوقت خطوة بخطوة للعملية للتأكد من تأثرها بأي عطل يحدث أثنائها
                current_start = s_t
                remaining_proc_time = proc_time
                current_time_pointer = current_start
                
                # مصفوفة الأعطال مرتبة حسب وقت البداية
                sorted_faults = sorted(faults, key=lambda x: x["start"])
                
                for fault in sorted_faults:
                    f_start = fault["start"]
                    f_end = fault["end"] if fault["end"] is not None else current_sim_time
                    
                    # إذا حدث العطل أثناء تشغيل المهمة (أو تداخل مع وقت بدئها المتوقع)
                    # نقوم بزيادة وقت النهاية بمقدار مدة العطل
                    if f_start < current_time_pointer + remaining_proc_time and f_end > current_time_pointer:
                        # حساب الجزء من العطل الذي يقع داخل فترة تنفيذ المهمة
                        overlap_start = max(f_start, current_time_pointer)
                        overlap_end = min(f_end, current_time_pointer + remaining_proc_time)
                        
                        # مدة العطل الذي تسبب في إيقاف الآلة
                        fault_duration = f_end - f_start
                        
                        # إزاحة الوقت: المهمة ستتأخر بمقدار العطل بالكامل
                        current_time_pointer += fault_duration

                # وقت البدء النهائي ووقت النهاية بعد حساب تأخيرات الأعطال
                start_times[j_idx, m] = current_start
                end_times[j_idx, m] = current_time_pointer + remaining_proc_time
            else:
                # إذا لم يكن هناك أعطال للآلة، الحساب طبيعي
                start_times[j_idx, m] = s_t
                end_times[j_idx, m] = s_t + proc_time


    # تجهيز بيانات الرسم لـ Plotly
    gantt_data = []
    for j_idx, job_id in enumerate(sequence):
        for m in range(n_m):
            if start_times[j_idx, m] <= current_sim_time:
                display_end = min(end_times[j_idx, m], current_sim_time)
                
                # إضافة المهمة العادية
                gantt_data.append(dict(
                    Task=f"Machine {m+1}",
                    Start=start_times[j_idx, m],
                    Finish=display_end,
                    Resource=f"Job {job_id + 1}"
                ))

    # إضافة فترات الأعطال كمربعات حمراء واضحة في المخطط لتبين سبب الفجوة الزمنية
    if "machine_faults" in st.session_state:
        for machine_name, faults in st.session_state.machine_faults.items():
            try:
                m_num = int(machine_name.split()[-1])
                if m_num <= n_m: 
                    for fault in faults:
                        f_start = fault["start"]
                        f_end = fault["end"] if fault["end"] is not None else current_sim_time
                        
                        if f_start <= current_sim_time:
                            gantt_data.append(dict(
                                Task=f"Machine {m_num}",
                                Start=f_start,
                                Finish=min(f_end, current_sim_time),
                                Resource="⚠️ عطل الآلة (Breakdown)"
                            ))
            except:
                pass

    if gantt_data:
        df_gantt = pd.DataFrame(gantt_data)
        
        # تحويل الثواني إلى تواريخ وهمية لـ Plotly
        df_gantt['Start'] = pd.to_datetime(df_gantt['Start'], unit='s')
        df_gantt['Finish'] = pd.to_datetime(df_gantt['Finish'], unit='s')

        # تخصيص الألوان (الوظائف ألوان عشوائية، والعطل أحمر دائماً)
        color_discrete_map = {" عطل الآلة (Breakdown)": "#ff0000"}

        fig = px.timeline(
            df_gantt, 
            x_start="Start", 
            x_end="Finish", 
            y="Task", 
            color="Resource",
            color_discrete_map=color_discrete_map,
            title="التنفيذ الديناميكي المباشر (تأثير الأعطال وتأخير المهام)"
        )
        
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(xaxis_title="الزمن (ثواني)", showlegend=True)
        fig.update_layout(xaxis=dict(tickformat="%M:%S"))
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("بانتظار بدء المحاكاة أو وصول الوقت للوظيفة الأولى...")




# ==========================================
# 🎯 الجزء المصحح والمطور: حساب وعرض الكامل والثابت باستخدام Plotly السريعة والمستقرة
# ==========================================
st.write("")

# 1. تهيئة متغير الحالة في الجلسة إذا لم يكن موجوداً
if "show_complete_gantt" not in st.session_state:
    st.session_state.show_complete_gantt = False

# 2. أزرار التحكم بالعرض في سطر أنيق ومتباعد
col_gantt_btn1, col_gantt_btn2 = st.columns([1, 1], gap="large")

with col_gantt_btn1:
    if st.button("Afficher Gantt Complete", type="primary"):
        st.session_state.show_complete_gantt = True

with col_gantt_btn2:
    if st.session_state.show_complete_gantt:
        if st.button("Masquer le Diagramme"):
            st.session_state.show_complete_gantt = False
            st.rerun()

# 3. إذا كانت الحالة True، يتم رسم المخطط الكامل فوراً
if st.session_state.show_complete_gantt:
    
    # دالة حساب الجدولة الكاملة الثابتة (بدون اقتطاع الوقت الحالي)
    def solve_flow_shop_static_plotly(pij, ts, job_sequence):
        n_jobs, m_machines = pij.shape
        st_times = np.zeros((n_jobs, m_machines))
        en_times = np.zeros((n_jobs, m_machines))
        machine_free_time = np.zeros(m_machines)
        
        for i, job_idx in enumerate(job_sequence):
            for m in range(m_machines):
                p_time = pij[job_idx, m]
                setup_time = 0
                if i > 0:
                    prev_job_idx = job_sequence[i-1]
                    setup_time = ts[prev_job_idx, job_idx]
                
                ready_after_setup = machine_free_time[m] + setup_time
                
                if m == 0:
                    st_times[job_idx, m] = ready_after_setup
                else:
                    st_times[job_idx, m] = max(ready_after_setup, en_times[job_idx, m-1])
                
                en_times[job_idx, m] = st_times[job_idx, m] + p_time
                machine_free_time[m] = en_times[job_idx, m]

        return st_times, en_times, n_jobs, m_machines

    # جلب البيانات الحية وتمريرها للحساب
    static_pij = st.session_state.Pij.values
    static_ts = st.session_state.Ts.values
    static_seq = [int(x) - 1 for x in st.session_state.sequence]
    
    s_times, e_times, nj, nm = solve_flow_shop_static_plotly(static_pij, static_ts, static_seq)
    
    # بناء مصفوفة البيانات الرسمية لـ Plotly
    static_gantt_data = []
    
    for i, job_idx in enumerate(static_seq):
        for m in range(nm):
            # 1. إضافة وقت الإعداد (Setup Time)
            if i > 0:
                prev_job_idx = static_seq[i-1]
                setup_duration = static_ts[prev_job_idx, job_idx]
                if setup_duration > 0:
                    setup_start = s_times[job_idx, m] - setup_duration
                    if setup_start >= 0:
                        static_gantt_data.append(dict(
                            Machine=f"Machine {m+1}",
                            Start=pd.to_datetime(setup_start, unit='s'),
                            Finish=pd.to_datetime(s_times[job_idx, m], unit='s'),
                            Type="Temps d'opération (Setup)",
                            Duration=setup_duration,
                            TaskInfo=f"Setup avant Job {job_idx + 1}"
                        ))
            
            # 2. إضافة فترة تشغيل المنتج العادية
            proc_duration = e_times[job_idx, m] - s_times[job_idx, m]
            static_gantt_data.append(dict(
                Machine=f"Machine {m+1}",
                Start=pd.to_datetime(s_times[job_idx, m], unit='s'),
                Finish=pd.to_datetime(e_times[job_idx, m], unit='s'),
                Type=f"Job {job_idx + 1}",
                Duration=proc_duration,
                TaskInfo=f"Exécution du Job {job_idx + 1}"
            ))
            
    if static_gantt_data:
        df_static_gantt = pd.DataFrame(static_gantt_data)
        
        # لوحة ألوان حديثة واحترافية للمنتجات (لوحة مريحة للعين ومتناسقة)
        color_map = {"🧪 Temps d'opération (Setup)": "#4A5568"} # رمادي داكن أنيق للإعداد
        
        fig_static = px.timeline(
            df_static_gantt,
            x_start="Start",
            x_end="Finish",
            y="Machine",
            color="Type",
            color_discrete_map=color_map,
            color_discrete_sequence=px.colors.qualitative.Safe, # ألوان جميلة واحترافية تلقائية للمنتجات
            title=f"📋 Diagramme de Gantt Complet Static | Makespan (Cmax) = {int(np.max(e_times))} s",
            hover_name="TaskInfo"
        )
        
        # تخصيص نافذة الـ Hover لتظهر بشكل منسق وجذاب جداً بالفرنسية/الإنجليزية
        fig_static.update_traces(
            hovertemplate="<b>%{hovertext}</b><br><br>📍 Machine: %{y}<br>⏱️ Durée: %{customdata[0]} secondes<br><extra></extra>",
            customdata=df_static_gantt[["Duration"]].values
        )
        
        fig_static.update_yaxes(autorange="reversed")
        fig_static.update_layout(
            xaxis_title="Temps Global (Minutes:Secondes)",
            xaxis=dict(tickformat="%M:%S", gridcolor="#E2E8F0"),
            yaxis=dict(gridcolor="#E2E8F0"),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            height=420,
            title_font=dict(size=18, family="Arial", color="#2D3748"),  # 🎯 تم التصحيح هنا
            hoverlabel=dict(
                bgcolor="#1A202C", 
                font_size=13, 
                font_family="Arial",
                font_color="white"
            )
        )       
        # تغليف المخطط داخل HTML Container لتطبيق تأثيرات الـ CSS الخارجي
        st.markdown('<div class="custom-gantt-container">', unsafe_allow_html=True)
        st.plotly_chart(fig_static, use_container_width=True, key="static_gantt_plotly")
        st.markdown('</div>', unsafe_allow_html=True)






# =========================
# 8. لوحة متابعة حالة الآلات والمنتجات المنتهية
# =========================
st.divider()

# تأكد أولاً من أن الجداول والتسلسل قد تم إنشاؤهم بنجاح قبل عرض اللوحة
if "Pij" in st.session_state and "sequence" in st.session_state:
    
    # جلب المتغيرات بشكل آمن ليتعرف عليها بايثون في هذا النطاق
    sequence = [int(i) - 1 for i in st.session_state.sequence] # تحويل التسلسل لـ index (0-based)
    n_machines = st.session_state.n_machines

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("🖥️ حالة الآلات الآن")
        machine_status = []
        
        # استخدام n_machines بعد الإصلاح السابق
        for m in range(n_machines):
            current_job = "متوقفة (Idle)"
            for j_idx, job_id in enumerate(sequence):  # الآن سيتعرف بايثون على sequence بدون مشاكل
                # التحقق إذا كان الوقت الحالي يقع بين بداية ونهاية الوظيفة على هذه الآلة
                if start_times[j_idx, m] <= current_sim_time <= end_times[j_idx, m]:
                    current_job = f"🔨 Job {job_id + 1}"
                    break
            machine_status.append({"الآلة": f"Machine {m+1}", "المنتج الحالي": current_job})
        
        st.table(pd.DataFrame(machine_status))

    with col2:
        st.subheader("✅ المنتجات المكتملة")
        completed_jobs = []
        
        # نمر على كل وظيفة ونتحقق من آخر آلة في الخط
        for j_idx, job_id in enumerate(sequence):
            finish_time_on_last_machine = end_times[j_idx, n_machines - 1]
            
            if current_sim_time >= finish_time_on_last_machine:
                completed_jobs.append({
                    "المنتج": f"Job {job_id + 1}",
                    "وقت البدء (ث)": f"{start_times[j_idx, 0]:.1f}", 
                    "وقت الانتهاء (ث)": f"{finish_time_on_last_machine:.1f}", 
                    "الحالة": "تم الإنجاز"
                })
        
        if completed_jobs:
            st.dataframe(pd.DataFrame(completed_jobs), use_container_width=True)
        else:
            st.info("لا توجد منتجات مكتملة بالكامل حتى الآن.")

    # =========================
    # 9. إحصائيات سريعة
    # =========================
    if completed_jobs:
        progress = len(completed_jobs) / len(sequence)
        st.progress(progress)
        st.write(f"📊 نسبة الإنجاز الكلية: {progress*100:.1f}%")

else:
    # رسالة تظهر للمستخدم إذا فتح الصفحة لأول مرة قبل توليد البيانات
    st.info("⏳ الرجاء الضغط على زر 'إنشاء الجداول' أولاً لتوليد البيانات وعرض حالة الآلات.")
