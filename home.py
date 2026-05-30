import streamlit as st
from datetime import datetime
import pandas as pd
from streamlit_autorefresh import st_autorefresh 

# تأكد من وجود هذا السطر في أعلى ملف التطبيق لقراءة الـ CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
# 1. إعدادات الصفحة
st.set_page_config(
    page_title="Industrial AI Control Center",
    layout="wide",
    page_icon=":material/factory:"
)

# 2. إخفاء القائمة الجانبية برمجياً إذا لم يتم التفعيل
if "is_activated" not in st.session_state or not st.session_state.is_activated:
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {display: none;}
            [data-testid="stSidebar"] {display: none;}
        </style>
    """, unsafe_allow_html=True)

# ----------------------------------------------------------------
# 3. جلب قاعدة بيانات المفاتيح والتواريخ من Google Sheets أونلاين
# ----------------------------------------------------------------
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
        st.error("خطأ في الاتصال بخادم التفعيل أونلاين. يرجى التحقق من جودة الإنترنت لديك والمحاولة لاحقاً.")
        st.stop()


if "is_activated" not in st.session_state:
    st.session_state.is_activated = False

# دالة التحقق الذكية من المفتاح والوقت
def verify_key(key):
    db = load_licenses_from_sheets()
    
    if key in db:
        key_info = db[key]
        expire_date = datetime.strptime(key_info["expire_date"], '%Y-%m-%d')
        current_date = datetime.now()
        
        if current_date > expire_date:
            st.error(f" هذا المفتاح انتهت صلاحيته بتاريخ: {key_info['expire_date']}")
            return
            
        if key_info["used_devices"] >= key_info["max_devices"]:
            st.error(" هذا المفتاح مستخدم على أقصى عدد مسموح به من الأجهزة!")
            return
            
        st.session_state.is_activated = True
        st.session_state.license_expiry = key_info["expire_date"]
        st.success(" تم التفعيل بنجاح!")
        st.rerun()
    else:
        st.error(" Clé d'activation invalide !")


# 1. تعريف النافذة المنبثقة خارج الشروط (لتكون متاحة للاستدعاء)
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
# 4. واجهة قفل التطبيق (تم إدخال col_right بالكامل داخل الـ if)
# ----------------------------------------------------------------
if not st.session_state.is_activated:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>🔒 Activation du Système</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Le système de contrôle industriel est protégé. Veuillez activer votre produit.</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.subheader("🔑 Activation du Produit")
        with st.container(border=True):
            input_key = st.text_input("Clé de Produit (Product Key)", type="password", placeholder="XXXX-XXXX-XXXX")
            st.write("") 
            
            sub_col1, sub_col2, sub_col3 = st.columns([1, 1.5, 1])
            with sub_col2:
                if st.button("Activer le Système", type="primary"): 
                    verify_key(input_key)
            st.write("") 
            st.caption("Note: La clé est valide pour une utilisation sur deux appareils maximum.")

    # تعديل: تم نقل الـ col_right إلى هنا (داخل نطاق الـ if الشرطية)
    with col_right:
        st.subheader("🛒 Achat d'une Clé d'Activation")
        with st.container(border=True):
            st.markdown("""
            **Besoin d'une clé de produit valide ?** Vous pouvez obtenir une nouvelle clé d'activation immédiatement en contactant notre service commercial ou via notre plateforme sécurisée.
            """)
            st.write("") 
            
            sub_b1, sub_b2, sub_b3 = st.columns([0.5, 2, 0.5])
            with sub_b2:
                if st.button("Acheter une Clé / Support", type="secondary"):
                    st.toast("💡 Redirection vers le support commercial...", icon="ℹ️")
                    show_contact_dialog() 
                    
            st.write("")
            st.caption("Pour toute urgence, contactez : Markandreas03@gmail.com")
            
    st.stop() # إيقاف الكود هنا فلا يظهر المحتوى الأصلي إلا بعد التفعيل

# =========================================================
# المحتوى الأصلي (يظهر فقط بعد التفعيل الناجح)
# =========================================================


# تحديث تلقائي كل ثانية
st_autorefresh(interval=1000, key="refresh_clock")

st.title(":material/factory: Industrial AI Control Center")


# =========================================================================
# شعار المنصة في أعلى الـ Sidebar الجانبي
# =========================================================================
st.sidebar.markdown(
    """
    <div style="display: flex; flex-direction: column; align-items: flex-start; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #e0e0e0;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <img src="ضع_رابط_الأيقونة_هنا.png" width="40" style="object-fit: contain;">
            <h1 style="font-family: 'Poppins', 'Helvetica Neue', sans-serif; font-size: 24px; font-weight: 700; color: #1E3A8A; margin: 0; padding: 0;">
                Fetba Platform
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
# حساب الوقت المتبقي لانتهاء الترخيص
# =========================================================================
try:
    # تحويل التاريخ (تأكد أن الصيغة في السيرفر تطابق YYYY-MM-DD)
    expiry_date = datetime.strptime(st.session_state.license_expiry, "%Y-%m-%d")
    now = datetime.now()
    
    # حساب الفارق الزمني
    time_remaining = expiry_date - now
    days_remaining = time_remaining.days
    
    # تحضير النص والأيقونة بناءً على حالة الترخيص
    if days_remaining > 0:
        license_status_text = f":material/hourglass_top: Temps restant : {days_remaining} jours"
        # إذا كان متبقي أقل من 7 أيام يظهر تنبيه أصفر، وإلا يظهر أخضر نجاح
        sidebar_status = st.sidebar.warning if days_remaining <= 7 else st.sidebar.success
    else:
        license_status_text = ":material/gpp_bad: Licence expirée !"
        sidebar_status = st.sidebar.error
        
