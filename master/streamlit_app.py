import streamlit as st
from auth_pages import sign_in_page, sign_up_page, load_css

# 1. Initialisation de l'état de la session pour vérifier le statut de connexion
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Fonction de déconnexion pour reverrouiller le site
def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.rerun()

# ---- 🛡️ Gestion de la navigation conditionnelle et protection des pages ----

if not st.session_state.logged_in:
    # A) Si l'utilisateur n'est pas connecté : Le serveur affiche uniquement les options de connexion ou d'inscription
    login_page = st.Page(sign_in_page, title="Connexion", icon=":material/lock:")
    register_page = st.Page(sign_up_page, title="Créer un compte", icon=":material/person_add:")
    
    pg = st.navigation([login_page, register_page])

else:
    # B) Si l'utilisateur est connecté avec succès
    load_css() # 👈 Ajouté pour activer immédiatement les grands styles sur le sidebar !
    
    # Appel manuel des pages réelles de votre projet
    
    # 1. Liaison du fichier principal home.py
    home_page = st.Page("home.py", title="Accueil", icon=":material/home:", default=True)
    
    # 2. Liaison des autres pages situées dans le dossier 'pages'
    # Matrice_Generator -> Icône de grille de données ou de matrices
    page_1 = st.Page("pages/Matrice_Generator.py", title="Générateur de Matrice", icon=":material/grid_on:")
    
    # Monitoring -> Icône d'écran de surveillance et d'analyses
    page_2 = st.Page("pages/Monitoring.py", title="Surveillance", icon=":material/monitoring:")
    
    # Ordonancement -> Icône de planification ou de calendrier de travail
    page_3 = st.Page("pages/Ordonancement.py", title="Ordonnancement", icon=":material/view_timeline:")

    # Regroupement des pages du projet dans la liste de navigation
    pg = st.navigation({
        "Projet Principal": [home_page, page_1, page_2, page_3]
    })
    
    # Affichage du nom d'utilisateur et du bouton de déconnexion dans la barre latérale
    st.sidebar.markdown(f"### Compte actuel : {st.session_state.username}")
    st.sidebar.button("Se déconnecter", on_click=logout, use_container_width=True)

# Exécution de la page autorisée par le serveur selon l'état de connexion
pg.run()
