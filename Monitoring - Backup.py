import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import time
from streamlit_autorefresh import st_autorefresh




# =========================
# 1. إعداد الصفحة
# =========================



st.set_page_config(page_title="Monitoring System", layout="wide")

st.title("🛡️ Monitoring System")

# =========================
# 2. إعداد Telegram
# =========================
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN"

CONTACTS = {
    "حرارة": "CHAT_ID_TEMP",
    "رطوبة": "CHAT_ID_HUMID",
    "ضغط": "CHAT_ID_PRESSURE",
    "اهتزاز": "CHAT_ID_VIBRATION",
    "تيار": "CHAT_ID_ELECTRIC",
    "عام/احتياطي": "CHAT_ID_GENERAL"
}



def get_health_color(health):
    if health > 80:
        return "#2eba00"  # أخضر خفيف جداً
    elif health > 40:
        return "#fffb00"  # أصفر خفيف جداً
    else:
        return "#ff0000"  # أحمر خفيف جداً
        

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

def send_telegram_msg(chat_id, message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": message})
    except:
        pass
        

def toggle_machine(machine, source="يدوي 👤", fault_type="عطل"):
    current_sim_duration = (datetime.now() - st.session_state.sim_start_time).total_seconds()
    time_stamp = f"{int(current_sim_duration // 60):02d}:{int(current_sim_duration % 60):02d}"

    # تهيئة قاموس الأعطال في الجلسة إذا لم يكن موجوداً
    if "machine_faults" not in st.session_state:
        st.session_state.machine_faults = {f"Machine {i+1}": [] for i in range(5)}

    if st.session_state.machine_status[machine] == "Running":
        st.session_state.machine_status[machine] = "Under Repair 🛠️"
        status_text = "قيد الإصلاح"
        
        # تسجيل بداية العطل بالثواني
        st.session_state.machine_faults[machine].append({
            "start": current_sim_duration,
            "end": None  # لم تنتهِ بعد
        })
    else:
        st.session_state.machine_status[machine] = "Running"
        status_text = "تم الإصلاح"
        fault_type = "عودة للعمل"
        
        # تحديث وقت نهاية آخر عطل تم تسجيله لهذه الآلة
        if machine in st.session_state.machine_faults and len(st.session_state.machine_faults[machine]) > 0:
            if st.session_state.machine_faults[machine][-1]["end"] is None:
                st.session_state.machine_faults[machine][-1]["end"] = current_sim_duration

    new_entry = pd.DataFrame([{"Runtime": time_stamp, "الآلة": machine, "النوع": fault_type, "المصدر": source, "الحالة": status_text}])
    st.session_state.maintenance_log = pd.concat([new_entry, st.session_state.maintenance_log], ignore_index=True)

        
        
def can_send_alert(machine, key, cooldown=180):
    now = time.time()

    alert_key = f"{machine}_{key}"

    last_time = st.session_state.last_alert_time.get(alert_key, 0)

    if now - last_time > cooldown:
        st.session_state.last_alert_time[alert_key] = now
        return True

    return False
# =========================
# 3. Session State
# =========================

if "machine_faults" not in st.session_state:
    st.session_state.machine_faults = {f"Machine {i+1}": [] for i in range(5)}


if "maintenance_log" not in st.session_state:
    st.session_state.maintenance_log = pd.DataFrame(
        columns=["Runtime", "الآلة", "النوع", "المصدر", "الحالة"]
    )
    
if "sim_start_time" not in st.session_state:
    st.session_state.sim_start_time = datetime.now()

if "machine_status" not in st.session_state:
    st.session_state.machine_status = {
        f"Machine {i+1}": "Running" for i in range(5)
    }
machines = [f"Machine {i+1}" for i in range(5)]

if "alerts_sent" not in st.session_state:
    st.session_state.alerts_sent = {
        m: {"temp": False, "humid": False, "press": False, "vibe": False, "curr": False}
        for m in machines
    }

if "last_alert_time" not in st.session_state:
    st.session_state.last_alert_time = {}
    
    
if "performance_data" not in st.session_state:
    st.session_state.performance_data = pd.DataFrame(
        columns=["time", "الكفاءة", "الاستقرار"]
    )
    
# =========================
# 4. Title
# =========================
st.title("AI Monitoring System")
st_autorefresh(interval=1000, key="refresh")
# =========================
# 5. Sidebar Settings
# =========================
with st.sidebar:
    st.header("⚙️ حدود الخطر")

    t_limit = st.slider("حرارة", 1, 120, 100)
    h_limit = st.slider("رطوبة", 5, 100, 100)
    p_limit = st.slider("ضغط", 1.0, 15.0, 15.0)
    v_limit = st.slider("اهتزاز", 1.0, 10.0, 10.0)
    c_limit = st.slider("تيار", 1, 50, 50)

# =========================
# 6. زر تحديث (بديل while True)
# =========================
if st.button("🔄 تحديث البيانات"):
    st.rerun()

# =========================
# 7. بيانات التشغيل
# =========================
sim_now = datetime.now()
sim_duration = (sim_now - st.session_state.sim_start_time).total_seconds()
fault_time = sim_duration
minutes = int(fault_time // 60)
seconds = int(fault_time % 60)
all_data = {}
now_time = datetime.now().strftime("%H:%M:%S")

for machine in machines:

    # -------------------------
    # بيانات عشوائية لكل آلة
    # -------------------------
    np.random.seed(hash(machine) % 10000)
    temp = np.random.uniform(65, 5)
    humidity = np.random.uniform(55, 10)
    pressure = np.random.uniform(6, 1.5)
    vibe = np.random.uniform(3, 1)
    current = np.random.uniform(20, 5)

    checks = [
        (temp > t_limit, "temp", "حرارة", f"{temp:.1f}°C"),
        (humidity > h_limit, "humid", "رطوبة", f"{humidity:.1f}%"),
        (pressure > p_limit, "press", "ضغط", f"{pressure:.1f} Bar"),
        (vibe > v_limit, "vibe", "اهتزاز", f"{vibe:.2f} mm/s"),
        (current > c_limit, "curr", "تيار", f"{current:.1f} A")
    ]

    # -------------------------
    # الفحص والتنبيهات
    # -------------------------
    for is_danger, key, label, val in checks:

        if is_danger and can_send_alert(machine, key):
            send_telegram_msg(CONTACTS.get(label, CONTACTS["عام/احتياطي"]), f"🚨 {machine}\n{label}: {val}")
            
            # السطر الجديد المسؤول عن تغيير الحالة تلقائياً:
            if st.session_state.machine_status[machine] == "Running":
                toggle_machine(machine, source="آلي 🤖", fault_type=label)

            st.session_state.alerts_sent[machine][key] = True

        elif not is_danger:
            st.session_state.alerts_sent[machine][key] = False

    # -------------------------
    # حساب الصحة
    # -------------------------
    health = 100
    for is_danger, _, _, _ in checks:
        if is_danger:
            health -= 20

    all_data[machine] = {
        "temp": temp,
        "humidity": humidity,
        "pressure": pressure,
        "vibe": vibe,
        "current": current,
        "health": max(0, health)
    }



# ========================================================
# 🛑 الكود الجديد: إضافة صوت الإنذار عند نزول الصحة تحت 80%
# ========================================================

# مصفوفة لتخزين الآلات التي تعاني من مشاكل في هذا التحديث
low_health_machines = [m for m, data in all_data.items() if data["health"] < 81]

if low_health_machines:
    # رابط لصوت إنذار خارجي (يمكنك استبداله بأي رابط صوتي مباشر MP3 تفضله)
    alarm_url = "https://actions.google.com/sounds/v1/alarms/digital_watch_alarm_long.ogg"
    
    # كود HTML مخفي لتشغيل الصوت تلقائياً بمجرد نزول الصحة
    st.components.v1.html(
        f'''
        <audio autoplay style="display:none;">
            <source src="{alarm_url}" type="audio/ogg">
        </audio>
        ''',
        height=0,
    )
    
    # تنبيه مرئي يظهر أعلى الشاشة بجانب الصوت
    st.error(f"🚨 تحذير: انخفاض مؤشر الصحة في الآلات التالية: {', '.join(low_health_machines)}")

# ========================================================





# =========================
# 8. العرض (Dashboard) المطور
# =========================


st.info(f"⏱️ Runtime: {minutes} minutes {seconds} seconds")


# --- حساب الكفاءة والاستقرار بناءً على حالة الآلات الفعلية ---

# 1. جلب قائمة بالآلات التي تعمل فقط (ليست تحت الإصلاح)
working_machines = [m for m, status in st.session_state.machine_status.items() if status == "Running"]
num_working = len(working_machines)

# 2. حساب متوسط الصحة للآلات التي تعمل
if num_working > 0:
    avg_health = sum([all_data[m]["health"] for m in working_machines]) / num_working
else:
    avg_health = 0

# 3. حساب الكفاءة: تتأثر بعدد الآلات الشغالة (كل آلة تمثل 20% من طاقة المصنع)
# مع إضافة لمسة عشوائية بسيطة للمحاكاة
factory_efficiency = (num_working / 5) * avg_health + np.random.uniform(-2, 2)

# 4. حساب الاستقرار: يتأثر بمتوسط الصحة العام
factory_stability = avg_health + np.random.uniform(-5, 5)

# تسجيل البيانات الجديدة
new_row = pd.DataFrame([{
    "time": int(sim_duration), 
    "الكفاءة": max(0, min(100, factory_efficiency)),
    "الاستقرار": max(0, min(100, factory_stability))
}])

# إضافة النقطة الجديدة ثم الاحتفاظ بآخر 20 نقطة فقط لتسريع الأداء
st.session_state.performance_data = pd.concat(
    [st.session_state.performance_data, new_row],
    ignore_index=True
).tail(20) # ✅ هذا السطر يضمن بقاء الذاكرة خفيفة دائماً


for machine, data in all_data.items():
    status = st.session_state.machine_status[machine]
    health_val = data["health"]
    bg_color = get_health_color(health_val)

    # بداية كارد الآلة
    
    if "Under Repair" in status:
        bg_color = "#fff" # رمادي

    st.markdown(f'''
        <div class="machine-card" style="background-color: {bg_color}; border-right: 5px solid {bg_color.replace('0.1', '1')};">
    ''', unsafe_allow_html=True)
    
    
    
    col_header, col_btn = st.columns([3, 1])
    with col_header:
        # تلوين الحالة بناءً على نوعها
        status_color = "#28a745" if "Running" in status else "#dc3545"
        st.markdown(f'<h3>🔧 {machine} | <span style="color:{status_color}">{status}</span></h3>', unsafe_allow_html=True)
    
    with col_btn:
        if st.button(f"تغيير الحالة", key=f"btn_{machine}"):
            toggle_machine(machine)
            st.rerun()

    if "Under Repair" in status:
        st.warning("⚠️ هذه الآلة قيد الإصلاح حالياً")
    else:
        
        # عرض شريط الصحة المخصص
        st.markdown(f'''
            <medium><b>مؤشر صحة الآلة: {health_val}%</b></medium>
            <div class="health-bar-container">
                <div class="health-bar-fill" style="width: {health_val}%; background-color: {bg_color};"></div>
        ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # عرض المقاييس
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("🌡️ حرارة", f"{data['temp']:.1f}°C")
        c2.metric("💧 رطوبة", f"{data['humidity']:.1f}%")
        c3.metric("⚙️ ضغط", f"{data['pressure']:.1f} Bar")
        c4.metric("📳 اهتزاز", f"{data['vibe']:.2f}")
        c5.metric("⚡ تيار", f"{data['current']:.1f}A")
    
    st.markdown('</div>', unsafe_allow_html=True) # نهاية كارد الآلة
    st.write("") # مسافة بسيطة
    st.markdown('</div>', unsafe_allow_html=True)
# =========================
# 9. Charts + Logs
# =========================
col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader("📊 أداء عام (Live Time Series)")

    df = st.session_state.performance_data

    if not df.empty:
        # ترتيب البيانات حسب الثواني وضبطها كمحور أساسي
        df_plot = df.sort_values("time").set_index("time")
        
        # رسم المخطط لجميع البيانات من ثانية 0 حتى الآن
        st.line_chart(df_plot)
    else:
        st.write("بانتظار بدء المحاكاة...")

with col2:
    st.subheader("📋 سجل الأعطال")
    st.dataframe(st.session_state.maintenance_log, use_container_width=True, hide_index=True)