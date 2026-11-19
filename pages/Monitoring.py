import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import os
import time
import threading
import smtplib

from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client

# =========================
# 1. Configuration de la page
# =========================
st.set_page_config(page_title="Système de Supervision et de Surveillance (SCADA)", layout="wide")

st.title(":material/monitoring: Système de Supervision et de Surveillance (SCADA)")

# =========================
# 2. Configuration Telegram
# =========================
TELEGRAM_TOKEN = "8800481127:AAEibU7DQCV4NgPVw7EBbt1jz_QYAXC3KIc"

# Catégories de pannes (clés utilisées partout dans l'application)
CAT_TEMP = "Température"
CAT_HUM = "Humidité"
CAT_PRESS = "Pression"
CAT_VIBE = "Vibration"
CAT_CURR = "Courant"
CAT_GENERAL = "Général/Secours"

CONTACTS = {
    CAT_TEMP: "@CCryptomic",
    CAT_HUM: "CHAT_ID_HUMID",
    CAT_PRESS: "CHAT_ID_PRESSURE",
    CAT_VIBE: "CHAT_ID_VIBRATION",
    CAT_CURR: "CHAT_ID_ELECTRIC",
    CAT_GENERAL: "CHAT_ID_GENERAL"
}

# 💡 Renseignez ici l'e-mail expéditeur et les identifiants de votre compte :
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "mohamedbachirhabchi@gmail.com"
SENDER_PASSWORD = "wrmi lpuz geyj ssyp"  # Mot de passe d'application Google (et non le mot de passe habituel du compte)

# =========================
# Configuration Twilio (messages WhatsApp / SMS)
# =========================
TWILIO_ACCOUNT_SID = "AC63ca0d3643cccca495c8409993ad6e34"
TWILIO_AUTH_TOKEN = "68510f98171cd751af475b790f0aeef5"

TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"

# Votre numéro personnel lié au Sandbox (préfixe « whatsapp: » obligatoire)
YOUR_PERSONAL_NUMBER = "whatsapp:+15055510744"

# =========================
# 3. Gestion des données des employés (sauvegarde permanente en JSON)
# =========================
CONFIG_FILE = "workers_Information.json"

# Données par défaut si le fichier n'existe pas
default_contacts = {
    CAT_TEMP: {"name": "Technicien de Température", "telegram_id": "@CCryptxwcdomic", "email": "bachirhabchi3@gmail.com", "phone": "+213541445824"},
    CAT_HUM: {"name": "Technicien d'Humidité", "telegram_id": "@CCryptrhrttomic", "email": "MohamedAmineAbdellatif@gmail.com", "phone": "+213541445825"},
    CAT_PRESS: {"name": "Technicien de Pression", "telegram_id": "@CCryptoytrhmic", "email": "YassineSebaa@gmail.com", "phone": "+213541445826"},
    CAT_VIBE: {"name": "Technicien de Vibration", "telegram_id": "@CCrypfghtomic", "email": "HamidSoukeur@gmail.com", "phone": "+213541445827"},
    CAT_CURR: {"name": "Technicien d'Électricité", "telegram_id": "@CCryptomic", "email": "bachirhabchi3@gmail.com", "phone": "+213541445828"},
    CAT_GENERAL: {"name": "Technicien Général", "telegram_id": "@CCryptofdgfdic", "email": "BoulilaMohamedTaher@gmail.com", "phone": "+213541445829"}
}

# Anciennes clés (arabes) -> nouvelles clés françaises, pour les fichiers déjà enregistrés
LEGACY_KEYS = {
    "حرارة": CAT_TEMP,
    "رطوبة": CAT_HUM,
    "ضغط": CAT_PRESS,
    "اهتزاز": CAT_VIBE,
    "تيار": CAT_CURR,
    "عام/احتياطي": CAT_GENERAL,
}


def migrate_contacts(data):
    """Convertit les anciennes clés du fichier JSON vers les clés françaises."""
    return {LEGACY_KEYS.get(k, k): v for k, v in data.items()}


