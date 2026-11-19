import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import time
from streamlit_autorefresh import st_autorefresh




# =========================
# 1. Configuration de la page
# =========================



st.set_page_config(page_title="Système de monitoring", layout="wide")

st.title("🛡️ Système de monitoring")

# =========================
# 2. Configuration de Telegram
# =========================
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN"

CONTACTS = {
    "Température": "CHAT_ID_TEMP",
    "Humidité": "CHAT_ID_HUMID",
    "Pression": "CHAT_ID_PRESSURE",
    "Vibration": "CHAT_ID_VIBRATION",
    "Courant": "CHAT_ID_ELECTRIC",
    "Général/Secours": "CHAT_ID_GENERAL"
}



def get_health_color(health):
    if health > 80:
        return "#2eba00"  # Vert très clair
    elif health > 40:
        return "#fffb00"  # Jaune très clair
    else:
        return "#ff0000"  # Rouge très clair
        

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
        

def toggle_machine(machine, source="Manuel 👤", fault_type="Panne"):
    current_sim_duration = (datetime.now() - st.session_state.sim_start_time).total_seconds()
    time_stamp = f"{int(current_sim_duration // 60):02d}:{int(current_sim_duration % 60):02d}"

    # Initialisation du dictionnaire des pannes dans la session s'il n'existe pas
    if "machine_faults" not in st.session_state:
        st.session_state.machine_faults = {f"Machine {i+1}": [] for i in range(5)}

    if st.session_state.machine_status[machine] == "Running":
        st.session_state.machine_status[machine] = "Under Repair 🛠️"
        status_text = "En réparation"
        
        # Enregistrement du début de la panne en secondes
        st.session_state.machine_faults[machine].append({
            "start": current_sim_duration,
            "end": None  # pas encore terminée
        })
    else:
        st.session_state.machine_status[machine] = "Running"
        status_text = "Réparée"
        fault_type = "Reprise du travail"
        
        # Mise à jour de l'heure de fin de la dernière panne enregistrée pour cette machine
        if machine in st.session_state.machine_faults and len(st.session_state.machine_faults[machine]) > 0:
            if st.session_state.machine_faults[machine][-1]["end"] is None:
                st.session_state.machine_faults[machine][-1]["end"] = current_sim_duration

    new_entry = pd.DataFrame([{"Runtime": time_stamp, "Machine": machine, "Type": fault_type, "Source": source, "État": status_text}])
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
        columns=["Runtime", "Machine", "Type", "Source", "État"]
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
st.title("Système de monitoring IA")
st_autorefresh(interval=1000, key="refresh")
# =========================
# 5. Sidebar Settings
# =========================
with st.sidebar:
    st.header("⚙️ Seuils de danger")

    t_limit = st.slider("Température", 1, 120, 100)
    h_limit = st.slider("Humidité", 5, 100, 100)
    p_limit = st.slider("Pression", 1.0, 15.0, 15.0)
    v_limit = st.slider("Vibration", 1.0, 10.0, 10.0)
    c_limit = st.slider("Courant", 1, 50, 50)

# =========================
# 6. Bouton d'actualisation (alternative à while True)
# =========================
if st.button("🔄 Actualiser les données"):
    st.rerun()

# =========================
# 7. Données de fonctionnement
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
    # Données aléatoires pour chaque machine
    # -------------------------
    np.random.seed(hash(machine) % 10000)
    temp = np.random.uniform(65, 5)
    humidity = np.random.uniform(55, 10)
    pressure = np.random.uniform(6, 1.5)
    vibe = np.random.uniform(3, 1)
    current = np.random.uniform(20, 5)

    checks = [
        (temp > t_limit, "temp", "Température", f"{temp:.1f}°C"),
        (humidity > h_limit, "humid", "Humidité", f"{humidity:.1f}%"),
        (pressure > p_limit, "press", "Pression", f"{pressure:.1f} Bar"),
        (vibe > v_limit, "vibe", "Vibration", f"{vibe:.2f} mm/s"),
        (current > c_limit, "curr", "Courant", f"{current:.1f} A")
    ]

    # -------------------------
    # Vérification et alertes
    # -------------------------
    for is_danger, key, label, val in checks:

        if is_danger and can_send_alert(machine, key):
            send_telegram_msg(CONTACTS.get(label, CONTACTS["Général/Secours"]), f"🚨 {machine}\n{label}: {val}")
            
            # Nouvelle ligne chargée de changer l'état automatiquement :
            if st.session_state.machine_status[machine] == "Running":
                toggle_machine(machine, source="Auto 🤖", fault_type=label)

            st.session_state.alerts_sent[machine][key] = True

        elif not is_danger:
            st.session_state.alerts_sent[machine][key] = False

    # -------------------------
    # Calcul de la santé
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
# 🛑 Nouveau code : ajout d'un son d'alarme lorsque la santé passe sous 80 %
# ========================================================

# Liste pour stocker les machines en difficulté lors de cette mise à jour
low_health_machines = [m for m, data in all_data.items() if data["health"] < 81]

