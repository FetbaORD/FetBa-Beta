import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
from GA import run_ga_interface
from G_NEH_S import run_g_neh_s_interface
from MILP import solve_algorithm5_cplex

# ==========================================================
# ================== GA FUNCTIONS AREA =====================
# ==========================================================

def computeCmax(seq, P, Incompat, Ts):
    nM = P.shape[1]
    nJ = len(seq)
    machineReadyTime = np.zeros(nM)
    jobReadyTime = np.zeros(int(np.max(seq)) + 1)
    lastJobOnM = np.zeros(nM, dtype=int)

    for jIdx in range(nJ):
        job = int(seq[jIdx])
        for m in range(nM):
            cleaningTime = 0
            if lastJobOnM[m] != 0:
                prevJob = lastJobOnM[m]
                cleaningTime = Ts[prevJob - 1, job - 1]

            startTime = max(machineReadyTime[m] + cleaningTime, jobReadyTime[job])
            endTime = startTime + P[job - 1, m]

            machineReadyTime[m] = endTime
            jobReadyTime[job] = endTime
            lastJobOnM[m] = job
    return np.max(machineReadyTime)

def tournamentSelection(pop, fitness, k):
    idx = np.random.choice(pop.shape[0], k, replace=False)
    bIdx = np.argmin(fitness[idx])
    return pop[idx[bIdx]].copy()

def orderCrossover(p1, p2):
    n = len(p1)
    pts = np.sort(np.random.choice(n, 2, replace=False))
    child1 = fillChild(p1[pts[0]:pts[1]+1], p2, pts)
    child2 = fillChild(p2[pts[0]:pts[1]+1], p1, pts)
    return child1, child2

def fillChild(sub, parent, pts):
    n = len(parent)
    child = np.zeros(n, dtype=int)
    child[pts[0]:pts[1]+1] = sub
    remaining = [item for item in parent if item not in sub]
    all_idx = list(range(pts[1]+1, n)) + list(range(0, pts[0]))
    for i, idx in enumerate(all_idx):
        child[idx] = remaining[i]
    return child

def smartSwapMutation(seq, pm, P, Incompat, Ts):
    mutated = seq.copy()
    if np.random.rand() < pm:
        nJ = len(seq)
        maxTsVal = -1
        targetIdx = np.random.randint(0, nJ)
        for jIdx in range(1, nJ):
            currJob = int(seq[jIdx])
            prevJob = int(seq[jIdx-1])
            if Incompat[prevJob - 1, currJob - 1] == 1:
                currentCleaning = Ts[prevJob - 1, currJob - 1]
                if currentCleaning > maxTsVal:
                    maxTsVal = currentCleaning
                    targetIdx = jIdx
        if targetIdx > 0:
            swapIdx = targetIdx - 1
            mutated[swapIdx], mutated[targetIdx] = mutated[targetIdx], mutated[swapIdx]
    return mutated



st.set_page_config(page_title="Ordonancement de la production", layout="wide")

st.title("Ordonancement de la production")