# =========================
# Gestion des limites de danger (sauvegarde permanente en JSON)
# =========================
LIMITS_FILE = "limits_configuration.json"

# Valeurs par défaut des limites si le fichier n'existe pas
default_limits = {
    "t_limit": 100,
    "h_limit": 100,
    "p_limit": 15.0,
    "v_limit": 10.0,
    "c_limit": 50
}

# Création du fichier avec les valeurs par défaut s'il n'existe pas
if not os.path.exists(LIMITS_FILE):
    with open(LIMITS_FILE, "w", encoding="utf-8") as f:
        json.dump(default_limits, f, ensure_ascii=False, indent=4)


# Sauvegarde immédiate des limites dès qu'un curseur change
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


# Chargement des données depuis le fichier, ou création avec les valeurs par défaut
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(default_contacts, f, ensure_ascii=False, indent=4)

if "workers_contacts" not in st.session_state:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        st.session_state.workers_contacts = migrate_contacts(json.load(f))


# Sauvegarde immédiate des modifications dans le fichier
def save_workers_Information():
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.workers_contacts, f, ensure_ascii=False, indent=4)


# =========================
# 4. Outils : durées et notifications
# =========================
def format_duration(total_seconds):
    """Formate une durée en secondes sous la forme « 1 h 05 min 12 s »."""
    total_seconds = max(0, int(total_seconds))
    h, rest = divmod(total_seconds, 3600)
    m, s = divmod(rest, 60)
    if h:
        return f"{h} h {m:02d} min {s:02d} s"
    if m:
        return f"{m} min {s:02d} s"
    return f"{s} s"


