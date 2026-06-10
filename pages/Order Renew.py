import streamlit as st
import requests

# إعدادات الصفحة
st.set_page_config(page_title="Order Renew", page_icon="🔄", layout="centered")

# دالة لتطبيق الـ CSS
def local_css(file_name):
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

local_css("style.css")

# عنوان الصفحة
st.markdown("<h1 class='main-title'>تجديد الاشتراك | Order Renew</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>أدخل الرقم التسلسلي الخاص بك واختر خطة التجديد المناسبة لإتمام العملية.</p>", unsafe_allow_html=True)

# رابط خدمة إرسال الإيميلات (FormSubmit) المربوط بإيميلك
FORM_SUBMIT_URL = "https://formsubmit.co/markandreas03@gmail.com"

# فتح حاوية التنسيق المخصصة
st.markdown('<div class="renew-container">', unsafe_allow_html=True)

with st.form(key="renew_form", clear_on_submit=False):
    
    # 1. إدخال الرقم التسلسلي
    serial_number = st.text_input("الرقم التسلسلي (Serial Number) *", placeholder="مثال: XXXX-XXXX-XXXX-XXXX")
    
    # 2. اختيار مدة التجديد
    duration = st.radio(
        "اختر مدة التجديد *",
        ["شهر واحد (1 Month)", "6 أشهر (6 Months)", "عام كامل (1 Year)"],
        index=0
    )
    
    # حساب السعر بناءً على الاختيار للاستخدام في العرض والإرسال
    if duration == "شهر واحد (1 Month)":
        price = "8$"
    elif duration == "6 أشهر (6 Months)":
        price = "40$"
    else:
        price = "70$"
        
    # عرض السعر بشكل احترافي للعميل
    st.markdown(f'<div class="price-tag">المبلغ الإجمالي المستحق: {price}</div>', unsafe_allow_html=True)
    
    # 3. اختيار طريقة الدفع
    payment_method = st.selectbox(
        "اختر طريقة الدفع المفضلة *",
        ["PayPal", "Credit Card (Stripe)", "BaridiMob (بريديبوب)"]
    )
    
    # عرض تعليمات بناءً على طريقة الدفع
    screenshot = None
    if payment_method == "BaridiMob (بريديبوب)":
        st.markdown("""
        <div class="payment-info-box">
            <strong>⚠️ معلومات الدفع عبر بريديبوب:</strong><br>
            الرجاء تحويل المبلغ المقابل بالدينار الجزائري إلى الحساب التالي:<br>
            <strong>RIP:</strong> 00799999000123456789 (قم بتغييره لحسابك الحقيقي)<br>
            بعد إتمام التحويل، يرجى رفع صورة أو لقطة شاشة لوصل التحويل (Screenshot) لإثبات الدفع.
        </div>
        """, unsafe_allow_html=True)
        screenshot = st.file_uploader("ارفع لقطة شاشة لوصل الدفع (PNG/JPG)", type=["jpg", "png", "jpeg"])
        
    elif payment_method == "PayPal":
        st.info("💡 سيتم توجيه طلب التجديد للمراجعة فور الضغط على الزر أدناه، يرجى التأكد من جاهزية حسابك لإتمام الدفع عند التواصل معك.")
        
    elif payment_method == "Credit Card (Stripe)":
        st.info("💳 أدخل بيانات بطاقتك الائتمانية عبر بوابة التأمين عند معالجة طلبك.")

    # حقول خفية لضبط إعدادات FormSubmit (تعطيل الكابتشا وتخصيص العنوان)
    st.markdown('<input type="hidden" name="_captcha" value="false">', unsafe_allow_html=True)
    st.markdown(f'<input type="hidden" name="_subject" value="طلب تجديد جديد: {serial_number}">', unsafe_allow_html=True)

    # زر إرسال الطلب وإتمام العملية
    submit_button = st.form_submit_button(label="تأكيد وإرسال طلب التجديد")

st.markdown('</div>', unsafe_allow_html=True)

# معالجة الضغط على زر الإرسال
if submit_button:
    if not serial_number:
        st.error("الرجاء إدخال الرقم التسلسلي الخاص بك أولاً!")
    elif payment_method == "BaridiMob (بريديبوب)" and screenshot is None:
        st.error("الرجاء رفع صورة وصل تحويل بريديموب لإثبات الدفع!")
    else:
        # تجهيز البيانات لإرسالها بالبريد الإلكتروني عبر API الخاص بـ FormSubmit
        payload = {
            "الرقم التسلسلي (Serial)": serial_number,
            "مدة التجديد المختار": duration,
            "السعر": price,
            "طريقة الدفع": payment_method
        }
        
        files = {}
        # إذا كان الدفع عبر بريديموب وهناك ملف مرفوع، نرسله كملف مرفق للإيميل تلقائياً
        if screenshot is not None:
            files = {"attachment": (screenshot.name, screenshot.getvalue(), screenshot.type)}
            
        with st.spinner("جاري معالجة وإرسال طلبك..."):
            try:
                # إرسال الطلب (POST Request)
                if files:
                    response = requests.post(FORM_SUBMIT_URL, data=payload, files=files)
                else:
                    response = requests.post(FORM_SUBMIT_URL, data=payload)
                    
                if response.status_code == 200:
                    st.success(f"🎉 تم إرسال طلب التجديد للرقم التسلسلي ({serial_number}) بنجاح! ستتلقى رسالة تأكيد على بريدك فور تفعيل الاشتراك.")
                else:
                    st.error("حدث خطأ أثناء معالجة الطلب، يرجى المحاولة مرة أخرى.")
            except Exception as e:
                st.error("فشل الاتصال بخادم إرسال البيانات، يرجى التحقق من الإنترنت.")
