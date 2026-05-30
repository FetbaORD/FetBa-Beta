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
# ----------------------------------------------------------------
# 3. جلب قاعدة بيانات المفاتيح والتواريخ من Google Sheets أونلاين (نسخة محدثة ومستقرة)
# ----------------------------------------------------------------
def load_licenses_from_sheets():
    try:
        # قراءة الرابط الآمن من الـ Secrets
        sheet_url = st.secrets["public_gsheet_url"]
        
        # استخراج المعرّف الفريد للجدول (ID) برمجياً لضمان دقة التحويل
        # هذا الأسلوب يتفوق على الاستبدال النصي التقليدي ويمنع مشاكل روابط usp=drivesdk
        if "/d/" in sheet_url:
            sheet_id = sheet_url.split("/d/")[1].split("/")[0]
        else:
            sheet_id = sheet_url
            
        # الرابط المباشر والأكثر استقراراً لتصدير البيانات بصيغة CSV
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        
        # قراءة البيانات مع تحديد نوع البيانات كنصوص لمنع أخطاء تحويل الأرقام
        df = pd.read_csv(csv_url, dtype=str)
        
        # تنظيف البيانات وتحويلها لقاموس (Dictionary)
        db = {}
        for _, row in df.iterrows():
            # التأكد من عدم وجود حقول فارغة في السطر
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
        # يفضل طباعة الخطأ الحقيقي في الـ Console للمطور لمعرفة السبب بدقة دون إظهاره للمستخدم
        print(f"Error connecting to Google Sheets: {e}")
        st.error("خطأ في الاتصال بخادم التفعيل أونلاين. يرجى التحقق من جودة الإنترنت لديك والمحاولة لاحقاً.")
        st.stop()


if "is_activated" not in st.session_state:
    st.session_state.is_activated = False

# دالة التحقق الذكية من المفتاح والوقت
def verify_key(key):
    # جلب أحدث البيانات من الجدول أونلاين في تلك اللحظة
    db = load_licenses_from_sheets()
    
    if key in db:
        key_info = db[key]
        
        # تحويل نصوص التواريخ إلى صيغة وقت للمقارنة
        expire_date = datetime.strptime(key_info["expire_date"], '%Y-%m-%d')
        current_date = datetime.now()
        
        # 1. التحقق من تاريخ انتهاء الصلاحية المخصص الذي حددته أنت في الجدول
        if current_date > expire_date:
            st.error(f"❌ هذا المفتاح انتهت صلاحيته بتاريخ: {key_info['expire_date']}")
            return
            
        # 2. التحقق من عدد الأجهزة
        if key_info["used_devices"] >= key_info["max_devices"]:
            st.error("❌ هذا المفتاح مستخدم على أقصى عدد مسموح به من الأجهزة!")
            return
            
        # إذا كان كل شيء تمام يتم التفعيل
        st.session_state.is_activated = True
        st.session_state.license_expiry = key_info["expire_date"]
        st.success("✔️ تم التفعيل بنجاح!")
        st.rerun()
    else:
        st.error("❌ مفتاح التفعيل غير صحيح!")

# ----------------------------------------------------------------
# 4. واجهة قفل التطبيق
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


# 1. تعريف النافذة المنبثقة واستخدام st.html لتنفيذ كود الـ HTML
@st.dialog("📱 Support & Achat de Clé", width="medium")
def show_contact_dialog():
    # استخدام st.html يضمن أن الـ Streamlit سيقوم بتشغيل الكود وليس طباعته كنص
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

# 2. قسم الكود الخاص بك المرتبط بالزر (بدون تعديل، فقط استدعاء الدالة)
with col_right:
    st.subheader("🛒 Achat d'une Clé d'Activation")
    with st.container(border=True):
        st.markdown("""
        **Besoin d'une clé de produit valide ?** Vous pouvez obtenir une nouvelle clé d'activation immédiatement en contactant notre service commercial ou via notre plateforme sécurisée.
        """)
        st.write("") 
        
        sub_b1, sub_b2, sub_b3 = st.columns([0.5, 2, 0.5])
        with sub_b2:
            if st.button("Acheter une Clé / Support", type="secondary", use_container_width=True):
                st.toast("💡 Redirection vers le support commercial...", icon="ℹ️")
                show_contact_dialog() # استدعاء النافذة المنبثقة
                
        st.write("")
        st.caption("Pour toute urgence, contactez : Markandreas03@gmail.com")
        
st.stop()

# =========================================================
# المحتوى الأصلي (يظهر فقط بعد التفعيل)
# =========================================================
st.title(":material/factory: Industrial AI Control Center")
st.sidebar.success(f"🔐 نسخة مرخصة حتى: {st.session_state.license_expiry}")
# =========================================================
# المحتوى الأصلي (يظهر فقط بعد التفعيل)
# =========================================================

# تحديث تلقائي كل ثانية
st_autorefresh(interval=1000, key="refresh_clock")

st.title(":material/factory: Industrial AI Control Center")
st.markdown("### Smart Factory Monitoring & Scheduling System")

# منطق عداد الوقت
if "sim_start_time" not in st.session_state:
    # لا نبدأ الوقت تلقائياً إلا عند ضغط الزر
    pass

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
    # إنشاء حاوية HTML تجبر الزر على الانحياز لليمين تماماً (Right-to-Left)
    st.markdown('<div style="text-align: right; direction: rtl;">', unsafe_allow_html=True)
    
    # قمنا بإزالة use_container_width ليحافظ الزر على حجمه الصغير والاحترافي
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
