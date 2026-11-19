import streamlit as st
import sqlite3
import re
import bcrypt
from streamlit_gsheets import GSheetsConnection

# =========================================================================
# 2. INTERFACES UTILISATEUR (DESIGN DESIGN AMÉLIORÉ)
# =========================================================================

def load_css():
    try:
        with open("style.css", "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass




# =========================================================================
# 1. GESTION DE LA BASE DE DONNÉES ET SÉCURITÉ DES MOTS DE PASSE (BCRYPT)
# =========================================================================

def get_db_connection():
    conn = sqlite3.connect("project_db.db")
    return conn

def create_usertable():
    conn = get_db_connection()
    c = conn.cursor()
    # La table prend en charge l'ajout automatique des nouvelles colonnes si elles n'existent pas
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT UNIQUE, password TEXT)')
    try:
        c.execute('ALTER TABLE userstable ADD COLUMN email TEXT')
        c.execute('ALTER TABLE userstable ADD COLUMN phone TEXT')
    except sqlite3.OperationalError:
        pass  # Les colonnes existent déjà : rien à faire
    conn.commit()
    conn.close()

def hash_password(password):
    # Conversion du hash en texte (str) pour éviter les problèmes avec Python et sqlite3
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed_password):
    # Si le hash vient de Google Sheets sous forme de texte (str), on le convertit en octets (bytes)
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    
    # Conversion également du mot de passe saisi en octets
    if isinstance(password, str):
        password = password.encode('utf-8')
        
    try:
        return bcrypt.checkpw(password, hashed_password)
    except Exception:
        # Protège l'application si le hash stocké est corrompu ou vide
        return False



# Connexion à Google Sheets (les paramètres sont lus automatiquement depuis les Secrets)
def get_sheets_connection():
    # Passage explicite de la classe importée, comme l'exige streamlit_gsheets
    return st.connection("gsheets", type=GSheetsConnection)




def add_user(username, password, email="", phone=""):
    conn = get_sheets_connection()
    
    # 1. Lecture des données actuelles en précisant la feuille de calcul
    try:
        df = conn.read(worksheet="Sheet1", ttl=0) 
    except Exception:
        import pandas as pd
        df = pd.DataFrame(columns=["username", "password", "email", "phone"])
    
    # Nettoyage des noms existants avant la vérification pour éviter les doublons dus aux espaces
    if not df.empty and "username" in df.columns:
        df['username'] = df['username'].astype(str).str.strip().str.lower() # 👈 .str.lower() ajouté
    
    # Vérifier que le nom d'utilisateur n'existe pas déjà après nettoyage
    if username.strip().lower() in df["username"].values: # 👈 .lower() ajouté
        return False
        
    # 2. Chiffrement du mot de passe et préparation des nouvelles données
    hashed_pass = hash_password(password)
    new_data = {
        "username": [username.strip().lower()], # 👈 .lower() ajouté ici aussi
        "password": [hashed_pass.strip()],
        "email": [email.strip()],
        "phone": [phone.strip()]
    }
    import pandas as pd
    new_df = pd.DataFrame(new_data)
    
    # Fusion de la nouvelle ligne avec les données précédentes
    updated_df = pd.concat([df, new_df], ignore_index=True)
    
    # 3. Mise à jour de la feuille de calcul indiquée
    conn.update(worksheet="Sheet1", data=updated_df)
    return True

def login_user(username, password):
    conn = get_sheets_connection()
    try:
        # st.spinner remplace le texte par défaut par un texte personnalisé
        with st.spinner("Vérification des informations saisies..."):
            st.cache_data.clear()
            df = conn.read(worksheet="Sheet1", ttl=0, show_spinner=False)
    except Exception as e:
        st.error(f"Erreur de lecture: {e}")
        return False
        
    if df.empty or "username" not in df.columns or "password" not in df.columns:
        return False

    # Nettoyage complet des colonnes des espaces superflus (important pour Google Sheets)
    df['username'] = df['username'].astype(str).str.strip().str.lower() # 👈 .str.lower() ajouté
    df['password'] = df['password'].astype(str).str.strip()
    
    clean_username = str(username).strip().lower() # 👈 .lower() ajouté



    
    # Recherche de la ligne de l'utilisateur
    user_row = df[df["username"] == clean_username]
    
    if not user_row.empty:
        # Récupération du hash stocké
        hashed_password = user_row.iloc[0]["password"]
        
        # Appel de la fonction de vérification
        return check_password(password, hashed_password)
        
    return False


# =====================================================================================

