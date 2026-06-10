import streamlit as st
from auth_pages import sign_in_page, sign_up_page, load_css

# 1. Initialisation de l'état de la session (تمت إضافة الـ username هنا)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None

# Fonction de déconnexion pour reverrouiller le site
def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    # ❌ تم حذف st.rerun() لمنع ظهور التحذير السابق نهائياً 🎉

# ---- 🛡️ Gestion de la navigation conditionnelle et protection des pages ----

if not st.session_state.logged_in:
    # A) Si l'utilisateur n'est pas connecté
    login_page = st.Page(sign_in_page, title="Connexion", icon=":material/lock:")
    register_page = st.Page(sign_up_page, title="Créer un compte", icon=":material/person_add:")
    
    pg = st.navigation([login_page, register_page])

else:
    # B) Si l'utilisateur est connecté avec succès
    load_css() 
    
    # 1. Liaison du fichier principal home.py
    home_page = st.Page("home.py", title="Accueil", icon=":material/home:", default=True)
    
    # 2. Liaison des autres pages situées dans le dossier 'pages'
    page_1 = st.Page("pages/Matrice_Generator.py", title="Générateur de Matrice", icon=":material/grid_on:")
    page_2 = st.Page("pages/Monitoring.py", title="Surveillance", icon=":material/monitoring:")
    page_3 = st.Page("pages/Ordonancement.py", title="Ordonnancement", icon=":material/view_timeline:")
    page_4 = st.Page("pages/Contact Us.py" , title="Contact Us")
    page_5 = st.Page("pages/Order Renew.py", title="Order Renew")

    # 💡 نصيحة ذكية: قمنا بنقل أزرار ومعلومات المستخدم إلى داخل الـ Sidebar هنا
    # حتى تظهر دائماً في أسفل أو أعلى القائمة الجانبية بشكل أنيق وقبل تشغيل الصفحة
    with st.sidebar:
        st.markdown(f"### :material/account_circle: {st.session_state.username}")
        st.button("Se déconnecter", on_click=logout, use_container_width=True, type="secondary")
        st.markdown("---") # خط فاصل جمالي

    # Regroupement des pages du projet dans la liste de navigation
    pg = st.navigation({
        "Projet Principal": [home_page, page_1, page_2, page_3, page_4, page_5]
    })

# Exécution de la page autorisée par le serveur selon l'état de connexion
pg.run()
