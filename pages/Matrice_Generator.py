import streamlit as st
import numpy as np
import random
import pandas as pd

# Paramètres de la page
st.set_page_config(page_title="Générateur de Matrice d'Incompatibilité", layout="wide")

st.title("📊 Générateur Optimisé de Matrice d'Incompatibilité & Stérilisation")
st.write("Définissez les entrées dans la barre latérale, puis cliquez sur les boutons pour générer les matrices souhaitées.")

# Initialisation du session_state pour conserver les données lors du passage d'un bouton à l'autre
if 'Incomp' not in st.session_state:
    st.session_state.Incomp = None
if 'N' not in st.session_state:
    st.session_state.N = 0
if 'categories' not in st.session_state:
    st.session_state.categories = None
if 'taux_voulu' not in st.session_state:
    st.session_state.taux_voulu = 0.0
if 'taux_final' not in st.session_state:
    st.session_state.taux_final = 0.0
if 'nb_final' not in st.session_state:
    st.session_state.nb_final = 0
if 'total_pairs' not in st.session_state:
    st.session_state.total_pairs = 0
# Ajout d'une variable pour conserver la matrice de stérilisation importée ou générée afin de faciliter la gestion des fichiers externes
if 'Ts_matrix' not in st.session_state:
    st.session_state.Ts_matrix = None

# =========================================================
# Fonctions de calcul de base
# =========================================================

def calculer_incomp_matrix(categories):
    N = len(categories)
    cat_row = categories.reshape(1, N)
    cat_col = categories.reshape(N, 1)
    Incomp = (cat_row != cat_col).astype(int)
    np.fill_diagonal(Incomp, 0)
    return Incomp

def calculer_nb_incompatibilites(categories):
    Incomp = calculer_incomp_matrix(categories)
    return np.sum(Incomp)

def generer_matrice_sterilisation(Incomp):
    N = Incomp.shape[0]
    Ts = np.zeros((N, N), dtype=int)
    
    for i in range(N):
        for j in range(i + 1, N):
            if Incomp[i, j] == 1:
                # Génération d'une valeur aléatoire symétrique entre 1 et 99 pour Ts(i,j) et Ts(j,i)
                valeur_aleatoire = random.randint(1, 99)
                Ts[i, j] = valeur_aleatoire
                Ts[j, i] = valeur_aleatoire
            else:
                # La valeur 10 est fixe en cas de compatibilité
                Ts[i, j] = 0
                Ts[j, i] = 0
                
    # Garantie que la diagonale principale est strictement nulle Ts(i,i) = 0
    np.fill_diagonal(Ts, 0)
    return Ts

# =========================================================
# Moteur de recherche et d'optimisation
# =========================================================
def optimiser_repartition(N, taux_cible, max_classes):
    total_pairs = N * (N - 1)
    nb_cible = round((taux_cible / 100) * total_pairs)
    
    # ✅ Solution : on commence par placer tous les produits dans la classe 1 (taux d'incompatibilité = 0 %)
    # Cela laisse à l'algorithme toute liberté pour monter progressivement et précisément vers le taux souhaité
    categories = np.ones(N, dtype=int)
    
    best_categories = categories.copy()
    min_diff = abs(calculer_nb_incompatibilites(categories) - nb_cible)

    for i in range(100000):
        current_nb = calculer_nb_incompatibilites(categories)
        if current_nb == nb_cible:
            break

        idx = random.randint(0, N - 1)
        old_val = categories[idx]
        new_val = random.randint(1, max_classes) 
        
        categories[idx] = new_val
        new_diff = abs(calculer_nb_incompatibilites(categories) - nb_cible)

        # Accepter le changement s'il nous rapproche de l'objectif ou s'il lui est égal
        if new_diff <= min_diff:
            min_diff = new_diff
            best_categories = categories.copy()
        else:
            # Donner une petite chance (1 %) d'acceptation aléatoire pour sortir des minima locaux
            if random.random() > 0.01: 
                categories[idx] = old_val

    res = best_categories.copy()
    unique_classes = sorted(np.unique(res))
    mapping = {old: new for new, old in enumerate(unique_classes, 1)}
    for old_id, new_id in mapping.items():
        res[best_categories == old_id] = new_id
        
    return res