# 🎨 Appel du fichier CSS externe pour appliquer les ombres et effets esthétiques
with open("style.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


st.markdown("""
<style>

/* ================================
   🎨 Couleurs des boutons d'algorithmes
   ================================ */

/* Bouton 1 - G-NEH-S */
div[data-testid="stPopover"] button:nth-of-type(1) {
    background-color: #2563EB !important;
    color: white !important;
    border: none !important;
}

/* Bouton 2 - GA + G-NEH-S */
div[data-testid="stPopover"] button:nth-of-type(2) {
    background-color: #7C3AED !important;
    color: white !important;
    border: none !important;
}

/* Bouton 3 - Génetique Robuste */
div[data-testid="stPopover"] button:nth-of-type(3) {
    background-color: #0891B2 !important;
    color: white !important;
    border: none !important;
}

/* Bouton 4 - GA */
div[data-testid="stPopover"] button:nth-of-type(4) {
    background-color: #059669 !important;
    color: white !important;
    border: none !important;
}

/* Bouton 5 - MILP / Algorithme 5 */
div[data-testid="stPopover"] button:nth-of-type(5) {
    background-color: #D97706 !important;
    color: white !important;
    border: none !important;
}


/* Effet Hover */
div[data-testid="stPopover"] button:hover {
    filter: brightness(1.12);
    transform: translateY(-2px);
    box-shadow: 0 5px 12px rgba(0,0,0,0.18);
}


/* Style professionnel unifié */
div[data-testid="stPopover"] button {
    border-radius: 9px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}

</style>
""", unsafe_allow_html=True)


# =========================
# 1. Saisie de la taille
# =========================
st.sidebar.header("⚙️ Paramètres")
# =========================
n_jobs = st.sidebar.number_input("nombre des taches (Jobs)", 2, 50, 5)
n_machines = st.sidebar.number_input("nombre des machines (Machines)", 2, 10, 3)
simulation_speed = st.sidebar.slider(
    "⚡ Vitesse de simulation",
    min_value=1,
    max_value=50,
    value=1,
    step=1,
    format="%dx"
)

if "sim_start_time" in st.session_state:
	# Temps réel écoulé
	real_elapsed_time = (
		datetime.now() - st.session_state.sim_start_time
	).total_seconds()
	# Temps simulé après application de la vitesse
	sim_duration = real_elapsed_time * simulation_speed
	
	minutes = int(sim_duration // 60)
	seconds = int(sim_duration % 60)
	
	st.info(
		f"⏱️ Temps de simulation : {minutes:02d} min {seconds:02d} sec "
		f" | Vitesse : {simulation_speed}x"
	)
else:
    st.warning("La simulation n'a pas été lancée depuis la page d'accueil.")










# ==========================================================
# Mise à jour de la simulation selon la vitesse de simulation
# 1x  = mise à jour toutes les 1 seconde
# 2x  = mise à jour toutes les 0,5 seconde
# 10x = mise à jour toutes les 0,1 seconde
# ==========================================================
refresh_interval = max(100, int(5000 / simulation_speed))

st_autorefresh(
    interval=refresh_interval,
    key="refresh_clock"
)

# =========================
# 2. Bouton de création des tables
# =========================
if st.button("Crée des tables"):

    # Sauvegarde de la taille
    st.session_state.n_jobs = n_jobs
    st.session_state.n_machines = n_machines

    # =========================
    # 3. Création de Pij
    # =========================
    Pij = pd.DataFrame(
        np.random.randint(1, 99, size=(n_jobs, n_machines)),
        columns=[f"M{i+1}" for i in range(n_machines)],
        index=[f"Job {i+1}" for i in range(n_jobs)]
    )




    # =========================
    # 4. Création de Ts (matrice de setup)
    # =========================
    Ts = pd.DataFrame(
        np.random.randint(1, 99, size=(n_jobs, n_jobs)),
        columns=[f"Job {i+1}" for i in range(n_jobs)],
        index=[f"Job {i+1}" for i in range(n_jobs)]
    )
    
   # Ajouter ce code juste après la création de la matrice Ts
   # np.where(condition, valeur si vraie, valeur si fausse)
    incomp_values = np.where(Ts.values > 0, 1, 0)
    Incompatibilite = pd.DataFrame(
        incomp_values,
        columns=[f"Job {i+1}" for i in range(n_jobs)],
        index=[f"Job {i+1}" for i in range(n_jobs)]
    )








    


    
    
    # =========================
    # 5. Sequence (initial)
    # =========================

    sequence = list(range(1, n_jobs + 1))
    st.session_state.sequence = sequence
    st.session_state.sequence_df = pd.DataFrame(
    [sequence],
    columns=[f"J{i+1}" for i in range(n_jobs)]
)




    # Stockage dans session_state
    st.session_state.Pij = Pij
    st.session_state.Ts = Ts
    st.session_state.Incompatibilite = Incompatibilite  # Ajouter cette ligne pour le stockage
    
    st.success("Tables créées avec succès")

# =========================
# 6. Affichage des tables
# =========================

# ==========================================================
# 📂 Import des matrices depuis des fichiers TXT séparés
# ==========================================================

def read_matrix_txt(uploaded_file):
    content = uploaded_file.read().decode("utf-8")

    rows = []

    for line in content.splitlines():
        line = line.strip()

        if not line:
            continue

        row = [float(x) for x in line.replace(",", " ").split()]
        rows.append(row)

    if not rows:
        raise ValueError("Le fichier est vide.")

    # Vérifier que toutes les lignes ont la même longueur
    n_cols = len(rows[0])

    if any(len(row) != n_cols for row in rows):
        raise ValueError("Toutes les lignes doivent avoir le même nombre de colonnes.")

    return np.array(rows)
	
if "Pij" in st.session_state:

    col_title, col_upload = st.columns([2, 1])

with col_title:
    st.subheader("📊 Pij (Temps de traitement)")

with col_upload:
    pij_file = st.file_uploader(
        "📂 Importer Pij",
        type=["txt"],
        key="pij_txt_file"
    )
if pij_file is not None:
    try:
        matrix = read_matrix_txt(pij_file)

        Pij = pd.DataFrame(
            matrix,
            columns=[f"M{i+1}" for i in range(matrix.shape[1])],
            index=[f"Job {i+1}" for i in range(matrix.shape[0])]
        )

        st.session_state.Pij = Pij
        st.session_state.n_jobs = matrix.shape[0]
        st.session_state.n_machines = matrix.shape[1]

        st.success("✅ Matrice Pij importée avec succès.")

    except Exception as e:
        st.error(f"❌ Erreur Pij : {e}")
    edited_pij = st.data_editor(
        st.session_state.Pij,
        key="Pij_editor",
        use_container_width=True,
        num_rows="dynamic"
)
    st.session_state.Pij = edited_pij
    
    
if "Ts" in st.session_state:

    col_title, col_upload = st.columns([5, 1])

with col_title:
    st.subheader("Ts (Temps de préparation / stérilisation)")

with col_upload:
    ts_file = st.file_uploader(
        "📂 Importer Ts",
        type=["txt"],
        key="ts_txt_file"
    )
if ts_file is not None:
    try:
        matrix = read_matrix_txt(ts_file)

        Ts = pd.DataFrame(
            matrix,
            columns=[f"Job {i+1}" for i in range(matrix.shape[1])],
            index=[f"Job {i+1}" for i in range(matrix.shape[0])]
        )

        st.session_state.Ts = Ts

        # Mise à jour automatique de Incompatibilité
        st.session_state.Incompatibilite = pd.DataFrame(
            np.where(matrix > 0, 1, 0),
            columns=Ts.columns,
            index=Ts.index
        )

        st.success("✅ Matrice Ts importée avec succès.")

    except Exception as e:
        st.error(f"❌ Erreur Ts : {e}")
    edited_ts = st.data_editor(
        st.session_state.Ts,
        key="Ts_editor",
        use_container_width=True
)
    st.session_state.Ts = edited_ts

# Mise à jour immédiate de la matrice d'incompatibilité selon la dernière modification de l'utilisateur
    st.session_state.Incompatibilite = pd.DataFrame(
        np.where(edited_ts.values > 0, 1, 0),
        columns=edited_ts.columns,
        index=edited_ts.index
    )


# ==========================================
# Ajouter ce code juste sous la fin de la condition d'affichage de la matrice Ts
# ==========================================
if "Incompatibilite" in st.session_state:

    st.subheader("❌ Matrice d'incompatibilité (0 : compatible, 1 : incompatible)")
    edited_incomp = st.data_editor(
        st.session_state.Incompatibilite,
        key="Incompatibilite_editor",
        use_container_width=True,
        disabled=True # matrice miroir en lecture seule ; supprimer cette ligne pour autoriser la modification par l'utilisateur
    )
    st.session_state.Incompatibilite = edited_incomp
    











# ==========================================
# 5 & 6. Sequence (génération et modification de la séquence)
# ==========================================

if "sequence_df" in st.session_state:
    st.divider() 
    
    col_title, col_btn = st.columns([3, 1])
    
    with col_title:
        st.subheader("Modifier la Séquence")
    
    with col_btn:
        # Utilisation d'un popover pour créer une liste déroulante contenant les algorithmes
        with st.popover("Choisir Algorithme", icon=":material/alt_route:", type="primary"):
            st.write("Sélectionnez un Algorithme :")
            
            # Création des cinq boutons
            algo_choice = None
            
            

            # 2. Bouton d'exécution de l'algorithme
            if st.button("G-NEH-S", type="primary"): 
                if "Pij" in st.session_state and "Ts" in st.session_state:
                    
                    # Exécution des calculs à partir des matrices actuelles de session_state
                    optimized_seq, detected_groups = run_g_neh_s_interface(
                        st.session_state.Pij, 
                        st.session_state.Ts, 
                        st.session_state.Incompatibilite
                    )
                    
                    # Mise à jour de session_state avec la nouvelle séquence (base 1)
                    current_n_jobs = len(optimized_seq)
                    st.session_state.sequence = optimized_seq
                    st.session_state.sequence_df = pd.DataFrame(
                        [optimized_seq], 
                        columns=[f"J{i+1}" for i in range(current_n_jobs)]
                    )
                    
                    # Affichage d'un message de succès personnalisé contenant le nombre de groupes détectés
                    st.success(f"✨ G-NEH-S calculé avec succès ! Groupes détectés: {detected_groups}")
                    st.rerun()
                else:
                    st.error("⚠️ Veuillez d'abord créer les tables avant de lancer l'algorithme.")            
            
            
            
            # =================================================================
            # Option algorithme (GA + G-NEH-S) interactive (se déplie et se replie au clic)
            # =================================================================            
            # 1. Initialisation de la variable d'état d'ouverture/fermeture du menu de réglages dans session_state
            if "show_ga_settings" not in st.session_state:
                st.session_state.show_ga_settings = False

            # 2. Bouton principal contrôlant le dépliage et le repliage
            # Au clic, il inverse son état (de True à False et inversement) puis relance le script pour mettre à jour l'interface
            if st.button("GA + G-NEH-S", type="primary"):
                st.session_state.show_ga_settings = not st.session_state.show_ga_settings
                st.rerun()

            # 3. Bloc affiché uniquement lorsque l'état est True (déplié)
            if st.session_state.show_ga_settings:
                # On place les réglages dans un conteneur visuellement distinct (container)
                with st.container(border=True):
                    st.markdown("#### ⚙️ Réglage des Paramètres")
                    
                    # Initialisation des valeurs par défaut des paramètres dans session_state pour les protéger contre l'Autorefresh
                    if "ga_pop_size" not in st.session_state: st.session_state.ga_pop_size = 100
                    if "ga_n_gen" not in st.session_state: st.session_state.ga_n_gen = 200
                    if "ga_pc" not in st.session_state: st.session_state.ga_pc = 0.85
                    if "ga_pm" not in st.session_state: st.session_state.ga_pm = 0.06

                    # Champs de saisie liés à des clés
                    pop_size = st.number_input("Taille de la population", min_value=4, max_value=500, step=10, key="ga_pop_size")
                    n_gen = st.number_input("Nombre de générations", min_value=1, max_value=1000, step=10, key="ga_n_gen")
                    pc = st.slider("Taux de croisement (pc)", min_value=0.0, max_value=1.0, step=0.05, key="ga_pc")
                    pm = st.slider("Taux de mutation (pm)", min_value=0.0, max_value=1.0, step=0.01, key="ga_pm")

                    st.write("") # espacement esthétique

                    # Bouton d'exécution effective de l'algorithme dans le conteneur déplié
                    if st.button("Lancer l'algorithme", type="secondary", key="run_hybrid_ga_btn"):
                        if "Pij" in st.session_state and "Ts" in st.session_state:
                            with st.spinner("Exécution de l'algorithme hybride en cours..."):
                                
                                from GA_G_NEH_S import run_ga_g_neh_s_interface
                                optimized_seq, best_cmax = run_ga_g_neh_s_interface(
                                    st.session_state.Pij,
                                    st.session_state.Ts,
                                    st.session_state.Incompatibilite,
                                    popSize=int(pop_size),
                                    nGen=int(n_gen),
                                    pc=pc,
                                    pm=pm
                                )
                                
                                current_n_jobs = len(optimized_seq)
                                st.session_state.sequence = optimized_seq
                                st.session_state.sequence_df = pd.DataFrame(
                                    [optimized_seq], 
                                    columns=[f"J{i+1}" for i in range(current_n_jobs)]
                                )
                                
                                st.success(f"✨ Calcul réussi ! Valeur de Cmax obtenue : {best_cmax} secondes")
                                st.rerun()
                        else:
                            st.error("⚠️ Veuillez d'abord créer les tables avant de lancer l'algorithme.")


# =================================================================
            # Option algorithme (Génetique Robuste) amélioré, isolé et résistant à l'Autorefresh
            # ================================================================= 
            if "show_robust_settings" not in st.session_state:
                st.session_state.show_robust_settings = False

            if st.button("Génetique Robuste", type="primary"):
                st.session_state.show_robust_settings = not st.session_state.show_robust_settings
                st.rerun()

            if st.session_state.show_robust_settings:
                with st.container(border=True):
                    if "Pij" in st.session_state and "Ts" in st.session_state:
                        from Robuste import run_robust_ga_interface
                        run_robust_ga_interface(
                            st.session_state.Pij,
                            st.session_state.Ts,
                            st.session_state.Incompatibilite
                        )
                        
                        # Réception du résultat complet venant de l'arrière-plan et application immédiate aux tables
                        if "optimized_robust_seq" in st.session_state:
                            robust_seq = st.session_state.pop("optimized_robust_seq")
                            current_n_jobs = len(robust_seq)
                            st.session_state.sequence = robust_seq
                            st.session_state.sequence_df = pd.DataFrame(
                                [robust_seq], 
                                columns=[f"J{i+1}" for i in range(current_n_jobs)]
                            )
                            st.success("🏆 Meilleure séquence robuste appliquée avec succès aux diagrammes !")
                            st.rerun()
                    else:
                        st.error("⚠️ Veuillez d'abord créer les tables avant de lancer l'algorithme.")
            # =================================================================            


            run_ga_interface()





            
#-----------------------
            
            if st.button("MILP", type="primary"):
                if "Pij" not in st.session_state or "Ts" not in st.session_state or "Incompatibilite" not in st.session_state:
                    st.error("⚠️ Veuillez d'abord créer les tables avant de lancer Algorithme 5.")
                else:
                    from MILP import solve_algorithm5_cplex

                    with st.spinner("🔄 Résolution du modèle d'optimisation..."):
                        try:
                            optimized_seq, best_cmax = solve_algorithm5_cplex(
                                st.session_state.Pij,
                                st.session_state.Ts,
                                st.session_state.Incompatibilite
                            )

                            current_n_jobs = len(optimized_seq)
                            st.session_state.sequence = optimized_seq
                            st.session_state.sequence_df = pd.DataFrame(
                                [optimized_seq],
                                columns=[f"J{i+1}" for i in range(current_n_jobs)]
                            )
                            st.session_state.algorithm5_cmax = best_cmax

                            st.success(f"✅ Algorithme 5 terminé ! Cmax = {best_cmax:.2f}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erreur pendant l'exécution de Algorithme 5 : {e}")



	
    # Affichage du tableau modifiable
    edited_seq = st.data_editor(
        st.session_state.sequence_df,
        key="Seq_editor",
        use_container_width=True
    )
    
    if edited_seq is not None:
        try:
            st.session_state.sequence_df = edited_seq
            st.session_state.sequence = [int(x) for x in edited_seq.values.flatten().tolist()]
        except ValueError:
            st.error("Veuillez saisir uniquement des nombres")



# =========================
# 7. Calcul et affichage du Gantt Chart
# =========================
if "machine_faults" not in st.session_state:
    st.session_state.machine_faults = {f"Machine {i+1}": [] for i in range(5)}

if "Pij" in st.session_state and "sequence" in st.session_state:
    st.subheader("Gantt Chart (Progressif avec gestion des pannes)")

    # Extraction des données depuis session_state
    pij_data = st.session_state.Pij.values
    ts_data = st.session_state.Ts.values
    sequence = [int(i) - 1 for i in st.session_state.sequence] # conversion de la séquence en index (base 0)
    
    n_j = len(sequence)
    n_m = st.session_state.n_machines

    # Matrices pour stocker les heures de début et de fin ajustées
    start_times = np.zeros((n_j, n_m))
    end_times = np.zeros((n_j, n_m))

    # Obtention du temps de simulation actuel (secondes)
    if "sim_start_time" in st.session_state:
        real_elapsed_time = (
            datetime.now() - st.session_state.sim_start_time
        ).total_seconds()
        # Application de la vitesse de simulation
        current_sim_time = real_elapsed_time * simulation_speed
    else:
        current_sim_time = 0

    # Calcul de l'ordonnancement dynamique (Flow Shop avec décalage dû aux pannes)
    for j_idx, job_id in enumerate(sequence):
        for m in range(n_m):
            # Temps de traitement d'origine requis
            proc_time = pij_data[job_id, m]
            
            # Temps de préparation (Setup)
            setup_time = 0
            if j_idx > 0:
                prev_job_id = sequence[j_idx - 1]
                setup_time = ts_data[prev_job_id, job_id]

            # 1. Détermination de l'heure de début initiale (logique classique)
            if j_idx == 0 and m == 0:
                s_t = 0
            elif j_idx == 0: 
                s_t = end_times[j_idx, m-1]
            elif m == 0: 
                s_t = end_times[j_idx-1, m] + setup_time
            else: 
                s_t = max(end_times[j_idx-1, m] + setup_time, end_times[j_idx, m-1])
            
            # 2. Calcul de l'effet des pannes imbriquées et décalage du temps (la nouveauté et le point clé)
            machine_key = f"Machine {m+1}"
            if "machine_faults" in st.session_state and machine_key in st.session_state.machine_faults:
                faults = st.session_state.machine_faults[machine_key]
                
                # On simule l'écoulement du temps pas à pas pour vérifier si l'opération est affectée par une panne survenant pendant son exécution
                current_start = s_t
                remaining_proc_time = proc_time
                current_time_pointer = current_start
                
                # Tableau des pannes trié par heure de début
                sorted_faults = sorted(faults, key=lambda x: x["start"])
                
                for fault in sorted_faults:
                    f_start = fault["start"]
                    f_end = fault["end"] if fault["end"] is not None else current_sim_time
                    
                    # Si la panne survient pendant l'exécution de la tâche (ou chevauche son heure de début prévue)
                    # On augmente l'heure de fin de la durée de la panne
                    if f_start < current_time_pointer + remaining_proc_time and f_end > current_time_pointer:
                        # Calcul de la part de la panne située dans la période d'exécution de la tâche
                        overlap_start = max(f_start, current_time_pointer)
                        overlap_end = min(f_end, current_time_pointer + remaining_proc_time)
                        
                        # Durée de la panne ayant provoqué l'arrêt de la machine
                        fault_duration = f_end - f_start
                        
                        # Décalage du temps : la tâche sera retardée de la durée totale de la panne
                        current_time_pointer += fault_duration

                # Heure de début finale et heure de fin après prise en compte des retards dus aux pannes
                start_times[j_idx, m] = current_start
                end_times[j_idx, m] = current_time_pointer + remaining_proc_time
            else:
                # S'il n'y a pas de pannes pour la machine, le calcul est normal
                start_times[j_idx, m] = s_t
                end_times[j_idx, m] = s_t + proc_time


    # Préparation des données du graphique pour Plotly
    gantt_data = []
    for j_idx, job_id in enumerate(sequence):
        for m in range(n_m):
            if start_times[j_idx, m] <= current_sim_time:
                display_end = min(end_times[j_idx, m], current_sim_time)
                
                # Ajout de la tâche normale
                gantt_data.append(dict(
                    Task=f"Machine {m+1}",
                    Start=start_times[j_idx, m],
                    Finish=display_end,
                    Resource=f"Job {job_id + 1}"
                ))

    # Ajout des périodes de panne sous forme de rectangles rouges bien visibles dans le diagramme pour expliquer l'écart temporel
    if "machine_faults" in st.session_state:
        for machine_name, faults in st.session_state.machine_faults.items():
            try:
                m_num = int(machine_name.split()[-1])
                if m_num <= n_m: 
                    for fault in faults:
                        f_start = fault["start"]
                        f_end = fault["end"] if fault["end"] is not None else current_sim_time
                        
                        if f_start <= current_sim_time:
                            gantt_data.append(dict(
                                Task=f"Machine {m_num}",
                                Start=f_start,
                                Finish=min(f_end, current_sim_time),
                                Resource="⚠️ Panne de la machine"
                            ))
            except:
                pass

    if gantt_data:
        df_gantt = pd.DataFrame(gantt_data)
        
        # Conversion des secondes en dates fictives pour Plotly
        df_gantt['Start'] = pd.to_datetime(df_gantt['Start'], unit='s')
        df_gantt['Finish'] = pd.to_datetime(df_gantt['Finish'], unit='s')

        # Personnalisation des couleurs (couleurs aléatoires pour les tâches, rouge toujours pour les pannes)
        color_discrete_map = {"⚠️ Panne de la machine": "#ff0000"}

        fig = px.timeline(
            df_gantt, 
            x_start="Start", 
            x_end="Finish", 
            y="Task", 
            color="Resource",
            color_discrete_map=color_discrete_map,
            title="Exécution dynamique en direct (effet des pannes et retards des tâches)"
        )
        
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(xaxis_title="Temps (secondes)", showlegend=True)
        fig.update_layout(xaxis=dict(tickformat="%M:%S"))
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("En attente du démarrage de la simulation ou de l'arrivée du temps de la première tâche...")








# ==========================================
#  Partie corrigée et améliorée : calcul et affichage complets et fixes avec Plotly, rapide et stable
# ==========================================
st.write("")

# 1. Initialisation de la variable d'état dans la session si elle n'existe pas
if "show_complete_gantt" not in st.session_state:
    st.session_state.show_complete_gantt = False

# 2. Boutons de contrôle de l'affichage sur une ligne élégante et espacée
# Ajout de gap="large" pour garantir une distance de sécurité claire entre les colonnes
col_gantt_btn1, col_gantt_btn2 = st.columns([1, 1], gap="large")

with col_gantt_btn1:
    if st.button("Afficher le Gantt complet", type="primary"):
        st.session_state.show_complete_gantt = True

with col_gantt_btn2:
    if st.session_state.show_complete_gantt:
        if st.button("Masquer le Diagramme", type="secondary"):
            st.session_state.show_complete_gantt = False
            st.rerun()

# 3. Si l'état est True, le diagramme complet est tracé immédiatement
if st.session_state.show_complete_gantt:
    
    # Fonction de calcul de l'ordonnancement complet fixe (sans troncature au temps actuel)
    def solve_flow_shop_static_plotly(pij, ts, job_sequence, machine_faults=None, now_sim=0.0):
        # machine_faults : pannes enregistrées {"Machine k": [{"start":..., "end":...}]}
        # Même logique que le Gantt en direct : une panne qui chevauche l'exécution d'une tâche la retarde de la durée de la panne.
        machine_faults = machine_faults or {}
        n_jobs, m_machines = pij.shape
        st_times = np.zeros((n_jobs, m_machines))
        en_times = np.zeros((n_jobs, m_machines))
        machine_free_time = np.zeros(m_machines)
        
        for i, job_idx in enumerate(job_sequence):
            for m in range(m_machines):
                p_time = pij[job_idx, m]
                setup_time = 0
                if i > 0:
                    prev_job_idx = job_sequence[i-1]
                    setup_time = ts[prev_job_idx, job_idx]
                
                ready_after_setup = machine_free_time[m] + setup_time
                
                if m == 0:
                    st_times[job_idx, m] = ready_after_setup
                else:
                    st_times[job_idx, m] = max(ready_after_setup, en_times[job_idx, m-1])
                
                # Prise en compte des pannes de la machine
                pointer = st_times[job_idx, m]
                for fault in sorted(machine_faults.get(f"Machine {m+1}", []), key=lambda x: x["start"]):
                    f_start = fault["start"]
                    f_end = fault["end"] if fault["end"] is not None else now_sim
                    if f_start < pointer + p_time and f_end > pointer:
                        pointer += (f_end - f_start)

                en_times[job_idx, m] = pointer + p_time
                machine_free_time[m] = en_times[job_idx, m]

        return st_times, en_times, n_jobs, m_machines

    # Récupération des données en direct et transmission au calcul
    static_pij = st.session_state.Pij.values
    static_ts = st.session_state.Ts.values
    static_seq = [int(x) - 1 for x in st.session_state.sequence]
    
    _faults = st.session_state.get("machine_faults", {})
    _now_sim = current_sim_time if "current_sim_time" in globals() else 0.0
    s_times, e_times, nj, nm = solve_flow_shop_static_plotly(static_pij, static_ts, static_seq, _faults, _now_sim)
    
    # Construction du tableau de données officiel pour Plotly
    static_gantt_data = []
    
    for i, job_idx in enumerate(static_seq):
        for m in range(nm):
            # 1. Ajout du temps de préparation (Setup Time) en gris s'il existe
            if i > 0:
                prev_job_idx = static_seq[i-1]
                setup_duration = static_ts[prev_job_idx, job_idx]
                if setup_duration > 0:
                    # L'heure de début du setup est l'heure de libération de la machine précédente (égale à l'heure de début de la tâche actuelle moins le temps de setup)
                    setup_start = s_times[job_idx, m] - setup_duration
                    if setup_start >= 0:
                        static_gantt_data.append(dict(
                            Machine=f"Machine {m+1}",
                            Start=pd.to_datetime(setup_start, unit='s'),
                            Finish=pd.to_datetime(s_times[job_idx, m], unit='s'),
                            Type="Temps d'opération (Setup)"
                        ))
            
            # 2. Ajout de la période de fonctionnement normale du produit
            static_gantt_data.append(dict(
                Machine=f"Machine {m+1}",
                Start=pd.to_datetime(s_times[job_idx, m], unit='s'),
                Finish=pd.to_datetime(e_times[job_idx, m], unit='s'),
                Type=f"Job {job_idx + 1}"
            ))
            
    # Ajout des pannes sous forme de rectangles rouges
    for _m_name, _flist in _faults.items():
        try:
            _m_num = int(_m_name.split()[-1])
        except Exception:
            continue
        if _m_num > nm:
            continue
        for _f in _flist:
            _fe = _f["end"] if _f["end"] is not None else _now_sim
            if _fe > _f["start"]:
                static_gantt_data.append(dict(
                    Machine=f"Machine {_m_num}",
                    Start=pd.to_datetime(_f["start"], unit='s'),
                    Finish=pd.to_datetime(_fe, unit='s'),
                    Type="⚠️ Panne de la machine"
                ))

    if static_gantt_data:
        df_static_gantt = pd.DataFrame(static_gantt_data)
        
        # Palette personnalisée : le temps de setup en gris foncé distinctif et les produits avec leurs couleurs habituelles
        color_map = {"Temps d'opération (Setup)": "#555555", "⚠️ Panne de la machine": "#ff0000"}
        
        fig_static = px.timeline(
            df_static_gantt,
            x_start="Start",
            x_end="Finish",
            y="Machine",
            color="Type",
            color_discrete_map=color_map,
            # Utilisation de la balise span pour colorer la valeur en rouge à titre d'exemple
            title=f"Diagramme de Gantt Complet statique | Cmax = <span style='color:red; font-weight:bold;'>{int(np.max(e_times))}</span> secondes"
        )
        
        fig_static.update_yaxes(autorange="reversed")
        fig_static.update_layout(
            xaxis_title="Temps total de l'ordonnancement (minutes:secondes)",
            xaxis=dict(tickformat="%M:%S"),
            showlegend=True,
            height=400
        )
        
        # Affichage immédiat du diagramme en toute stabilité
        st.plotly_chart(fig_static, use_container_width=True, key="static_gantt_plotly")
# ==========================================================
# 📊 TAUX D'UTILISATION COMPLET DES MACHINES
# ==========================================================

if "show_machine_utilization" not in st.session_state:
    st.session_state.show_machine_utilization = False

col_util1, col_util2 = st.columns([1, 1], gap="large")

with col_util1:
    if st.button(
        "Afficher les taux d'utilisation des machines",
        type="primary"
    ):
        st.session_state.show_machine_utilization = True

with col_util2:
    if st.session_state.show_machine_utilization:
        if st.button("Masquer les taux", type="secondary"):
            st.session_state.show_machine_utilization = False
            st.rerun()


# ==========================================================
# TAUX COMPLET — basé sur le Gantt complet
# ==========================================================

if st.session_state.show_machine_utilization:

    # Cmax COMPLET de la planification
    Cmax = float(np.max(e_times))

    st.subheader("📊 Taux d'utilisation complet des machines")

    utilization_data = []

    for m in range(nm):

        processing_time = 0.0
        setup_time = 0.0

        # ------------------------------------------
        # Temps de traitement + TS
        # ------------------------------------------
        for i, job_idx in enumerate(static_seq):

            # Temps de production
            processing_time += float(static_pij[job_idx, m])

            # Temps de setup / TS
            if i > 0:
                prev_job_idx = static_seq[i - 1]
                setup_time += float(static_ts[prev_job_idx, job_idx])

        # ------------------------------------------
        # Temps d'arrêt / panne
        # ------------------------------------------
        breakdown_time = 0.0

        machine_key = f"Machine {m + 1}"

        if "machine_faults" in st.session_state:

            faults = st.session_state.machine_faults.get(
                machine_key, []
            )

            for fault in faults:

                f_start = float(fault["start"])

                if fault["end"] is not None:
                    f_end = float(fault["end"])
                else:
                    f_end = Cmax

                # Limiter la panne à Cmax
                f_start = max(0, min(f_start, Cmax))
                f_end = max(0, min(f_end, Cmax))

                if f_end > f_start:
                    breakdown_time += f_end - f_start

        # ------------------------------------------
        # Inactivité = temps restant
        # ------------------------------------------
        idle_time = Cmax - (
            processing_time
            + setup_time
            + breakdown_time
        )

        idle_time = max(0, idle_time)

        # ------------------------------------------
        # Pourcentages
        # ------------------------------------------
        processing_pct = (processing_time / Cmax) * 100
        idle_pct = (idle_time / Cmax) * 100
        setup_pct = (setup_time / Cmax) * 100
        breakdown_pct = (breakdown_time / Cmax) * 100

        utilization_data.append({
            "Machine": f"Machine {m + 1}",
            "Processing": processing_pct,
            "Idle": idle_pct,
            "TS": setup_pct,
            "Arrêt": breakdown_pct
        })

    # ======================================================
    # AFFICHAGE DES DONUTS
    # ======================================================

    cols = st.columns(nm)

    for m, data in enumerate(utilization_data):

        with cols[m]:

            values = [
                data["Processing"],
                data["Idle"],
                data["TS"],
                data["Arrêt"]
            ]

            labels = [
                "Machine en marche",
                "Inactif",
                "TS",
                "Arrêt"
            ]

            fig_donut = px.pie(
                values=values,
                names=labels,
                hole=0.62
            )

            fig_donut.update_traces(
                textinfo="percent",
                textposition="inside"
            )

            fig_donut.update_layout(
                title=f"<b>{data['Machine']}</b>",
                showlegend=True,
                height=350,
                margin=dict(
                    l=10,
                    r=10,
                    t=50,
                    b=10
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.25,
                    xanchor="center",
                    x=0.5
                )
            )

            st.plotly_chart(
                fig_donut,
                use_container_width=True,
                key=f"complete_utilization_{m}"
            )


# =========================
# 8. Tableau de suivi de l'état des machines et des produits terminés
# =========================
st.divider()

# S'assurer d'abord que les tables et la séquence ont été créées avec succès avant d'afficher le tableau
if "Pij" in st.session_state and "sequence" in st.session_state:
    
    # Récupération sûre des variables pour que Python les reconnaisse dans cette portée
    sequence = [int(i) - 1 for i in st.session_state.sequence] # conversion de la séquence en index (base 0)
    n_machines = st.session_state.n_machines

# 1. Passage à 3 colonnes
    col1, col2, col3 = st.columns([1, 1.5, 1.2])

    with col1:
        st.subheader("🖥️ état actuel des machines")
        machine_status = []
        for m in range(n_machines):
            current_job = "arrêté (inactif)"
            for j_idx, job_id in enumerate(sequence):
                if start_times[j_idx, m] <= current_sim_time <= end_times[j_idx, m]:
                    current_job = f"🔨 Job {job_id + 1}"
                    break
            machine_status.append({"Machine": f"Machine {m+1}", "produit actuel": current_job})
        st.table(pd.DataFrame(machine_status))

    with col2:
        st.subheader("✅ Produits finis")
        completed_jobs = []
        for j_idx, job_id in enumerate(sequence):
            finish_time_on_last_machine = end_times[j_idx, n_machines - 1]
            if current_sim_time >= finish_time_on_last_machine:
                completed_jobs.append({
                    "produit": f"Job {job_id + 1}",
                    "date de debut (s)": f"{start_times[j_idx, 0]:.1f}", 
                    "date de fin (s)": f"{finish_time_on_last_machine:.1f}", 
                    "etat": "c'est terminé"
                })
        if completed_jobs:
            st.dataframe(pd.DataFrame(completed_jobs), use_container_width=True)
        else:
            st.info("Aucun produit entièrement terminé pour le moment.")

    # 2. Nouvelle troisième colonne (contrôlée par le bouton Gantt Complete)
    with col3:
        if st.session_state.get("show_complete_gantt", False):
            st.subheader("📋 Total TS / Machine")
            
            static_ts = st.session_state.Ts.values
            static_seq = [int(x) - 1 for x in st.session_state.sequence]
            
            machine_ts_totals = {f"Machine {m+1}": 0.0 for m in range(n_machines)}
            
            for i in range(1, len(static_seq)):
                prev_job = static_seq[i - 1]
                current_job = static_seq[i]
                ts_value = float(static_ts[prev_job, current_job])
                for m in range(n_machines):
                    machine_ts_totals[f"Machine {m+1}"] += ts_value

            df_ts_machines = pd.DataFrame([
                {"Machine": m_name, "Total TS (s)": total_ts}
                for m_name, total_ts in machine_ts_totals.items()
            ])
            
            st.dataframe(df_ts_machines, use_container_width=True, hide_index=True)
	
	
	
	
	
	
	

    # =========================
    # 9. Statistiques rapides
    # =========================
    if completed_jobs:
        progress = len(completed_jobs) / len(sequence)
        st.progress(progress)
        st.write(f"📊 taux d'avancement global: {progress*100:.1f}%")

else:
    # Message affiché à l'utilisateur à l'ouverture de la page pour la première fois avant la génération des données
    st.info("⏳ Veuillez d'abord cliquer sur le bouton « Créer des tables » pour générer des données et afficher l'état de la machine.")
