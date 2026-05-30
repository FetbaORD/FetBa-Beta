import streamlit as st
import sqlite3
import bcrypt

# =========================================================================
# 1. GESTION DE LA BASE DE DONNÉES ET SÉCURITÉ DES MOTS DE PASSE (BCRYPT)
# =========================================================================

# Connexion à la base de données SQLite (Se crée automatiquement sous le nom project_db.db)
def get_db_connection():
    conn = sqlite3.connect("project_db.db")
    return conn

# Création de la table des utilisateurs si elle n'existe pas déjà
def create_usertable():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT UNIQUE, password TEXT)')
    conn.commit()
    conn.close()

# Fonction pour hacher le mot de passe de manière sécurisée
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Fonction pour vérifier le mot de passe lors de la connexion
def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

# Fonction pour ajouter un nouvel utilisateur
def add_user(username, password):
    create_usertable()
    conn = get_db_connection()
    c = conn.cursor()
    hashed_pass = hash_password(password)
    try:
        c.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (username, hashed_pass))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Nom d'utilisateur déjà existant
    finally:
        conn.close()

# Fonction pour vérifier les identifiants de connexion
def login_user(username, password):
    create_usertable()
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT password FROM userstable WHERE username = ?', (username,))
    data = c.fetchone()
    conn.close()
    
    if data:
        # Comparaison du mot de passe saisi avec le hash stocké en base de données
        return check_password(password, data[0])
    return False


# =========================================================================
# 2. INTERFACES UTILISATEUR (DESIGN DESIGN AMÉLIORÉ)
# =========================================================================

def load_css():
    """Fonction pour lire le fichier de style externe et l'injecter dans Streamlit"""
    try:
        with open("style.css", "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass



# 1. نقوم بإنشاء دالة صغيرة لتنفيذ عملية تسجيل الدخول
def trigger_login():
    # نتحقق من البيانات مباشرة من الـ session_state الخاص بالحقول
    user = st.session_state.login_user
    passw = st.session_state.login_pass
    
    if login_user(user, passw):
        st.session_state.logged_in = True
        st.session_state.username = user
        # سنستخدم st.toast أو نترك النجاح يظهر عند إعادة التشغيل
        st.session_state.login_success = True 
        st.rerun()
    else:
        st.session_state.login_error = True

def sign_in_page():
    load_css() # Chargement du style CSS
    
    title_html = """
    <p class="main-title">
        <i class="material-icons" style="vertical-align: middle; margin-right: 8px;">login</i>Connexion
    </p>
    """
    st.markdown(title_html, unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown('<p class="form-label">Connectez-vous pour continuer</p>', unsafe_allow_html=True)
        
        # 2. أضفنا on_change هنا: عندما يضغط Enter في حقل اليوزر أو الباسورد سيتنفذ تسجيل الدخول فوراً
        username = st.text_input("Nom d'utilisateur", key="login_user", placeholder="Entrez votre nom d'utilisateur", on_change=trigger_login)
        password = st.text_input("Mot de passe", type="password", key="login_pass", placeholder="••••••••", on_change=trigger_login)
                
        st.write("") 
        
        col_left, col_center, col_right = st.columns([1, 1.5, 1])
        
        with col_center:
            # 3. 👈 زرّك الأصلي كما هو تماماً (لم نغير فيه حرفاً واحداً لضمان بقاء الستايل)
            if st.button("Se connecter", type="primary"):
                if login_user(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("Connexion réussie ! Redirection en cours...")
                    st.rerun()
                else:
                    st.error("Nom d'utilisateur ou mot de passe incorrect.")
        
        # إظهار الأخطاء أو النجاح القادم من ضغطة الـ Enter
        if st.session_state.get('login_error'):
            st.error("Nom d'utilisateur ou mot de passe incorrect.")
            del st.session_state.login_error # تنظيف الحالة




def sign_up_page():
    load_css() # Chargement du style CSS
    
    # Titre avec icône officielle Google Material Icons (person_add)
    signup_html = """
    <p class="main-title">
        <i class="material-icons" style="vertical-align: middle; margin-right: 8px;">person_add</i>Rejoignez-nous
    </p>
    """
    st.markdown(signup_html, unsafe_allow_html=True)
    
    # Conteneur (Card) pour structurer l'interface d'inscription
    with st.container(border=True):
        st.markdown('<p class="form-label">Créez votre nouveau compte dès maintenant</p>', unsafe_allow_html=True)
        
        new_username = st.text_input("Choisissez un nom d'utilisateur", key="reg_user", placeholder="Ex: admin123")
        new_password = st.text_input("Choisissez un mot de passe", type="password", key="reg_pass", placeholder="••••••••")
        confirm_password = st.text_input("Confirmez le mot de passe", type="password", key="reg_pass_conf", placeholder="••••••••")
        
        st.write("")
        
        # Centrage du bouton à l'intérieur du conteneur via 3 sous-colonnes
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            if st.button("Créer le compte", type="primary"):
                if not new_username or not new_password:
                    st.warning("Veuillez remplir tous les champs obligatoires.")
                elif new_password != confirm_password:
                    st.error("Les mots de passe ne correspondent pas.")
                else:
                    if add_user(new_username, new_password):
                        st.success("Compte créé avec succès ! Vous pouvez maintenant passer à la page de connexion.")
                    else:
                        st.error("Ce nom d'utilisateur est déjà pris. Veuillez en choisir un autre.")
