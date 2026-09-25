import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import os
import time
import threading
import smtplib

from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
# =========================
# 1. إعداد الصفحة
# =========================



st.set_page_config(page_title="Systeme de Supervision et surveillance (SCADA)", layout="wide")

st.title("Systeme de Supervision et Surveillance (SCADA)")







# =========================
# 2. إعداد Telegram
# =========================
TELEGRAM_TOKEN = "8800481127:AAEibU7DQCV4NgPVw7EBbt1jz_QYAXC3KIc"

CONTACTS = {
    "حرارة": "@CCryptomic",
    "رطوبة": "CHAT_ID_HUMID",
    "ضغط": "CHAT_ID_PRESSURE",
    "اهتزاز": "CHAT_ID_VIBRATION",
    "تيار": "CHAT_ID_ELECTRIC",
    "عام/احتياطي": "CHAT_ID_GENERAL"
}
# 💡 ضع إيميلك المُرْسِل وبيانات حسابك هنا:
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "mohamedbachirhabchi@gmail.com"
SENDER_PASSWORD = "wrmi lpuz geyj ssyp"  # كلمة مرور التطبيقات من جوجل وليس كلمة مرور الحساب العادية

# =========================
# إعدادات Twilio (لرسائل SMS)
# =========================
TWILIO_ACCOUNT_SID = "AC63ca0d3643cccca495c8409993ad6e34"
TWILIO_AUTH_TOKEN = "68510f98171cd751af475b790f0aeef5"


TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"

# رقم هاتفك الشخصي الذي ربطته بالـ Sandbox (يجب إضافة whatsapp: قبل الرقم)
YOUR_PERSONAL_NUMBER = "whatsapp:+15055510744" # ضع رقمك هنا بالصيغة الدولية
# =========================
# 2. إدارة بيانات العمال (حفظ دائم في ملف JSON)
# =========================
CONFIG_FILE = "workers_Information.json"

# البيانات الافتراضية في حال عدم وجود الملف
default_contacts = {
        "حرارة": {"name": "Technicien de Temperature", "telegram_id": "@CCryptxwcdomic", "email": "bachirhabchi3@gmail.com", "phone": "+213541445824"},
        "رطوبة": {"name": "Technicien de Humidite", "telegram_id": "@CCryptrhrttomic", "email": "MohamedAmineAbdellatif@gmail.com", "phone": "+213541445825"},
        "ضغط": {"name": "Technicien de Pression", "telegram_id": "@CCryptoytrhmic", "email": "YassineSebaa@gmail.com", "phone": "+213541445826"},
        "اهتزاز": {"name": "Technicien de Vibration", "telegram_id": "@CCrypfghtomic", "email": "HamidSoukeur@gmail.com", "phone": "+213541445827"},
        "تيار": {"name": "Technicien de Electricite", "telegram_id": "@CCryptomic", "email": "bachirhabchi3@gmail.com", "phone": "+213541445828"},
        "عام/احتياطي": {"name": "Technicien Generale", "telegram_id": "@CCryptofdgfdic", "email": "BoulilaMohamedTaher@gmail.com", "phone": "+213541445829"}
}


# =========================
# إدارة حدود الخطر (حفظ دائم في ملف JSON)
# =========================
LIMITS_FILE = "limits_configuration.json"

# القيم الافتراضية للحدود في حال عدم وجود الملف
default_limits = {
    "t_limit": 100,
    "h_limit": 100,
    "p_limit": 15.0,
    "v_limit": 10.0,
    "c_limit": 50
}

# إنشاء الملف بالقيم الافتراضية إذا لم يكن موجوداً
if not os.path.exists(LIMITS_FILE):
    with open(LIMITS_FILE, "w", encoding="utf-8") as f:
        json.dump(default_limits, f, ensure_ascii=False, indent=4)

# دالة مخصصة لحفظ الحدود فوراً عند تغيير السلايدر
def save_limits_to_json():
    current_limits = {
        "t_limit": st.session_state.t_limit,
        "h_limit": st.session_state.h_limit,
        "p_limit": st.session_state.p_limit,
        "v_limit": st.session_state.v_limit,
        "c_limit": st.session_state.c_limit
    }
    with open(LIMITS_FILE, "w", encoding="utf-8") as f:
        json.dump(current_limits, f, ensure_ascii=False, indent=4)

# تحميل البيانات من الملف إذا كان موجوداً، أو إنشائه بالبيانات الافتراضية
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(default_contacts, f, ensure_ascii=False, indent=4)

if "workers_contacts" not in st.session_state:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        st.session_state.workers_contacts = json.load(f)

# دالة لحفظ التعديلات فوراً في الملف عند أي تغيير
def save_workers_Information():
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.workers_contacts, f, ensure_ascii=False, indent=4)

