def send_real_notifications(machine_name, fault_label, worker_info, value_str, start_clock):
    """
    Envoi de vraies notifications (Telegram, e-mail et WhatsApp) au technicien responsable.
    """
    message_text = (
        f"🚨 Alerte de panne sur {machine_name}\n"
        f"Type de panne : {fault_label}\n"
        f"Valeur actuelle : {value_str}\n"
        f"Heure de début : {start_clock}\n"
        f"Responsable : {worker_info['name']}\n"
        f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    # [1] Envoi Telegram
    try:
        # Remarque : l'API Telegram exige un Chat ID numérique (ou un @username si le bot partage un groupe avec le technicien)
        tg_id = worker_info["telegram_id"]
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": tg_id, "text": message_text})
    except Exception as e:
        st.sidebar.error(f"Erreur d'envoi Telegram : {e}")

    # [2] Envoi de l'e-mail (SMTP)
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = worker_info["email"]
        msg['Subject'] = f"🚨 ALERTE : {machine_name} - {fault_label}"
        msg.attach(MIMEText(message_text, 'plain', 'utf-8'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, worker_info["email"], msg.as_string())
    except Exception as e:
        st.sidebar.error(f"Erreur d'envoi de l'e-mail : {e}")

    # [3] Envoi WhatsApp (Twilio)
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message_text,
            from_=TWILIO_WHATSAPP_NUMBER,  # Numéro WhatsApp fourni par Twilio
            to=f"whatsapp:{worker_info['phone']}"  # Numéro du technicien, ajouté dynamiquement
        )
    except Exception as e:
        st.sidebar.error(f"Erreur d'envoi WhatsApp : {e}")


def get_health_color(health):
    if health > 80:
        return "#2eba00"  # vert
    elif health > 40:
        return "#f5b700"  # jaune
    else:
        return "#e63946"  # rouge


def local_css(file_name):
    with open(file_name, encoding="utf-8") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


local_css("style.css")

STATUS_RUNNING = "En marche"
STATUS_REPAIR = "En panne 🛠️"


def start_fault(machine, fault_type, source, worker_name="—"):
    """Enregistre le début d'une panne : machine, heure de début, type, source et intervenant."""
    sim_seconds = (datetime.now() - st.session_state.sim_start_time).total_seconds()
    st.session_state.machine_faults[machine].append({
        "start": sim_seconds,          # secondes depuis le début de la simulation (utilisé par le Gantt)
        "end": None,                   # None tant que la panne n'est pas résolue
        "start_clock": datetime.now(), # heure réelle de début de la panne
        "type": fault_type,
        "source": source,
        "worker": worker_name,
    })


def end_fault(machine):
    """Clôture la dernière panne ouverte de la machine."""
    sim_seconds = (datetime.now() - st.session_state.sim_start_time).total_seconds()
    faults = st.session_state.machine_faults.get(machine, [])
    if faults and faults[-1]["end"] is None:
        faults[-1]["end"] = sim_seconds
        faults[-1]["end_clock"] = datetime.now()


def toggle_machine(machine, source="Manuel 👤", fault_type="Panne manuelle"):
    if "machine_faults" not in st.session_state:
        st.session_state.machine_faults = {f"Machine {i+1}": [] for i in range(5)}

    if st.session_state.machine_status[machine] == STATUS_RUNNING:
        st.session_state.machine_status[machine] = STATUS_REPAIR
        start_fault(machine, fault_type, source)
    else:
        st.session_state.machine_status[machine] = STATUS_RUNNING
        end_fault(machine)


def build_fault_journal(current_sim_seconds):
    """Construit le journal des pannes : une ligne par panne, avec heure de début et durée."""
    rows = []
    for machine, faults in st.session_state.machine_faults.items():
        for f in faults:
            ongoing = f["end"] is None
            end_s = current_sim_seconds if ongoing else f["end"]
            start_clock = f.get("start_clock")
            end_clock = f.get("end_clock")
            rows.append({
                "Machine": machine,
                "Type de panne": f.get("type", "Panne"),
                "Date": start_clock.strftime("%Y-%m-%d") if start_clock else "—",
                "Heure de début": start_clock.strftime("%H:%M:%S") if start_clock else "—",
                "Heure de fin": ("En cours…" if ongoing else (end_clock.strftime("%H:%M:%S") if end_clock else "—")),
                "Durée de la panne": format_duration(end_s - f["start"]),
                "Source": f.get("source", "—"),
                "Intervenant": f.get("worker", "—"),
                "État": "🔴 En cours" if ongoing else "🟢 Résolue",
                "_sort": start_clock or datetime.min,
            })
    if not rows:
        return pd.DataFrame(columns=[
            "Machine", "Type de panne", "Date", "Heure de début", "Heure de fin",
            "Durée de la panne", "Source", "Intervenant", "État"
        ])
    df = pd.DataFrame(rows).sort_values("_sort", ascending=False).drop(columns="_sort")
    return df.reset_index(drop=True)


def send_telegram_msg(chat_id, message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": message})
    except:
        pass


def can_send_alert(machine, key, cooldown=180):
    now = time.time()

    alert_key = f"{machine}_{key}"

    last_time = st.session_state.last_alert_time.get(alert_key, 0)

    if now - last_time > cooldown:
        st.session_state.last_alert_time[alert_key] = now
        return True

    return False


# =========================
# 5. État de session (Session State)
# =========================
# Lecture des limites depuis le fichier JSON pour qu'elles survivent au rafraîchissement
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

if "sim_start_time" not in st.session_state:
    st.session_state.sim_start_time = datetime.now()

if "machine_status" not in st.session_state:
    st.session_state.machine_status = {
        f"Machine {i+1}": STATUS_RUNNING for i in range(5)
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
# 6. Rafraîchissement automatique
# =========================
st_autorefresh(interval=2000, key="refresh")

# =========================
# 7. Barre latérale : paramètres
# =========================
with st.sidebar:
    st.markdown(
        "<h3 style='text-align: center;'>Paramètres</h3>",
        unsafe_allow_html=True)
    with st.expander("Données des employés"):
        for fault_label, info in st.session_state.workers_contacts.items():

            # Un sous-menu par employé à l'intérieur du menu principal
            with st.expander(f"{info['name']}"):

                # La clé est liée directement au session_state pour une mise à jour immédiate
                st.text_input(
                    "Numéro de téléphone", key=f"phone_{fault_label}",
                    value=st.session_state.workers_contacts[fault_label]["phone"],
                    on_change=lambda fl=fault_label: (st.session_state.workers_contacts[fl].update({"phone": st.session_state[f"phone_{fl}"]}), save_workers_Information())
                )
                st.text_input(
                    "Telegram ID", key=f"tg_{fault_label}",
                    value=st.session_state.workers_contacts[fault_label]["telegram_id"],
                    on_change=lambda fl=fault_label: (st.session_state.workers_contacts[fl].update({"telegram_id": st.session_state[f"tg_{fl}"]}), save_workers_Information())
                )
                st.text_input(
                    "Adresse e-mail", key=f"email_{fault_label}",
                    value=st.session_state.workers_contacts[fault_label]["email"],
                    on_change=lambda fl=fault_label: (st.session_state.workers_contacts[fl].update({"email": st.session_state[f"email_{fl}"]}), save_workers_Information())
                )

    with st.expander("Limites de danger"):
        # on_change=save_limits_to_json : sauvegarde immédiate dans le fichier à chaque modification
        t_limit = st.slider("Température", 1, 120, value=st.session_state.t_limit, key="t_limit", on_change=save_limits_to_json)
        h_limit = st.slider("Humidité", 5, 100, value=st.session_state.h_limit, key="h_limit", on_change=save_limits_to_json)
        p_limit = st.slider("Pression", 1.0, 15.0, value=st.session_state.p_limit, key="p_limit", on_change=save_limits_to_json)
        v_limit = st.slider("Vibration", 1.0, 10.0, value=st.session_state.v_limit, key="v_limit", on_change=save_limits_to_json)
        c_limit = st.slider("Courant", 1, 50, value=st.session_state.c_limit, key="c_limit", on_change=save_limits_to_json)

# =========================
# 8. Données de fonctionnement (mise à jour des données puis envoi)
# =========================
sim_now = datetime.now()
sim_duration = (sim_now - st.session_state.sim_start_time).total_seconds()
fault_time = sim_duration
minutes = int(fault_time // 60)
seconds = int(fault_time % 60)
all_data = {}

for machine in machines:

    # -------------------------
    # 1. Génération des données aléatoires de chaque machine
    # -------------------------
    np.random.seed(hash(machine) % 10000)
    temp = np.random.uniform(65, 5)
    humidity = np.random.uniform(55, 10)
    pressure = np.random.uniform(6, 1.5)
    vibe = np.random.uniform(3, 1)
    current = np.random.uniform(20, 5)

    checks = [
        (temp > t_limit, "temp", CAT_TEMP, f"{temp:.1f}°C"),
        (humidity > h_limit, "humid", CAT_HUM, f"{humidity:.1f}%"),
        (pressure > p_limit, "press", CAT_PRESS, f"{pressure:.1f} Bar"),
        (vibe > v_limit, "vibe", CAT_VIBE, f"{vibe:.2f} mm/s"),
        (current > c_limit, "curr", CAT_CURR, f"{current:.1f} A")
    ]

    # -------------------------
    # 2. Mise à jour immédiate de la santé et détection des pannes
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

    # Enregistrement immédiat de la santé et des mesures
    all_data[machine] = {
        "temp": temp,
        "humidity": humidity,
        "pressure": pressure,
        "vibe": vibe,
        "current": current,
        "health": health
    }

    # -------------------------
    # 3. Décision : état de la machine et journal des pannes
    # -------------------------
    if health <= 80 and active_faults:
        primary_fault_key, primary_fault_label, primary_fault_val = active_faults[0]

        if can_send_alert(machine, primary_fault_key, cooldown=180):

            # Technicien responsable (affiché dans le journal)
            worker_info = st.session_state.workers_contacts.get(
                primary_fault_label,
                st.session_state.workers_contacts[CAT_GENERAL]
            )

            # a) Passage de la machine « en panne » et enregistrement du début de la panne
            fault_start_clock = datetime.now().strftime("%H:%M:%S")
            if st.session_state.machine_status[machine] == STATUS_RUNNING:
                st.session_state.machine_status[machine] = STATUS_REPAIR
                start_fault(machine, primary_fault_label, "Auto 🤖", worker_info["name"])

            # -------------------------
            # 4. Envoi des notifications réelles en arrière-plan
            # -------------------------
            threading.Thread(
                target=send_real_notifications,
                args=(machine, primary_fault_label, worker_info, primary_fault_val, fault_start_clock)
            ).start()

# ========================================================
# Alarme sonore lorsque la santé passe sous 80 %
# ========================================================
low_health_machines = [m for m, data in all_data.items() if data["health"] < 81]

if low_health_machines:
    alarm_url = "https://actions.google.com/sounds/v1/alarms/digital_watch_alarm_long.ogg"

    # HTML masqué pour lancer le son automatiquement
    st.components.v1.html(
        f'''
        <audio autoplay style="display:none;">
            <source src="{alarm_url}" type="audio/ogg">
        </audio>
        ''',
        height=0,
    )

    # Alerte visuelle en haut de l'écran
    st.error(f"🚨 Attention : baisse de l'indicateur de santé sur les machines suivantes : {', '.join(low_health_machines)}")

# ========================================================

# =========================
# 9. Tableau de bord
# =========================

# Indicateurs globaux sur les pannes
all_faults = [f for fl in st.session_state.machine_faults.values() for f in fl]
nb_faults = len(all_faults)
nb_ongoing = sum(1 for f in all_faults if f["end"] is None)
total_downtime = sum(((sim_duration if f["end"] is None else f["end"]) - f["start"]) for f in all_faults)

k1, k2, k3, k4 = st.columns(4)
k1.metric(":material/timer: Temps de simulation", f"{minutes} min {seconds:02d} s")
k2.metric(":material/report_problem: Nombre de pannes", nb_faults)
k3.metric(":material/build: Pannes en cours", nb_ongoing)
k4.metric(":material/hourglass_bottom: Durée totale d'arrêt", format_duration(total_downtime))

st.write("")

# --- Calcul de l'efficacité et de la stabilité selon l'état réel des machines ---

# 1. Liste des machines qui fonctionnent (hors panne)
working_machines = [m for m, status in st.session_state.machine_status.items() if status == STATUS_RUNNING]
num_working = len(working_machines)

# 2. Moyenne de la santé des machines en marche
if num_working > 0:
    avg_health = sum([all_data[m]["health"] for m in working_machines]) / num_working
else:
    avg_health = 0

# 3. Efficacité : dépend du nombre de machines en marche (chaque machine = 20 % de la capacité de l'usine)
factory_efficiency = (num_working / 5) * avg_health + np.random.uniform(-2, 2)

# 4. Stabilité : dépend de la santé moyenne globale
factory_stability = avg_health + np.random.uniform(-5, 5)

# Enregistrement des nouvelles données
new_row = pd.DataFrame([{
    "time": int(sim_duration),
    "Efficacité": max(0, min(100, factory_efficiency)),
    "Stabilité": max(0, min(100, factory_stability))
}])

# Ajout du nouveau point puis conservation des 20 derniers seulement (performances)
st.session_state.performance_data = pd.concat(
    [st.session_state.performance_data, new_row],
    ignore_index=True
).tail(20)

for machine, data in all_data.items():
    status = st.session_state.machine_status[machine]
    health_val = data["health"]
    accent = get_health_color(health_val)
    in_repair = status == STATUS_REPAIR

    if in_repair:
        accent = "#e63946"

    with st.container(border=True):
        col_header, col_btn = st.columns([3, 1])
        with col_header:
            status_class = "status-pill status-down" if in_repair else "status-pill status-ok"
            st.markdown(
                f'<div class="machine-title" style="border-left: 6px solid {accent};">'
                f'<span class="machine-name">🔧 {machine}</span>'
                f'<span class="{status_class}">{status}</span></div>',
                unsafe_allow_html=True)

        with col_btn:
            if st.button("Modifier le statut", key=f"btn_{machine}", use_container_width=True):
                toggle_machine(machine)
                st.rerun()

        if in_repair:
            # Détails de la panne en cours : début + durée
            open_faults = [f for f in st.session_state.machine_faults[machine] if f["end"] is None]
            if open_faults:
                f = open_faults[-1]
                started = f["start_clock"].strftime("%H:%M:%S") if f.get("start_clock") else "—"
                st.warning(
                    f"⚠️ Cette machine est en panne ({f.get('type', 'Panne')}) — "
                    f"début à **{started}** — durée : **{format_duration(sim_duration - f['start'])}**"
                )
            else:
                st.warning("⚠️ Cette machine est en panne.")
        else:
            # Barre de santé personnalisée
            st.markdown(f'''
                <b>Indicateur de santé de la machine : {health_val}%</b>
                <div class="health-bar-container">
                    <div class="health-bar-fill" style="width: {health_val}%; background-color: {accent};"></div>
                </div>
            ''', unsafe_allow_html=True)

            # Affichage des mesures
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("🌡️ Température", f"{data['temp']:.1f}°C")
            c2.metric("💧 Humidité", f"{data['humidity']:.1f}%")
            c3.metric("⚙️ Pression", f"{data['pressure']:.1f} Bar")
            c4.metric("📳 Vibration", f"{data['vibe']:.2f}")
            c5.metric("⚡ Courant", f"{data['current']:.1f}A")

# =========================
# 9 bis. Formulaire d'ajout manuel d'une panne
# =========================
with st.expander(":material/add_circle: Ajouter une panne manuellement", expanded=False):
    with st.form("manual_fault_form", clear_on_submit=True):
        fc1, fc2 = st.columns(2)
        with fc1:
            f_machine = st.selectbox("Machine", machines)
            f_type = st.selectbox(
                "Type de panne",
                [CAT_TEMP, CAT_HUM, CAT_PRESS, CAT_VIBE, CAT_CURR, "Autre"]
            )
        with fc2:
            f_start_time = st.time_input("Heure de début", value=datetime.now().time().replace(microsecond=0), step=60)
            d1, d2 = st.columns(2)
            f_min = d1.number_input("Durée (minutes)", min_value=0, max_value=1440, value=5, step=1)
            f_sec = d2.number_input("Durée (secondes)", min_value=0, max_value=59, value=0, step=1)
        add_fault = st.form_submit_button("Enregistrer la panne", type="primary")

    if add_fault:
        duration_s = int(f_min) * 60 + int(f_sec)
        if duration_s <= 0:
            st.error("La durée de la panne doit être supérieure à 0.")
        else:
            start_dt = datetime.combine(datetime.now().date(), f_start_time)
            start_s = max(0.0, (start_dt - st.session_state.sim_start_time).total_seconds())
            st.session_state.machine_faults[f_machine].append({
                "start": start_s,
                "end": start_s + duration_s,
                "start_clock": start_dt,
                "end_clock": start_dt + timedelta(seconds=duration_s),
                "type": f_type,
                "source": "Manuel 👤",
                "worker": "—",
            })
            st.success(f"Panne ajoutée sur {f_machine} : début {f_start_time.strftime('%H:%M:%S')}, durée {format_duration(duration_s)}.")

# =========================
# 10. Graphiques + journal
# =========================
st.subheader("Performance globale (série temporelle en direct)")

df = st.session_state.performance_data

if not df.empty:
    # Tri par seconde et utilisation du temps comme axe principal
    df_plot = df.sort_values("time").set_index("time")
    st.line_chart(df_plot)
else:
    st.write("En attente du démarrage de la simulation...")

st.subheader(":material/history: Journal des pannes")
journal = build_fault_journal(sim_duration)

if journal.empty:
    st.info("Aucune panne enregistrée pour le moment.")
else:
    st.dataframe(journal, use_container_width=True, hide_index=True)
