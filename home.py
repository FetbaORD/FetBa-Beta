import streamlit as st
from datetime import datetime
import pandas as pd
from streamlit_autorefresh import st_autorefresh 


    
# 1. Paramètres de la page
st.set_page_config(
    page_title="Centre de Contrôle Industriel par IA",
    layout="wide",
    page_icon=":material/factory:"
)

# Chargement de la feuille de style CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 2. Masquer le menu latéral tant que le produit n'est pas activé
if "is_activated" not in st.session_state or not st.session_state.is_activated:
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {display: none;}
            [data-testid="stSidebar"] {display: none;}
        </style>
    """, unsafe_allow_html=True)

# ----------------------------------------------------------------
# 3. Récupération de la base des clés et des dates depuis Google Sheets (en ligne)
# ----------------------------------------------------------------
@st.cache_data(ttl=600) # 👈 Mise en cache des données pendant 10 minutes (600 s) pour économiser la connexion et accélérer l'application
def load_licenses_from_sheets():
    try:
        sheet_url = st.secrets["public_gsheet_url"]
        if "/d/" in sheet_url:
            sheet_id = sheet_url.split("/d/")[1].split("/")[0]
        else:
            sheet_id = sheet_url
            
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        df = pd.read_csv(csv_url, dtype=str)
        
        db = {}
        for _, row in df.iterrows():
            if pd.isna(row['key']) or pd.isna(row['expire_date']):
                continue
                
            key_name = str(row['key']).strip()
            db[key_name] = {
                "expire_date": str(row['expire_date']).strip(),
                "max_devices": int(row['max_devices']) if 'max_devices' in row and not pd.isna(row['max_devices']) else 2,
                "used_devices": int(row['used_devices']) if 'used_devices' in row and not pd.isna(row['used_devices']) else 0
            }
        return db
    except Exception as e:
        print(f"Error connecting to Google Sheets: {e}")
        st.error("Erreur de connexion au serveur d'activation en ligne. Veuillez vérifier votre connexion Internet et réessayer plus tard.")
        st.stop()


if "is_activated" not in st.session_state:
    st.session_state.is_activated = False

# Fonction de vérification de la clé et de sa date d'expiration
def verify_key(key):
    db = load_licenses_from_sheets()
    
    if key in db:
        key_info = db[key]
        expire_date = datetime.strptime(key_info["expire_date"], '%Y-%m-%d')
        current_date = datetime.now()
        
        if current_date > expire_date:
            st.error(f"Cette clé a expiré le : {key_info['expire_date']}")
            return
            
        if key_info["used_devices"] >= key_info["max_devices"]:
            st.error("Cette clé est déjà utilisée sur le nombre maximal d'appareils autorisés !")
            return
            
        st.session_state.is_activated = True
        st.session_state.license_expiry = key_info["expire_date"]
        st.success("Activation réussie !")
        st.rerun()
    else:
        st.error(" Clé d'activation invalide !")


# 1. Définition de la fenêtre contextuelle hors des conditions (pour qu'elle soit appelable)
@st.dialog("📱 Support & Achat de Clé", width="medium")
def show_contact_dialog():
    st.html("""
    <p style='color: #666; font-size: 14px; margin-bottom: 20px;'>
        Choisissez votre moyen de communication préféré pour obtenir votre clé d'activation rapidement :
    </p>
    
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    
    <div class="contact-card-container">
        <a href="mailto:Markandreas03@gmail.com" target="_blank" class="contact-card email-card">
            <span class="material-icons icon-box">email</span>
            <div class="contact-text">
                <span class="contact-label">E-mail Officiel</span>
                <span class="contact-value">Markandreas03@gmail.com</span>
            </div>
            <span class="material-icons arrow-box">open_in_new</span>
        </a>
        
        <a href="https://t.me/CCryptomic" target="_blank" class="contact-card telegram-card">
            <span class="material-icons icon-box">telegram</span>
            <div class="contact-text">
                <span class="contact-label">Telegram Support</span>
                <span class="contact-value">@CCryptomic</span>
            </div>
            <span class="material-icons arrow-box">open_in_new</span>
        </a>
        
        <a href="https://wa.me/213541445824" target="_blank" class="contact-card whatsapp-card">
            <span class="material-icons icon-box">chat</span>
            <div class="contact-text">
                <span class="contact-label">WhatsApp Business</span>
                <span class="contact-value">+213 5 41 44 58 24</span>
            </div>
            <span class="material-icons arrow-box">open_in_new</span>
        </a>
    </div>
    """)


# ----------------------------------------------------------------
# 4. Écran de verrouillage de l'application (col_right est entièrement dans le if)
# ----------------------------------------------------------------
if not st.session_state.is_activated:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>🔒 Activation du Système</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Le système de contrôle industriel est protégé. Veuillez activer votre produit.</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.subheader(":material/vpn_key: Activation du Produit")
        with st.container(border=True):
# Création du formulaire (Form) pour gérer la touche Entrée
            with st.form(key="activation_form", clear_on_submit=False):
                
                # Champ de saisie principal masqué (mot de passe) dans le formulaire
                input_key = st.text_input("Clé de produit", type="password", placeholder="XXXX-XXXX-XXXX")
                st.write("") 
                
                # Colonnes internes pour centrer le bouton
                sub_col1, sub_col2, sub_col3 = st.columns([1, 1.5, 1])
                with sub_col2:
                    submit_button = st.form_submit_button("Activer le Système", type="primary", use_container_width=False)
                    
                    if submit_button:
                        if input_key.strip() != "":
                            verify_key(input_key.strip())
                        else:
                            st.error("Veuillez saisir une clé valide !")
            
            st.write("") 
            st.caption("Note: La clé est valide pour une utilisation sur deux appareils maximum.")

	
	# col_right est placé ici (dans la portée du if)
    with col_right:
        st.subheader(":material/shopping_cart: Achat d'une Clé d'Activation")
        with st.container(border=True):
            st.markdown("""
            **Besoin d'une clé de produit valide ?** Vous pouvez obtenir une nouvelle clé d'activation immédiatement en contactant notre service commercial ou via notre plateforme sécurisée.
            """)
            st.write("") 
            
            sub_b1, sub_b2, sub_b3 = st.columns([1, 1.5, 1])
            with sub_b2:
                if st.button("Acheter une Clé / Support", type="secondary",use_container_width=False):
                    st.toast("💡 Redirection vers le support commercial...", icon="ℹ️")
                    show_contact_dialog() 
                    
            st.write("")
            st.caption("Pour toute urgence, contactez : Markandreas03@gmail.com")


# =========================================================
    # Page des tarifs (Pricing) sous la fenêtre d'activation et de commande
    # =========================================================
    st.markdown("---")
    st.markdown("""
    <div class="pricing-header">
        <h2 style='text-align: center; color: #1E3A8A; display: flex; align-items: center; justify-content: center; gap: 10px;'>
			<span class="material-icons" style="font-size: 32px; color: #1E3A8A;">workspace_premium</span>
			Plans d'abonnement flexibles
        </h2>
		<p style='text-align: center; color: #666; max-width: 600px; margin: 0 auto;'>
            Choisissez le forfait qui correspond le mieux à vos besoins industriels. Obtenez une clé instantanée après l'achat.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
