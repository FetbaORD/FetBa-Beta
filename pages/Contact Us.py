import streamlit as st

# Paramètres de la page
st.set_page_config(page_title="Contactez-nous", page_icon="✉️", layout="centered")

# Fonction de lecture et d'application du fichier CSS
def local_css(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Appel de la feuille de style
local_css("style.css")

# Interface : titre de la page
st.markdown("<h1 class='main-title'>Contactez-nous</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Nous serons heureux de recevoir vos questions et vos messages ; nous vous répondrons dans les plus brefs délais.</p>", unsafe_allow_html=True)

# Lien d'envoi FormSubmit avec votre adresse e-mail
FORM_SUBMIT_URL = "https://formsubmit.co/markandreas03@gmail.com"

# Création du formulaire dans un conteneur HTML personnalisé
st.markdown('<div class="contact-container">', unsafe_allow_html=True)

# Utilisation de st.form pour gérer la saisie et l'envoi
with st.form(key="contact_form", clear_on_submit=True):
    
    # Champs de saisie
    name = st.text_input("Nom complet", placeholder="Saisissez votre nom ici...")
    email = st.text_input("Adresse e-mail", placeholder="example@domain.com")
    message = st.text_area("Contenu du message", placeholder="Écrivez votre message ici...", height=150)
    
    # Champ masqué pour éviter le spam (Captcha / anti-spam) de FormSubmit
    st.markdown(f'<input type="hidden" name="_captcha" value="false">', unsafe_allow_html=True)
    
    # Bouton d'envoi
    submit_button = st.form_submit_button(label="Envoyer le message")

st.markdown('</div>', unsafe_allow_html=True)

# Traitement de l'envoi au clic sur le bouton
if submit_button:
    if not email or not message:
        st.error("Veuillez renseigner l'adresse e-mail et le contenu du message !")
    elif "@" not in email:
        st.error("Veuillez saisir une adresse e-mail valide !")
    else:
        # Envoi des données en arrière-plan avec requests, sans redirection de l'utilisateur
        import requests
        
        data = {
            "Name": name,
            "Email": email,
            "Message": message
        }
        
        try:
            response = requests.post(FORM_SUBMIT_URL, data=data)
            if response.status_code == 200:
                st.success("🎉 Votre message a été envoyé avec succès ! Merci de nous avoir contactés.")
            else:
                st.error("Désolé, une erreur est survenue lors de l'envoi du message. Veuillez réessayer plus tard.")
        except Exception as e:
            st.error("Impossible de se connecter au serveur, vérifiez votre connexion Internet.")