except Exception:
    license_status_text = ":material/hourglass_empty: Temps restant : Indisponible"
    sidebar_status = st.sidebar.info

# =========================================================================
# عرض البيانات في القائمة الجانبية (Sidebar) بأيقونات Material الرسمية
# =========================================================================

# الخانة الأولى: تاريخ انتهاء الترخيص مع أيقونة القفل الذكي (verified_user)
sidebar_status(f":material/verified_user: Version sous licence jusqu'au : {st.session_state.license_expiry}")

# الخانة الثانية: الوقت المتبقي بالأيام (تأخذ لون الحالة وتأتي بأيقونة الساعة تلقائياً من الشرط)
st.sidebar.info(license_status_text)


st.markdown("### Smart Factory Monitoring & Scheduling System")
st.markdown("---")

# لوحة تحكم علوية
col_status, col_timer, col_action = st.columns([1, 1, 1])

with col_status:
    st.metric(":material/gpp_good: System Status", "Online & Protected")

with col_timer:
    if "sim_start_time" in st.session_state:
        sim_duration = (datetime.now() - st.session_state.sim_start_time).total_seconds()
        mins, secs = divmod(int(sim_duration), 60)
        st.metric(":material/hourglass_top: Runtime", f"{mins:02d}:{secs:02d}")
    else:
        st.metric(":material/hourglass_empty: Runtime", "00:00")

with col_action:
    st.markdown('<div style="text-align: right; direction: rtl;">', unsafe_allow_html=True)
    if st.button(":material/rocket_launch: Start Production Simulation"):
        st.session_state.sim_start_time = datetime.now()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# باقي محتوى الصفحة (Architecture, Overview...)
col1, col2 = st.columns(2)
with col1:
    st.subheader(":material/analytics: Quick Overview")
    st.info("""
    🔹 **Monitoring System** - Real-time machine tracking  
    - Sensor alerts (temperature, vibration...)  
    """)

with col2:
    st.subheader(":material/schema: System Architecture")
    st.code("""
User Interface (Streamlit)
        ↓
Monitoring ←→ Scheduling (GA)
        ↓
     Alerts ←→ Logs
    """)

st.caption("Industrial AI System v1.0 | Authorized Access Only")