# Icônes Material pour les cases de fonctionnalités dans les cartes
    st.markdown('<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">', unsafe_allow_html=True)
    st.markdown("""
    <div class="pricing-container">
        <div class="pricing-card">
            <div>
                <span class="material-icons plan-icon" style="color: #f59e0b;">bolt</span>
                <div class="plan-name">Mensuel</div>
                <div class="plan-price">10$<span> / mois</span></div>
                <div style="height: 25px;"></div>
                <ul class="plan-features">
                    <li><i class="material-icons">check_circle</i> Accès complet au système</li>
                    <li><i class="material-icons">check_circle</i> Support sur 2 appareils</li>
                    <li><i class="material-icons">check_circle</i> Mises à jour gratuites</li>
                    <li class="disabled"><i class="material-icons">cancel</i> Support prioritaire 24/7</li>
                </ul>
            </div>
        </div><div class="pricing-card">
            <div>
                <span class="material-icons plan-icon" style="color: #3b82f6;">speed</span>
                <div class="plan-name">6 Mois</div>
                <div class="plan-price">45$<span> / 6 mois</span></div>
                <span class="save-badge">Économisez 25%</span>
                <ul class="plan-features">
                    <li><i class="material-icons">check_circle</i> Accès complet au système</li>
                    <li><i class="material-icons">check_circle</i> Support sur 2 appareils</li>
                    <li><i class="material-icons">check_circle</i> Mises à jour gratuites</li>
                    <li class="disabled"><i class="material-icons">cancel</i> Support prioritaire 24/7</li>
                </ul>
            </div>
        </div><div class="pricing-card popular">
            <span class="popular-badge">Plus Populaire</span>
            <div>
                <span class="material-icons plan-icon" style="color: #1e3a8a;">military_tech</span>
                <div class="plan-name">Annuel</div>
                <div class="plan-price">80$<span> / an</span></div>
                <span class="save-badge">Économisez 33%</span>
                <ul class="plan-features">
                    <li><i class="material-icons">check_circle</i> Accès complet au système</li>
                    <li><i class="material-icons">check_circle</i> Support sur 2 appareils</li>
                    <li><i class="material-icons">check_circle</i> Mises à jour gratuites</li>
                    <li><i class="material-icons">check_circle</i> Support prioritaire 24/7</li>
                </ul>
            </div>
        </div>
    </div>
    <br><br>
    """, unsafe_allow_html=True)
    
    # Bouton supplémentaire sous les cartes pour contacter directement le support
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        if st.button("Demander un abonnement maintenant", icon=":material/shopping_bag:", key="pricing_btn", use_container_width=False):
            show_contact_dialog()

    st.stop()  # Arrête l'exécution ici pour protéger le reste de l'application
