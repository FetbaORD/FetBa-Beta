import streamlit as st
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


# Configuration de la page
st.set_page_config(page_title="Renouvellement d'abonnement", page_icon="🔄", layout="centered")

# Fonction pour charger le fichier CSS
def local_css(file_name):
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

local_css("style.css")

# Titre de la page
st.markdown("<h1 class='main-title'>Renouvellement d'abonnement | Order Renew</h1>", unsafe_allow_html=True)
st.markdown(
    "<p class='sub-title'>Saisissez votre numéro de série, choisissez votre mode de paiement et envoyez votre preuve de paiement.</p>",
    unsafe_allow_html=True
)

# URL du service d'envoi d'e-mails (FormSubmit)
FORM_SUBMIT_URL = "https://formsubmit.co/markandreas03@gmail.com"

# Conteneur principal visuel
st.markdown('<div class="renew-container">', unsafe_allow_html=True)

# --- Les champs nécessitant une mise à jour dynamique sont placés hors de st.form pour éviter les problèmes de Streamlit ---

# 1. Numéro de série
serial_number = st.text_input(
    "Numéro de série (Serial Number) *",
    placeholder="Exemple : XXXX-XXXX-XXXX-XXXX"
)

# À placer juste sous le champ Numéro de série :
email = st.text_input(
    "Votre adresse e-mail *",
    placeholder="Exemple : client@gmail.com"
)


# 2. Durée du renouvellement (modification : ajout de la disposition horizontale)
duration = st.radio(
    "Choisissez la durée du renouvellement *",
    ["1 mois (1 Month)", "6 mois (6 Months)", "1 an (1 Year)"],
    index=0,
    horizontal=True  # Cette ligne place les boutons côte à côte
)

# Calcul du prix
if duration == "1 mois (1 Month)":
    price = "8$"
elif duration == "6 mois (6 Months)":
    price = "40$"
else:
    price = "70$"

# Affichage du prix
st.markdown(
    f'<div class="price-tag">Montant total à payer : {price}</div>',
    unsafe_allow_html=True
)

# 3. Sélection de la Méthode de paiement (mise à jour dynamique instantanée)
payment_method = st.selectbox(
    "Choisissez votre méthode de paiement préférée *",
    ["BaridiMob", "RedotPay", "PayPal"]
)

# Affichage de vos informations de paiement selon le choix du client
if payment_method == "BaridiMob":
    st.markdown("""
    <div class="payment-info-box" style="background-color: #fff4e6; border-left: 5px solid #ff922b; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
        <strong style="color: #d9480f;">CCP / BaridiMob :</strong><br>
        Veuillez effectuer le virement CCP ou via l'application BaridiMob vers :<br>
        • <strong>RIP :</strong> 00799999002904112209 (À remplacer par votre RIP)<br>
        • <strong>Nom :</strong> Mohamed Bachir Habchi
    </div>
    """, unsafe_allow_html=True)

elif payment_method == "RedotPay":
    st.markdown("""
    <div class="payment-info-box" style="background-color: #e8f7ff; border-left: 5px solid #339af0; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
        <strong style="color: #1c7ed6;">RedotPay :</strong><br>
        Veuillez envoyer le montant exact en USDT ou fiat vers votre compte RedotPay :<br>
        • <strong>RedotPay ID :</strong> 1072988159 <br>
        • <strong>Adresse Crypto (Optionnel) :</strong> Adresse de votre portefeuille si nécessaire
    </div>
    """, unsafe_allow_html=True)

elif payment_method == "PayPal":
    st.markdown("""
    <div class="payment-info-box" style="background-color: #f3f0ff; border-left: 5px solid #845ef7; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
        <strong style="color: #6741d9;">PayPal :</strong><br>
        Veuillez envoyer le paiement en mode "Proches/Amis" (Family and Friends) à l'adresse suivante :<br>
        • <strong>Email PayPal :</strong> markandreas03@gmail.com
    </div>
    """, unsafe_allow_html=True)


# Champ de téléversement de la preuve (s'affiche désormais correctement pour tous les modes de paiement)
screenshots = st.file_uploader(
    "Téléverser une capture d'écran comme preuve de paiement (PNG/JPG) *",
    type=["jpg", "png", "jpeg"],
    accept_multiple_files=True  # Activation du téléversement multiple
)

st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)

# Bouton d'envoi final indépendant pour envoyer toutes les données à votre e-mail
submit_button = st.button(label="Confirmer et envoyer la demande de renouvellement")

st.markdown('</div>', unsafe_allow_html=True)


# --- Traitement des données et envoi au clic sur le bouton ---
# --- Traitement des données et envoi via SMTP ---
if submit_button:
    if not serial_number:
        st.error("Veuillez d'abord saisir votre numéro de série !")
    elif not email:
        st.error("Veuillez saisir votre adresse e-mail !")
    elif not screenshots:
        st.error("Veuillez téléverser au moins une preuve de paiement !")
    else:
        with st.spinner("Envoi de votre demande en cours..."):
            try:
                # 1. Paramètres du serveur et de l'e-mail (mettez vos informations ici)
                SENDER_EMAIL = "markandreas03@gmail.com"
                # Mettez ici les 16 caractères obtenus auprès de Google (sans espaces)
                SENDER_PASSWORD = "lwks dykm swqe sexf" 
                RECEIVER_EMAIL = "markandreas03@gmail.com"

                # 2. Création de la structure du message électronique
                msg = MIMEMultipart()
                msg['From'] = SENDER_EMAIL
                msg['To'] = RECEIVER_EMAIL
                msg['Subject'] = f"🚀 Nouvelle demande de renouvellement : {serial_number}"

                # Corps du message (HTML pour un rendu structuré)
                body = f"""
                <h3>Nouvelle Demande de Renouvellement</h3>
                <p><b>Numéro de série :</b> {serial_number}</p>
                <p><b>Email Client :</b> {email}</p>
                <p><b>Durée :</b> {duration}</p>
                <p><b>Montant :</b> {price}</p>
                <p><b>Méthode de paiement :</b> {payment_method}</p>
                """
                msg.attach(MIMEText(body, 'html', 'utf-8'))

                # 3. Joindre les images téléversées (fichiers multiples)
                for file in screenshots:
                    part = MIMEBase('application', "octet-stream")
                    part.set_payload(file.getvalue())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename="{file.name}"')
                    msg.attach(part)

                # 4. Connexion au serveur Gmail et envoi sécurisé
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()  # Chiffrement de la connexion
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
                server.quit()

                st.success(f"🎉 Super ! La demande pour {serial_number} a été envoyée avec succès directement à votre boîte mail.")

            except Exception as e:
                st.error(f"Une erreur est survenue lors de l'envoi direct : {str(e)}")
