import streamlit as st
import requests

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
    "<p class='sub-title'>Saisissez votre numéro de série et choisissez le plan de renouvellement approprié pour finaliser l'opération.</p>",
    unsafe_allow_html=True
)

# URL du service d'envoi d'e-mails (FormSubmit)
FORM_SUBMIT_URL = "https://formsubmit.co/markandreas03@gmail.com"

# Conteneur principal
st.markdown('<div class="renew-container">', unsafe_allow_html=True)

with st.form(key="renew_form", clear_on_submit=False):

    # 1. Numéro de série
    serial_number = st.text_input(
        "Numéro de série (Serial Number) *",
        placeholder="Exemple : XXXX-XXXX-XXXX-XXXX"
    )

    # 2. Durée du renouvellement
    duration = st.radio(
        "Choisissez la durée du renouvellement *",
        [
            "1 mois (1 Month)",
            "6 mois (6 Months)",
            "1 an (1 Year)"
        ],
        index=0
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

    # 3. Méthode de paiement
    payment_method = st.selectbox(
        "Choisissez votre méthode de paiement préférée *",
        [
            "PayPal",
            "Carte bancaire (Stripe)",
            "BaridiMob"
        ]
    )

    # Informations selon le mode de paiement
    screenshot = None

    if payment_method == "BaridiMob":
        st.markdown("""
        <div class="payment-info-box">
            <strong>⚠️ Informations de paiement via BaridiMob :</strong><br>
            Veuillez transférer le montant correspondant en dinars algériens vers le compte suivant :<br>
            <strong>RIP :</strong> 00799999000123456789 (à remplacer par votre véritable compte)<br>
            Après le transfert, veuillez téléverser une capture d'écran du reçu afin de confirmer le paiement.
        </div>
        """, unsafe_allow_html=True)

        screenshot = st.file_uploader(
            "Téléverser une capture d'écran du reçu de paiement (PNG/JPG)",
            type=["jpg", "png", "jpeg"]
        )

    elif payment_method == "PayPal":
        st.info(
            "💡 Votre demande de renouvellement sera envoyée pour validation après avoir cliqué sur le bouton ci-dessous. Assurez-vous que votre compte PayPal est prêt pour le paiement."
        )
    st.markdown("""
    ### Paiement PayPal
    Envoyez le paiement à :
    **moncompte@gmail.com**
    """)

    elif payment_method == "Carte bancaire (Stripe)":
        st.info(
            "💳 Saisissez les informations de votre carte bancaire via la passerelle sécurisée lors du traitement de votre demande."
        )

    # Champs cachés pour FormSubmit
    st.markdown(
        '<input type="hidden" name="_captcha" value="false">',
        unsafe_allow_html=True
    )

    st.markdown(
        f'<input type="hidden" name="_subject" value="Nouvelle demande de renouvellement : {serial_number}">',
        unsafe_allow_html=True
    )

    # Bouton d'envoi
    submit_button = st.form_submit_button(
        label="Confirmer et envoyer la demande de renouvellement"
    )

st.markdown('</div>', unsafe_allow_html=True)

# Traitement de l'envoi
if submit_button:

    if not serial_number:
        st.error("Veuillez d'abord saisir votre numéro de série !")

    elif payment_method == "BaridiMob" and screenshot is None:
        st.error(
            "Veuillez téléverser une preuve de paiement BaridiMob !"
        )

    else:

        payload = {
            "Numéro de série": serial_number,
            "Durée du renouvellement": duration,
            "Prix": price,
            "Méthode de paiement": payment_method
        }

        files = {}

        if screenshot is not None:
            files = {
                "attachment": (
                    screenshot.name,
                    screenshot.getvalue(),
                    screenshot.type
                )
            }

        with st.spinner("Traitement et envoi de votre demande en cours..."):

            try:

                if files:
                    response = requests.post(
                        FORM_SUBMIT_URL,
                        data=payload,
                        files=files
                    )
                else:
                    response = requests.post(
                        FORM_SUBMIT_URL,
                        data=payload
                    )

                if response.status_code == 200:
                    st.success(
                        f"🎉 La demande de renouvellement pour le numéro de série ({serial_number}) a été envoyée avec succès ! Vous recevrez une confirmation dès l'activation de votre abonnement."
                    )
                else:
                    st.error(
                        "Une erreur est survenue lors du traitement de la demande. Veuillez réessayer."
                    )

            except Exception:
                st.error(
                    "Échec de la connexion au serveur d'envoi des données. Veuillez vérifier votre connexion Internet."
                )