if low_health_machines:
    # Lien vers un son d'alarme externe (vous pouvez le remplacer par n'importe quel lien MP3 direct)
    alarm_url = "https://actions.google.com/sounds/v1/alarms/digital_watch_alarm_long.ogg"
    
    # Code HTML masqué pour lire le son automatiquement dès que la santé baisse
    st.components.v1.html(
        f'''
        <audio autoplay style="display:none;">
            <source src="{alarm_url}" type="audio/ogg">
        </audio>
        ''',
        height=0,
    )
    
    # Alerte visuelle affichée en haut de l'écran à côté du son
    st.error(f"🚨 Avertissement : baisse de l'indice de santé sur les machines suivantes : {', '.join(low_health_machines)}")

# ========================================================





# =========================
# 8. Affichage (Dashboard) amélioré
# =========================


st.info(f"⏱️ Runtime: {minutes} minutes {seconds} seconds")


# --- Calcul de l'efficacité et de la stabilité selon l'état réel des machines ---

# 1. Récupération de la liste des machines en fonctionnement uniquement (pas en réparation)
working_machines = [m for m, status in st.session_state.machine_status.items() if status == "Running"]
num_working = len(working_machines)

# 2. Calcul de la santé moyenne des machines en fonctionnement
if num_working > 0:
    avg_health = sum([all_data[m]["health"] for m in working_machines]) / num_working
else:
    avg_health = 0

# 3. Calcul de l'efficacité : influencée par le nombre de machines actives (chaque machine représente 20 % de la capacité de l'usine)
# avec une légère touche aléatoire pour la simulation
factory_efficiency = (num_working / 5) * avg_health + np.random.uniform(-2, 2)

# 4. Calcul de la stabilité : influencée par la santé moyenne globale
factory_stability = avg_health + np.random.uniform(-5, 5)

# Enregistrement des nouvelles données
new_row = pd.DataFrame([{
    "time": int(sim_duration), 
    "Efficacité": max(0, min(100, factory_efficiency)),
    "Stabilité": max(0, min(100, factory_stability))
}])

# Ajout du nouveau point puis conservation des 20 derniers points seulement pour accélérer les performances
st.session_state.performance_data = pd.concat(
    [st.session_state.performance_data, new_row],
    ignore_index=True
).tail(20) # ✅ Cette ligne garantit que la mémoire reste toujours légère


for machine, data in all_data.items():
    status = st.session_state.machine_status[machine]
    health_val = data["health"]
    bg_color = get_health_color(health_val)

    # Début de la carte de la machine
    
    if "Under Repair" in status:
        bg_color = "#fff" # gris

    st.markdown(f'''
        <div class="machine-card" style="background-color: {bg_color}; border-right: 5px solid {bg_color.replace('0.1', '1')};">
    ''', unsafe_allow_html=True)
    
    
    
    col_header, col_btn = st.columns([3, 1])
    with col_header:
        # Coloration de l'état selon son type
        status_color = "#28a745" if "Running" in status else "#dc3545"
        st.markdown(f'<h3>🔧 {machine} | <span style="color:{status_color}">{status}</span></h3>', unsafe_allow_html=True)
    
    with col_btn:
        if st.button(f"Changer l'état", key=f"btn_{machine}"):
            toggle_machine(machine)
            st.rerun()

    if "Under Repair" in status:
        st.warning("⚠️ Cette machine est actuellement en réparation")
    else:
        
        # Affichage de la barre de santé personnalisée
        st.markdown(f'''
            <medium><b>Indice de santé de la machine : {health_val}%</b></medium>
            <div class="health-bar-container">
                <div class="health-bar-fill" style="width: {health_val}%; background-color: {bg_color};"></div>
        ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Affichage des mesures
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("🌡️ Température", f"{data['temp']:.1f}°C")
        c2.metric("💧 Humidité", f"{data['humidity']:.1f}%")
        c3.metric("⚙️ Pression", f"{data['pressure']:.1f} Bar")
        c4.metric("📳 Vibration", f"{data['vibe']:.2f}")
        c5.metric("⚡ Courant", f"{data['current']:.1f}A")
    
    st.markdown('</div>', unsafe_allow_html=True) # Fin de la carte de la machine
    st.write("") # Petit espacement
    st.markdown('</div>', unsafe_allow_html=True)
# =========================
# 9. Charts + Logs
# =========================
col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader("📊 Performance globale (Live Time Series)")

    df = st.session_state.performance_data

    if not df.empty:
        # Tri des données par secondes et définition de l'axe principal
        df_plot = df.sort_values("time").set_index("time")
        
        # Tracé du graphique pour toutes les données de la seconde 0 à maintenant
        st.line_chart(df_plot)
    else:
        st.write("En attente du démarrage de la simulation...")

with col2:
    st.subheader("📋 Journal des pannes")
    st.dataframe(st.session_state.maintenance_log, use_container_width=True, hide_index=True)