def send_real_notifications(machine_name, fault_label, worker_info, value_str):
    """
    إرسال رسائل حقيقية عبر تلغرام، الإيميل، و الرسائل النصية للفني المسؤول.
    """
    message_text = f"🚨 تنبيه عطل في {machine_name}\nنوع العطل: {fault_label}\nالقيمة الحالية: {value_str}\nالمسؤول: {worker_info['name']}\nالتاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # [1] إرسال Telegram (حقيقي باستخدام المعرف المخزن للفني)
    try:
        # ملاحظة: التلغرام يحتاج Chat ID رقمي لإرسال API، أو يمكنك استخدام الـ username إذا كان البوت مشتركاً في مجموعة مع الفني
        tg_id = worker_info["telegram_id"]
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": tg_id, "text": message_text})
    except Exception as e:
        st.sidebar.error(f"خطأ في إرسال تلغرام: {e}")

    # [2] إرسال البريد الإلكتروني (Email حقيقي عبر SMTP)
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = worker_info["email"]
        msg['Subject'] = f"🚨 ALERT: {machine_name} - {fault_label}"
        msg.attach(MIMEText(message_text, 'plain', 'utf-8'))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, worker_info["email"], msg.as_string())
    except Exception as e:
        st.sidebar.error(f"error for send To email :  {e}")

    # [3] إرسال رسالة نصية (SMS حقيقي عبر Twilio)
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message_text,
            from_=TWILIO_WHATSAPP_NUMBER,  # استخدام رقم الواتساب الممنوح من تويليو
            to=f"whatsapp:{worker_info['phone']}"  # 👈 التعديل هنا: دمج السابقة البرمجية مع رقم العامل ديناميكياً
        )
    except Exception as e:
        st.sidebar.error(f"خطأ في إرسال WhatsApp: {e}")











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
# قراءة الحدود من ملف الـ JSON لضمان عدم ضياعها عند الـ Refresh
if "t_limit" not in st.session_state:
    with open(LIMITS_FILE, "r", encoding="utf-8") as f:
        saved_limits = json.load(f)
    st.session_state.t_limit = saved_limits.get("t_limit", 100)
    st.session_state.h_limit = saved_limits.get("h_limit", 100)
    st.session_state.p_limit = saved_limits.get("p_limit", 15.0)
    st.session_state.v_limit = saved_limits.get("v_limit", 10.0)
    st.session_state.c_limit = saved_limits.get("c_limit", 50)


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
        columns=["time", "Efficacité", "Stabilité"]
    )
    
# =========================
# 4. Title
# =========================
st_autorefresh(interval=2000, key="refresh")
# =========================
# 5. Sidebar Settings
# =========================
with st.sidebar:
    st.markdown(
    "<h3 style='text-align: center;'>Les Parametres</h3>",
    unsafe_allow_html=True)
    with st.expander("Données des employés"):
        # 2. حلقة التكرار الآن أصبحت بالداخل (لاحظ المسافات البادئة Indentation)
        for fault_label, info in st.session_state.workers_contacts.items():
            
            # 3. إنشاء القائمة الابن لكل موظف داخل القائمة الرئيسية
            with st.expander(f"{info['name']}"):
                
                # ربط الـ key بالـ session_state مباشرة ليعمل التحديث الفوري
                st.text_input(
                    "رقم الهاتف", key=f"phone_{fault_label}", 
                    value=st.session_state.workers_contacts[fault_label]["phone"],
                    on_change=lambda fl=fault_label: (st.session_state.workers_contacts[fl].update({"phone": st.session_state[f"phone_{fl}"]}), save_workers_Information())
                )
                st.text_input(
                    "Telegram ID", key=f"tg_{fault_label}", 
                    value=st.session_state.workers_contacts[fault_label]["telegram_id"],
                    on_change=lambda fl=fault_label: (st.session_state.workers_contacts[fl].update({"telegram_id": st.session_state[f"tg_{fl}"]}), save_workers_Information())
                )
                st.text_input(
                    "البريد الإلكتروني", key=f"email_{fault_label}", 
                    value=st.session_state.workers_contacts[fault_label]["email"],
                    on_change=lambda fl=fault_label: (st.session_state.workers_contacts[fl].update({"email": st.session_state[f"email_{fl}"]}), save_workers_Information())
                )


    with st.expander("Limites de danger"):
        # أضفنا on_change=save_limits_to_json لتقوم بالحفظ فوراً في الملف عند أي تغيير
        t_limit = st.slider("حرارة", 1, 120, value=st.session_state.t_limit, key="t_limit", on_change=save_limits_to_json)
        h_limit = st.slider("رطوبة", 5, 100, value=st.session_state.h_limit, key="h_limit", on_change=save_limits_to_json)
        p_limit = st.slider("ضغط", 1.0, 15.0, value=st.session_state.p_limit, key="p_limit", on_change=save_limits_to_json)
        v_limit = st.slider("اهتزاز", 1.0, 10.0, value=st.session_state.v_limit, key="v_limit", on_change=save_limits_to_json)
        c_limit = st.slider("تيار", 1, 50, value=st.session_state.c_limit, key="c_limit", on_change=save_limits_to_json)