# =========================================================
# Contenu principal (visible uniquement après une activation réussie)
# =========================================================


# Rafraîchissement automatique
st_autorefresh(interval=2000, key="refresh_clock")

st.title(":material/factory: Centre de Contrôle Industriel par IA")


# =========================================================================
# Logo de la plateforme en haut de la barre latérale
# =========================================================================
st.sidebar.markdown(
    """
    <div style="display: flex; flex-direction: column; align-items: flex-start; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #e0e0e0;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <img src="https://raw.githubusercontent.com/FetbaORD/FetBa-Beta/refs/heads/app/%E2%80%94Pngtree%E2%80%94task%20schedule%20with%20stopwatch%20icon_20956305.png" width="40" style="object-fit: contain;">
            <h1 style="font-family: 'Poppins', 'Helvetica Neue', sans-serif; font-size: 24px; font-weight: 700; color: #1E3A8A; margin: 0; padding: 0;">
                FetBa Platform
            </h1>
        </div>
        <p style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 11px; color: #6B7280; margin: 5px 0 0 0; line-height: 1.3;">
            Une plateforme professionnelle pour la planification de la production
        </p>
    </div>
    """,
    unsafe_allow_html=True
)



# =========================================================================
# Calcul du temps restant avant l'expiration de la licence
# =========================================================================
try:
    # Conversion de la date (le format doit être YYYY-MM-DD)
    expiry_date = datetime.strptime(st.session_state.license_expiry, "%Y-%m-%d")
    now = datetime.now()
    
    # Calcul de l'écart de temps
    time_remaining = expiry_date - now
    days_remaining = time_remaining.days
    
    # Préparation du texte et de l'icône selon l'état de la licence
    if days_remaining > 0:
        license_status_text = f":material/hourglass_top: Temps restant : {days_remaining} jours"
        # Moins de 7 jours : avertissement jaune, sinon succès vert
        sidebar_status = st.sidebar.warning if days_remaining <= 7 else st.sidebar.success
    else:
        license_status_text = ":material/gpp_bad: Licence expirée !"
        sidebar_status = st.sidebar.error
        
except Exception:
    license_status_text = ":material/hourglass_empty: Temps restant : Indisponible"
    sidebar_status = st.sidebar.info

# =========================================================================
# Affichage des données dans la barre latérale avec les icônes Material
# =========================================================================

# Case 1 : date d'expiration de la licence
sidebar_status(f":material/verified_user: Version sous licence jusqu'au : {st.session_state.license_expiry}")

# Case 2 : temps restant en jours (couleur selon l'état)
st.sidebar.info(license_status_text)


st.markdown("### Système intelligent de surveillance et d'ordonnancement d'usine")
st.markdown("---")

# Panneau de contrôle supérieur
col_status, col_timer, col_action = st.columns([1, 1, 1])

with col_status:
    st.metric(":material/gpp_good: État du système", "En ligne et protégé")

with col_timer:
    if "sim_start_time" in st.session_state:
        sim_duration = (datetime.now() - st.session_state.sim_start_time).total_seconds()
        mins, secs = divmod(int(sim_duration), 60)
        st.metric(":material/hourglass_top: Temps de simulation", f"{mins:02d}:{secs:02d}")
    else:
        st.metric(":material/hourglass_empty: Temps de simulation", "00:00")

with col_action:
    st.markdown('<div style="text-align: right; direction: rtl;">', unsafe_allow_html=True)
    if st.button(":material/rocket_launch: Démarrer la simulation de production"):
        st.session_state.sim_start_time = datetime.now()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# Reste de la page (architecture, aperçu...)
col1, col2 = st.columns(2)
with col1:
    st.subheader(":material/analytics: Aperçu rapide")
    st.info("""
    🔹 **Système de surveillance** - Suivi des machines en temps réel  
    - Alertes capteurs (température, vibration...)  
    - Journal des pannes (machine, heure de début, durée)  
    """)

with col2:
    st.subheader(":material/schema: Architecture du système")
    st.code("""
Interface utilisateur (Streamlit)
        ↓
Surveillance ←→ Ordonnancement (GA)
        ↓
    Alertes ←→ Journaux
    """)

st.caption("Système industriel IA v1.0 | Accès réservé aux utilisateurs autorisés")
