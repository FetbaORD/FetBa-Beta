import streamlit as st

# إعدادات الصفحة
st.set_page_config(page_title="Contact Us", page_icon="✉️", layout="centered")

# دالة لقراءة ملف CSS وتطبيقه
def local_css(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# استدعاء ملف الستايل
local_css("style.css")

# واجهة المستخدم الحاوية للعنوان
st.markdown("<h1 class='main-title'>تواصل معنا</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>يسعدنا استقبال استفساراتك ورسائلك، سنقوم بالرد عليك في أقرب وقت ممكن.</p>", unsafe_allow_html=True)

# رابط الإرسال الخاص بـ FormSubmit مع إيميلك
FORM_SUBMIT_URL = "https://formsubmit.co/markandreas03@gmail.com"

# إنشاء النموذج داخل حاوية HTML مخصصة
st.markdown('<div class="contact-container">', unsafe_allow_html=True)

# استخدام st.form للتحكم في الإدخال والضغط
with st.form(key="contact_form", clear_on_submit=True):
    
    # حقول الإدخال
    name = st.text_input("الاسم الكامل", placeholder="أدخل اسمك هنا...")
    email = st.text_input("البريد الإلكتروني", placeholder="example@domain.com")
    message = st.text_area("محتوى الرسالة", placeholder="اكتب رسالتك هنا...", height=150)
    
    # حقل خفي لتجنب الرسائل العشوائية (Captcha/Anti-Spam) من FormSubmit
    st.markdown(f'<input type="hidden" name="_captcha" value="false">', unsafe_allow_html=True)
    
    # زر الإرسال
    submit_button = st.form_submit_button(label="إرسال الرسالة")

st.markdown('</div>', unsafe_allow_html=True)

# معالجة عملية الإرسال عند الضغط على الزر
if submit_button:
    if not email or not message:
        st.error("الرجاء ملء حقل البريد الإلكتروني ومحتوى الرسالة!")
    elif "@" not in email:
        st.error("الرجاء إدخال بريد إلكتروني صحيح!")
    else:
        # إرسال البيانات خلف الكواليس باستخدام requests دون إعادة توجيه المستخدم
        import requests
        
        data = {
            "Name": name,
            "Email": email,
            "Message": message
        }
        
        try:
            response = requests.post(FORM_SUBMIT_URL, data=data)
            if response.status_code == 200:
                st.success("🎉 تم إرسال رسالتك بنجاح! شكرًا لتواصلك معنا.")
            else:
                st.error("عذرًا، حدث خطأ أثناء إرسال الرسالة. حاول مرة أخرى لاحقًا.")
        except Exception as e:
            st.error("تعذر الاتصال بالسيرفر، تحقق من اتصال الإنترنت الخاص بك.")