# =========================
# 7. بيانات التشغيل (تحديث البيانات أولاً ثم الإرسال)
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
    # 1. توليد البيانات العشوائية لكل آلة
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
    # 2. التحديث الفوري لبيانات الصحة ورصد الأعطال (هذا ما سيظهر على الشاشة فوراً)
    # -------------------------
    health = 100
    active_faults = []  
    
    for is_danger, key, label, val in checks:
        if is_danger:
            health -= 20
            active_faults.append((key, label, val))
            st.session_state.alerts_sent[machine][key] = True  
        else:
            st.session_state.alerts_sent[machine][key] = False 

    health = max(0, health)

    # حفظ بيانات الصحة والقراءات فوراً ليراها المتصفح دون انتظار
    all_data[machine] = {
        "temp": temp,
        "humidity": humidity,
        "pressure": pressure,
        "vibe": vibe,
        "current": current,
        "health": health
    }

    # -------------------------
    # 3. اتخاذ القرار وتحديث حالة الآلة وسجل الأعطال على الشاشة
    # -------------------------
    if health <= 80 and active_faults:
        primary_fault_key, primary_fault_label, primary_fault_val = active_faults[0]
        
        if can_send_alert(machine, primary_fault_key, cooldown=180):
            
            # أ) تحديث جدول الـ SCADA على الشاشة فوراً
            time_stamp = datetime.now().strftime("%H:%M:%S")
            date_stamp = datetime.now().strftime("%Y-%m-%d")
            
            # جلب بيانات الموظف لمعرفة اسمه فقط وعرضه في الجدول فوراً
            worker_info = st.session_state.workers_contacts.get(
                primary_fault_label, 
                st.session_state.workers_contacts["عام/احتياطي"]
            )
            
            new_entry = pd.DataFrame([{
                "Runtime": f"{minutes:02d}:{seconds:02d}", 
                "الآلة": machine, 
                "النوع": primary_fault_label, 
                "المصدر": f"آلي 🤖 ({date_stamp})", 
                "الحالة": f"صحة الآلة {health}% - جاري إخطار {worker_info['name']}"
            }])
            st.session_state.maintenance_log = pd.concat([new_entry, st.session_state.maintenance_log], ignore_index=True)
            
            # ب) تحويل حالة الآلة إلى "قيد الإصلاح" وتغيير لون الكارد فوراً
            if st.session_state.machine_status[machine] == "Running":
                st.session_state.machine_status[machine] = "Under Repair 🛠️"
                st.session_state.machine_faults[machine].append({
                    "start": sim_duration,
                    "end": None
                })
            
            # -------------------------
            # 4. إرسال الإشعارات الحقيقية في الخلفية (بشكل منفصل دون تعطيل الشاشة)
            # -------------------------
            # استخدام Threading يجعل بايثون يطلق الإرسال ويستكمل تحديث الصفحة في نفس الأجزاء من الثانية
            import threading
            threading.Thread(
                target=send_real_notifications, 
                args=(machine, primary_fault_label, worker_info, primary_fault_val)
            ).start()
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
    "Efficacité": max(0, min(100, factory_efficiency)),
    "Stabilité": max(0, min(100, factory_stability))
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
        if st.button(f"Modifier le statut", key=f"btn_{machine}"):
            toggle_machine(machine)
            st.rerun()

    if "Under Repair" in status:
        st.warning("⚠️ هذه الآلة قيد الإصلاح حالياً")
    else:
        
        # عرض شريط الصحة المخصص
        st.markdown(f'''
            <medium><b>Indicateur de santé de la machine: {health_val}%</b></medium>
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
    st.subheader("Performance globale(Live Time Series)")

    df = st.session_state.performance_data

    if not df.empty:
        # ترتيب البيانات حسب الثواني وضبطها كمحور أساسي
        df_plot = df.sort_values("time").set_index("time")
        
        # رسم المخطط لجميع البيانات من ثانية 0 حتى الآن
        st.line_chart(df_plot)
    else:
        st.write("بانتظار بدء المحاكاة...")

with col2:
    st.subheader("Journal des pannes")
    st.dataframe(st.session_state.maintenance_log, use_container_width=True, hide_index=True)
