import streamlit as st
import sqlite3
import re
import bcrypt
from streamlit_gsheets import GSheetsConnection
import time
import extra_streamlit_components as stx
from streamlit_autorefresh import st_autorefresh

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
    # إذا كان الهاش قادماً كنص (str) من Google Sheets، نقوم بتحويله إلى بايتات (bytes)
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    
    # التأكد أيضاً من تحويل كلمة المرور المدخلة إلى بايتات
    if isinstance(password, str):
        password = password.encode('utf-8')
        
    try:
        return bcrypt.checkpw(password, hashed_password)
    except Exception:
        # حماية التطبيق من الانهيار إذا كان الهاش المخزن في الجدول تالفاً أو فارغاً
        return False



# إنشاء اتصال بجدول بيانات جوجل (يقرأ الإعدادات تلقائياً من Secrets)
def get_sheets_connection():
    # تمرير الفئة المستوردة صراحة كما تطلب مكتبة streamlit_gsheets
    return st.connection("gsheets", type=GSheetsConnection)




def add_user(username, password, email="", phone=""):
    conn = get_sheets_connection()
    
    # 1. قراءة البيانات الحالية مع تحديد ورقة العمل بدقة
    try:
        df = conn.read(worksheet="Sheet1", ttl=0) 
    except Exception:
        import pandas as pd
        df = pd.DataFrame(columns=["username", "password", "email", "phone"])
    
    # تنظيف الأسماء الحالية قبل الفحص لمنع التكرار بسبب المسافات
    if not df.empty and "username" in df.columns:
        df['username'] = df['username'].astype(str).str.strip()
    
    # التحقق من أن اسم المستخدم غير موجود مسبقاً بعد تنظيفه
    if username.strip() in df["username"].values:
        return False
        
    # 2. تشفير كلمة المرور وتجهيز البيانات الجديدة
    hashed_pass = hash_password(password)
    new_data = {
        "username": [username.strip()],
        "password": [hashed_pass.strip()], # إزالة أي مسافات زائدة من الهاش
        "email": [email.strip()],
        "phone": [phone.strip()]
    }
    import pandas as pd
    new_df = pd.DataFrame(new_data)
    
    # دمج السطر الجديد مع البيانات السابقة
    updated_df = pd.concat([df, new_df], ignore_index=True)
    
    # 3. تحديث الجدول على ورقة العمل المحددة
    conn.update(worksheet="Sheet1", data=updated_df)
    return True

def login_user(username, password):
    conn = get_sheets_connection()
    try:
        # استخدام st.spinner لإخفاء النص الافتراضي واستبداله بنص مخصص
        with st.spinner("Checking information entered..."):
            df = conn.read(worksheet="Sheet1", ttl=0, show_spinner=False)
    except Exception as e:
        st.error(f"Erreur de lecture: {e}")
        return False
        
    if df.empty or "username" not in df.columns or "password" not in df.columns:
        return False

    # 🧼 تنظيف الأعمدة تماماً من أي مسافات فارغة (مهم جداً لجداول جوجل)
    df['username'] = df['username'].astype(str).str.strip()
    df['password'] = df['password'].astype(str).str.strip()
    
    clean_username = str(username).strip()
    
    # البحث عن السطر الخاص بالمستخدم
    user_row = df[df["username"] == clean_username]
    
    if not user_row.empty:
        # جلب الهاش المخزن
        hashed_password = user_row.iloc[0]["password"]
        
        # استدعاء دالة التحقق
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
        
        if login_button or (username and password and st.session_state.login_pass):
            if login_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.just_logged_in = True # 👈 علم مؤقت لإبلاغ المتصفح بحفظ الكوكيز
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
        
        col1, col2, col3 = st.columns([2, 1.5, 2])
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


# 1. تشغيل التحديث التلقائي في الخلفية (كل 10 ثوانٍ) لفحص عداد الدقيقة
st_autorefresh(interval=10000, key="auto_logout_check")

# 2. استدعاء مدير الكوكيز الخاص بالمتصفح
cookie_manager = stx.CookieManager()

# ✨ التعديل السحري: إعطاء وقت للمتصفح للاتصال وقراءة الكوكيز عند الـ Refresh
# إذا كانت الكوكيز لم تُحمل بعد، ننتظر قليلاً حتى تظهر لكي لا يتم الطرد تلقائياً
if "cookies_ready" not in st.session_state:
    time.sleep(0.5)  # الانتظار نصف ثانية كحد أقصى ليقرأ المتصفح الكوكيز
    st.session_state.cookies_ready = True
    st.rerun()

# جلب بيانات الجلسة الحالية من متصفح المستخدم
is_logged_cookie = cookie_manager.get(cookie="logged_in")
username_cookie = cookie_manager.get(cookie="username")
login_time_cookie = cookie_manager.get(cookie="login_time")

# مدة صلاحية الجلسة بالثواني (دقيقة واحدة = 60 ثانية)
TIMEOUT_DURATION = 60

# 3. فحص شرط الطرد بعد دقيقة واحدة
if is_logged_cookie == "true" and login_time_cookie:
    elapsed_time = time.time() - float(login_time_cookie)
    if elapsed_time > TIMEOUT_DURATION:
        # إذا انتهت الدقيقة، احذف الكوكيز فوراً واطرد المستخدم لصفحة الدخول
        cookie_manager.delete("logged_in")
        cookie_manager.delete("username")
        cookie_manager.delete("login_time")
        st.warning("تم تسجيل الخروج تلقائياً لانتهاء صلاحية الجلسة (1 دقيقة).")
        st.rerun()

# 4. توجيه واجهة المستخدم بناءً على الكوكيز المخزنة
if is_logged_cookie != "true":
    # إذا لم يكن مسجلاً في الكوكيز، نعرض قائمة الدخول والتسجيل الافتراضية
    page = st.sidebar.selectbox("Navigation", ["Connexion", "Inscription"])
    
    if page == "Connexion":
        sign_in_page()
        
        # إذا نجح الدخول من النموذج وتم تفعيل العلم المؤقت، ننقل البيانات للكوكيز فوراً
        if st.session_state.get("just_logged_in") == True:
            # تم تحديد مدة الكوكي بـ 3600 ثانية (ساعة) ولكن كود الفحص فوق سيحذفه بعد دقيقة
            cookie_manager.set("logged_in", "true", max_age=3600)
            cookie_manager.set("username", st.session_state.username, max_age=3600)
            cookie_manager.set("login_time", str(time.time()), max_age=3600)
            st.session_state.just_logged_in = False # تصفير العلم المؤقت
            st.rerun()
    else:
        sign_up_page()

else:
    # 🌟 هنا تضع كود صفحة تطبيقك الرئيسية التي تظهر بعد تسجيل الدخول الناجح 🌟
    st.title(f"مرحباً بك مجدداً، {username_cookie} 👋")
    st.success("أنت متصل الآن بشكل آمن. جرب عمل Ctrl+R الآن ولن تخرج!")
    
    # حساب وعرض الوقت المتبقي للمخدم (اختياري)
    time_left = int(TIMEOUT_DURATION - (time.time() - float(login_time_cookie)))
    if time_left > 0:
        st.info(f"الوقت المتبقي لانتهاء الجلسة تلقائياً: {time_left} ثانية.")

    # زر تسجيل الخروج اليدوي
    if st.button("Déconnexion (تسجيل الخروج)"):
        cookie_manager.delete("logged_in")
        cookie_manager.delete("username")
        cookie_manager.delete("login_time")
        if "logged_in" in st.session_state:
            st.session_state.logged_in = False
        st.rerun()