def sign_in_page():
    load_css() 
    
    title_html = """
    <p class="main-title">
        <i class="material-icons" style="vertical-align: middle; margin-right: 8px;">login</i>Connexion
    </p>
    """
    st.markdown(title_html, unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown('<p class="form-label">Connectez-vous pour continuer</p>', unsafe_allow_html=True)
        
        username = st.text_input("Nom d'utilisateur", key="login_user", placeholder="Entrez votre nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password", key="login_pass", placeholder="••••••••")
                
        st.write("") 
        
        col_left, col_center, col_right = st.columns([2, 1.5, 2])
        
        with col_center:
            login_button = st.button("Se connecter", type="primary")
        
        clean_user_input = username.strip().lower() # Cette ligne doit précéder la condition
        if login_button or (clean_user_input and password and st.session_state.login_pass):
            clean_user_input = username.strip().lower()
            if login_user(clean_user_input, password):
                st.session_state.logged_in = True
                st.session_state.username = clean_user_input
                st.success("Connexion réussie ! Redirection en cours...")
                st.rerun()
            else:
                if login_button or (username and password):
                    st.error("Nom d'utilisateur ou mot de passe incorrect.")



def sign_up_page():
    load_css() 
    
    signup_html = """
    <p class="main-title">
        <i class="material-icons" style="vertical-align: middle; margin-right: 8px;">person_add</i>Rejoignez-nous
    </p>
    """
    st.markdown(signup_html, unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown('<p class="form-label">Créez votre nouveau compte dès maintenant</p>', unsafe_allow_html=True)
        
        # 1. Champ nom d'utilisateur
        new_username = st.text_input("Choisissez un nom d'utilisateur *", key="reg_user", placeholder="Ex: admin123")
        clean_new_username = new_username.strip().lower() # 👈 Nouvelle ligne
        # 2. Champ e-mail avec validation en couleur
        email = st.text_input("Adresse e-mail *", key="reg_email", placeholder="Ex: exemple@mail.com")
        is_email_valid = False
        if email: # La vérification ne démarre que si l'utilisateur a saisi quelque chose
            if re.match(r"[^@]+@[^@]+\.[^@]+", email):
                st.markdown('<p style="color: #28a745; font-size: 13px; margin-top: -10px;">Format de l\'e-mail valide</p>', unsafe_allow_html=True)
                is_email_valid = True
            else:
                st.markdown('<p style="color: #dc3545; font-size: 13px; margin-top: -10px;">Format invalide (ex: nom@domaine.com)</p>', unsafe_allow_html=True)
        
        # 3. Champ téléphone avec validation en couleur
        phone = st.text_input("Numéro de téléphone *", key="reg_phone", placeholder="Ex: +33612345678")
        is_phone_valid = False
        if phone:
            if re.match(r"^\+?[0-9\s]{7,15}$", phone):
                st.markdown('<p style="color: #28a745; font-size: 13px; margin-top: -10px;">Numéro de téléphone valide</p>', unsafe_allow_html=True)
                is_phone_valid = True
            else:
                st.markdown('<p style="color: #dc3545; font-size: 13px; margin-top: -10px;">Uniquement des chiffres (7 à 15 caractères)</p>', unsafe_allow_html=True)
        
        # 4. Champs de mot de passe
        new_password = st.text_input("Choisissez un mot de passe *", type="password", key="reg_pass", placeholder="••••••••")
        confirm_password = st.text_input("Confirmez le mot de passe *", type="password", key="reg_pass_conf", placeholder="••••••••")
        
        # Vérification immédiate de la correspondance des mots de passe
        is_password_matching = False
        if new_password and confirm_password:
            if new_password == confirm_password:
                st.markdown('<p style="color: #28a745; font-size: 13px; margin-top: -10px;">Les mots de passe correspondent</p>', unsafe_allow_html=True)
                is_password_matching = True
            else:
                st.markdown('<p style="color: #dc3545; font-size: 13px; margin-top: -10px;">Les mots de passe ne correspondent pas</p>', unsafe_allow_html=True)

        st.write("")
        
        col1, col2, col3 = st.columns([2, 1.5, 2])
        with col2:
            signup_button = st.button("Créer le compte", type="primary")
        
        # Validation par la touche Entrée ou le bouton, avec vérification complète
        if signup_button or (clean_new_username and email and phone and new_password and st.session_state.reg_pass_conf):
            
            # Vérifier d'abord que tous les champs obligatoires sont remplis
            if not clean_new_username or not email or not phone or not new_password or not confirm_password:
                st.warning("Veuillez remplir tous les champs obligatoires.")
            
            # Vérifier que toutes les saisies ont réussi la validation (vert)
            elif not is_email_valid:
                st.error("Veuillez corriger l'adresse e-mail avant validation.")
                
            elif not is_phone_valid:
                st.error("Veuillez corriger le numéro de téléphone avant validation.")
                
            elif not is_password_matching:
                st.error("Les mots de passe doivent être identiques.")
            
            else:
                # Si tout est rempli et valide, l'inscription est effectuée
                if add_user(clean_new_username, new_password, email, phone):
                    st.success("Compte créé avec succès ! Vous pouvez maintenant passer à la page de connexion.")
                else:
                    st.error("Ce nom d'utilisateur est déjà pris. Veuillez en choisir un autre.")