# =========================================================
# Interface utilisateur (Streamlit UI)
# =========================================================

st.sidebar.header("⚙️ Données d'entrée")

input_N = st.sidebar.number_input(
    "Nombre total de produits (N) :", 
    min_value=1, 
    max_value=200, 
    value=20, 
    step=1
)

input_taux_voulu = st.sidebar.slider(
    "Taux d'incompatibilité voulu (%) :", 
    min_value=0.0, 
    max_value=100.0, 
    value=30.0, 
    step=0.5
)

# Ajout d'un contrôle dans la barre latérale pour fixer le nombre maximal de classes autorisé
max_classes = st.sidebar.number_input(
    "Nombre maximal de classes (Max Classes) :",
    min_value=2,
    max_value=20,
    value=6
)


# Boutons de génération dans la barre latérale
bttn_incomp = st.sidebar.button("Generate Matrice Incompatibilité", use_container_width=True)
bttn_temp = st.sidebar.button("Générer la matrice des temps de stérilisation (Temp Sterlisation)", use_container_width=True)

# ---------------------------------------------------------
# Premier événement : clic sur le bouton de génération de la matrice d'incompatibilité
# ---------------------------------------------------------
if bttn_incomp:
    with st.spinner("Exécution de l'algorithme d'optimisation..."):
        st.session_state.N = input_N
        st.session_state.taux_voulu = input_taux_voulu
        st.session_state.categories = optimiser_repartition(input_N, input_taux_voulu, max_classes)
        st.session_state.Incomp = calculer_incomp_matrix(st.session_state.categories)
        st.session_state.nb_final = np.sum(st.session_state.Incomp)
        st.session_state.total_pairs = input_N * (input_N - 1)
        st.session_state.taux_final = (st.session_state.nb_final / st.session_state.total_pairs) * 100

# Affichage des résultats de la matrice d'incompatibilité si elle est disponible en mémoire
if st.session_state.Incomp is not None:
    st.markdown("---")
    st.subheader("📊 Résultats de la matrice d'incompatibilité (Matrice d'incompatibilité)")
    
    # ➕ Ajout d'une option d'import de la matrice d'incompatibilité depuis un fichier txt à côté de la matrice d'import
    file_incomp = st.file_uploader("📥 Importer Matrice Incompatibilité (.txt)", type=["txt"], key="upload_incomp")
    if file_incomp is not None:
        try:
            loaded_matrix = np.loadtxt(file_incomp, dtype=int)
            if loaded_matrix.ndim == 2 and loaded_matrix.shape[0] == loaded_matrix.shape[1]:
                st.session_state.Incomp = loaded_matrix
                st.session_state.N = loaded_matrix.shape[0]
                st.session_state.nb_final = np.sum(st.session_state.Incomp)
                st.session_state.total_pairs = st.session_state.N * (st.session_state.N - 1)
                st.session_state.taux_final = (st.session_state.nb_final / st.session_state.total_pairs) * 100
                
                # ✨ Code ajouté : analyse et déduction des classes à partir des données importées du fichier texte
                comp_matrix = (loaded_matrix == 0).astype(int)
                visited = np.zeros(st.session_state.N, dtype=bool)
                extracted_categories = np.zeros(st.session_state.N, dtype=int)
                current_class = 1
                
                for i in range(st.session_state.N):
                    if not visited[i]:
                        # Recherche de tous les éléments compatibles (0 dans la matrice d'origine) pour former une seule classe
                        queue = [i]
                        visited[i] = True
                        while queue:
                            curr = queue.pop(0)
                            extracted_categories[curr] = current_class
                            for neighbor in range(st.session_state.N):
                                if comp_matrix[curr, neighbor] == 1 and not visited[neighbor]:
                                    visited[neighbor] = True
                                    queue.append(neighbor)
                        current_class += 1
                
                st.session_state.categories = extracted_categories
            else:
                st.error("⚠️ Le fichier texte ne contient pas de matrice carrée valide.")
        except Exception as e:
            st.error(f"❌ Erreur lors de la lecture du fichier : {e}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Taux souhaité", value=f"{st.session_state.taux_voulu:.2f} %")
    with col2:
        st.metric(label="Taux atteint", value=f"{st.session_state.taux_final:.2f} %", delta=f"{st.session_state.taux_final - st.session_state.taux_voulu:.2f} %")
    with col3:
        st.metric(label="Nombre de cas d'incompatibilité", value=f"{int(st.session_state.nb_final)} / {st.session_state.total_pairs}")

    # Affichage du tableau de la matrice d'incompatibilité
    df_incomp = pd.DataFrame(
        st.session_state.Incomp, 
        index=[f"P{i+1}" for i in range(st.session_state.N)], 
        columns=[f"P{j+1}" for j in range(st.session_state.N)]
    )
    st.dataframe(df_incomp, use_container_width=True)

    # Détails des classes
    st.subheader("🗂️ Répartition des produits par classe (Répartition)")
    classes, counts = np.unique(st.session_state.categories, return_counts=True)
    col_left, col_right = st.columns([1, 2])
    with col_left:
        for cl, ct in zip(classes, counts):
            st.info(f"🔹 **Classe {int(cl)}** : {ct} produits")
    with col_right:
        df_cat = pd.DataFrame({
            "Produit": [f"P{i+1}" for i in range(st.session_state.N)],
            "Classe Affectée": st.session_state.categories
        })
        st.dataframe(df_cat.T, use_container_width=True)

