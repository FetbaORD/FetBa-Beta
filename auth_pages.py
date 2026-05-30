import streamlit as st
import sqlite3
import re
import bcrypt

# =========================================================================
# 1. GESTION DE LA BASE DE DONNÉES ET SÉCURITÉ DES MOTS DE PASSE (BCRYPT)
# =========================================================================

def get_db_connection():
    conn = sqlite3.connect("project_db.db")
    return conn

def create_usertable():
    conn = get_db_connection()
    c = conn.cursor()
    # تم تعديل الجدول ليدعم إضافة الأعمدة الجديدة تلقائياً إذا لم تكن موجودة
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT UNIQUE, password TEXT)')
    try:
        c.execute('ALTER TABLE userstable ADD COLUMN email TEXT')
        c.execute('ALTER TABLE userstable ADD COLUMN phone TEXT')
    except sqlite3.OperationalError:
        pass # الأعمدة موجودة مسبقاً فلا داعي لفعل شيء
    conn.commit()
    conn.close()

def hash_password(password):
    # ✨ التعديل السحري هنا: تحويل الهاش إلى نص (str) لتجنب مشاكل بايثون و sqlite3
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed_password):
    # التأكد من عمل encode للهاش المخزن إذا كان نصاً
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

def add_user(username, password, email="", phone=""):
    create_usertable()
    conn = get_db_connection()
    c = conn.cursor()
    hashed_pass = hash_password(password)
    try:
        # 📝 الآن نقوم بحفظ الإيميل والهاتف أيضاً بنجاح في قاعدة البيانات
        c.execute('INSERT INTO userstable(username, password, email, phone) VALUES (?,?,?,?)', 
                  (username, hashed_pass, email, phone))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  
    finally:
        conn.close()

def login_user(username, password):
    create_usertable()
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT password FROM userstable WHERE username = ?', (username,))
    data = c.fetchone()
    conn.close()
    
    if data:
        return check_password(password, data[0])
    return False


# =========================================================================
# 2. INTERFACES UTILISATEUR (DESIGN DESIGN AMÉLIORÉ)
# =========================================================================

def load_css():
    try:
        with open("style.css", "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

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
        
        col_left, col_center, col_right = st.columns([1, 1.5, 1])
        
        with col_center:
            login_button = st.button("Se connecter", type="primary")
        
        if login_button or (username and password and st.session_state.login_pass):
            if login_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
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
        
        # 1. حقل اسم المستخدم
        new_username = st.text_input("Choisissez un nom d'utilisateur *", key="reg_user", placeholder="Ex: admin123")
        
        # 2. حقل البريد الإلكتروني مع التحقق الملون
        email = st.text_input("Adresse e-mail *", key="reg_email", placeholder="Ex: exemple@mail.com")
        is_email_valid = False
        if email: # يبدأ الفحص فقط إذا كتب المستخدم شيئاً
            if re.match(r"[^@]+@[^@]+\.[^@]+", email):
                st.markdown('<p style="color: #28a745; font-size: 13px; margin-top: -10px;">Format de l\'e-mail valide</p>', unsafe_allow_html=True)
                is_email_valid = True
            else:
                st.markdown('<p style="color: #dc3545; font-size: 13px; margin-top: -10px;">Format invalide (ex: nom@domaine.com)</p>', unsafe_allow_html=True)
        
        # 3. حقل رقم الهاتف مع التحقق الملون
        phone = st.text_input("Numéro de téléphone *", key="reg_phone", placeholder="Ex: +33612345678")
        is_phone_valid = False
        if phone:
            if re.match(r"^\+?[0-9\s]{7,15}$", phone):
                st.markdown('<p style="color: #28a745; font-size: 13px; margin-top: -10px;">Numéro de téléphone valide</p>', unsafe_allow_html=True)
                is_phone_valid = True
            else:
                st.markdown('<p style="color: #dc3545; font-size: 13px; margin-top: -10px;">Uniquement des chiffres (7 à 15 caractères)</p>', unsafe_allow_html=True)
        
        # 4. حقول كلمة المرور
        new_password = st.text_input("Choisissez un mot de passe *", type="password", key="reg_pass", placeholder="••••••••")
        confirm_password = st.text_input("Confirmez le mot de passe *", type="password", key="reg_pass_conf", placeholder="••••••••")
        
        # التحقق من تطابق كلمة المرور فورياً
        is_password_matching = False
        if new_password and confirm_password:
            if new_password == confirm_password:
                st.markdown('<p style="color: #28a745; font-size: 13px; margin-top: -10px;">Les mots de passe correspondent</p>', unsafe_allow_html=True)
                is_password_matching = True
            else:
                st.markdown('<p style="color: #dc3545; font-size: 13px; margin-top: -10px;">Les mots de passe ne correspondent pas</p>', unsafe_allow_html=True)

        st.write("")
        
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            signup_button = st.button("Créer le compte", type="primary")
        
        # 🌟 تفعيل زر Enter أو الضغط على الزر مع التحقق الشامل
        if signup_button or (new_username and email and phone and new_password and st.session_state.reg_pass_conf):
            
            # التأكد أولاً من ملء كافة الحقول الأساسية
            if not new_username or not email or not phone or not new_password or not confirm_password:
                st.warning("Veuillez remplir tous les champs obligatoires.")
            
            # التأكد من أن جميع المدخلات تجاوزت الفحص بنجاح (باللون الأخضر)
            elif not is_email_valid:
                st.error("Veuillez corriger l'adresse e-mail avant validation.")
                
            elif not is_phone_valid:
                st.error("Veuillez corriger le numéro de téléphone avant validation.")
                
            elif not is_password_matching:
                st.error("Les mots de passe doivent être identiques.")
            
            else:
                # إذا كان كل شيء ممتلئاً وصحيحاً يتم التسجيل
                if add_user(new_username, new_password, email, phone):
                    st.success("Compte créé avec succès ! Vous pouvez maintenant passer à la page de connexion.")
                else:
                    st.error("Ce nom d'utilisateur est déjà pris. Veuillez en choisir un autre.")
