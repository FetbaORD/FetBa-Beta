import streamlit as st
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# 1. إعدادات الصفحة (يجب أن تكون في البداية تماماً)
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

# 3. قاعدة بيانات المفاتيح في الـ Session
if "activation_db" not in st.session_state:
    # قائمة بـ 10 مفاتيح مخصصة من اختيارك
    custom_keys = [
        "HY2qFJz5Hy",
        "rL1KYJ2VmO",
        "e25S2Fk5n1",
        "Z3KtgCU2SX",
        "09mTViNJEe",
        "8fB1Cy92XM",
        "U61R9aqx1N",
        "7Cj2ycuB9W",
        "imc3VxT773",
        "lBgYz7JyW6",
    ]
    
    # تحويل القائمة إلى قاموس مع وضع عداد الأجهزة 0 لكل مفتاح
    st.session_state.activation_db = {key: 0 for key in custom_keys}

if "is_activated" not in st.session_state:
    st.session_state.is_activated = False

# دالة التحقق
def verify_key(key):
    db = st.session_state.activation_db
    if key in db:
        if db[key] < 2: 
            db[key] += 1
            st.session_state.is_activated = True
            st.success(":material/check_circle: تم التفعيل بنجاح!")
            st.rerun()
        else:
            st.error(":material/error: هذا المفتاح تم استخدامه على جهازين بالفعل!")
    else:
        st.error(":material/cancel: مفتاح التفعيل غير صحيح!")
# 4. واجهة القفل (موزعة ومقسمة بين التفعيل والشراء في منتصف الشاشة)
if not st.session_state.is_activated:
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # عنوان الواجهة الرئيسي في المنتصف
    st.markdown("<h1 style='text-align: center;'>🔒 Activation du Système</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Le système de contrôle industriel est protégé. Veuillez activer votre produit.</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # إنشاء عمودين رئيسيين متساويين لتوزيع الواجهة (تفعيل | شراء)
    col_left, col_right = st.columns([1, 1])
    
    # -------------------------------------------------------------
    # الجانب الأيمن: كرت التفعيل الافتراضي (Activation)
    # -------------------------------------------------------------
    with col_left:
        st.subheader("🔑 Activation du Produit")
        with st.container(border=True):
            input_key = st.text_input("Clé de Produit (Product Key)", type="password", placeholder="XXXX-XXXX-XXXX")
            st.write("") 
            
            # زر التفعيل متناسق وموسط داخل عموده
            sub_col1, sub_col2, sub_col3 = st.columns([1, 1.5, 1])
            with sub_col2:
                if st.button("Activer le Système", type="primary"): 
                    verify_key(input_key)
            
            st.write("") 
            st.caption("Note: La clé est valide pour une utilisation sur deux appareils maximum.")

    # -------------------------------------------------------------
    # الجانب الأيسر: كرت شراء مفتاح جديد (Achat de clé)
    # -------------------------------------------------------------
    with col_right:
        st.subheader("🛒 Achat d'une Clé d'Activation")
        with st.container(border=True):
            st.markdown("""
            **Besoin d'une clé de produit valide ?** Vous pouvez obtenir une nouvelle clé d'activation immédiatement en contactant notre service commercial ou via notre plateforme sécurisée.
            
            * ⚡ **Livraison Instantanée** par Email.
            * 🛠️ **Support Technique 24/7** inclus.
            * 💻 **Licence Officielle** pour 2 appareils.
            """)
            
            st.write("") # فراغ جمالي
            
            # زر توجيهي للشراء أو الدعم
            sub_b1, sub_b2, sub_b3 = st.columns([0.5, 2, 0.5])
            with sub_b2:
                # يمكنك ربطه برابط خارجي أو تركه كزر تواصل
                if st.button("Acheter une Clé / Support", type="secondary"):
                    st.toast("💡 Redirection vers le support commercial...", icon="ℹ️")
            
            st.write("")
            st.caption("Pour toute urgence, contactez : admin@company.com")
            
    st.stop()
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