# ---------------------------------------------------------
# Deuxième événement : clic sur le bouton de génération de la matrice des temps de stérilisation
# ---------------------------------------------------------
if bttn_temp:
    if st.session_state.Incomp is None:
        st.error("⚠️ Veuillez d'abord générer la matrice d'incompatibilité en cliquant sur le premier bouton !")
    else:
        st.session_state.markdown_visible = True
        with st.spinner("Construction de la matrice symétrique des temps de stérilisation..."):
            st.session_state.Ts_matrix = generer_matrice_sterilisation(st.session_state.Incomp)

# Vérification de l'existence de la matrice des temps de stérilisation pour l'afficher et ajouter l'option d'import à côté
if st.session_state.Ts_matrix is not None or bttn_temp:
    if st.session_state.Incomp is not None:
        st.markdown("---")
        st.subheader("⏱️ Matrice des temps de stérilisation calculée (Temp_Sterlisation - Ts)")
        st.info("💡 Cette matrice est calculée comme un miroir symétrique : valeur 10 en cas de compatibilité (0), valeur aléatoire [1-99] en cas d'incompatibilité (1), et diagonale nulle.")
        
        # ➕ Ajout d'une option d'import de la matrice des temps de stérilisation depuis un fichier txt à côté du tableau
        file_ts = st.file_uploader("📥 Importer Matrice Temp Stérilisation (.txt)", type=["txt"], key="upload_ts")
        if file_ts is not None:
            try:
                loaded_ts = np.loadtxt(file_ts, dtype=int)
                if loaded_ts.ndim == 2 and loaded_ts.shape[0] == st.session_state.N:
                    st.session_state.Ts_matrix = loaded_ts
                else:
                    st.error(f"⚠️ Les dimensions de la matrice importée doivent correspondre au nombre de produits actuel ({st.session_state.N}x{st.session_state.N}).")
            except Exception as e:
                st.error(f"❌ Erreur lors de la lecture du fichier : {e}")

        if st.session_state.Ts_matrix is not None:
            # Conversion en DataFrame pour un affichage interactif structuré
            df_ts = pd.DataFrame(
                st.session_state.Ts_matrix,
                index=[f"P{i+1}" for i in range(st.session_state.N)],
                columns=[f"P{j+1}" for j in range(st.session_state.N)]
            )
            st.dataframe(df_ts, use_container_width=True)
