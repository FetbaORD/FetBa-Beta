# G_NEH_S.py
import numpy as np
import pandas as pd

def calculate_cmax_gneh(seq, P, Ts):
    """
    Fonction de calcul exact du Cmax dédiée à l'algorithme G-NEH-S.
    Elle manipule les matrices en indexation à partir de 0 (0-indexed), compatible avec Python.
    """
    if len(seq) == 0:
        return 0
    
    n = len(seq)
    m = P.shape[1]
    C = np.zeros((n, m))
    
    for k in range(n):
        job_idx = seq[k]
        for j in range(m):
            setup = 0
            # Si cette tâche n'est pas la première de la séquence
            if k > 0:
                # Récupération de la valeur Ts entre la tâche précédente et la tâche courante
                setup = Ts[seq[k-1], job_idx]
            
            if k == 0 and j == 0:
                C[k, j] = P[job_idx, j]
            elif k == 0:
                C[k, j] = C[k, j-1] + P[job_idx, j]
            elif j == 0:
                C[k, j] = C[k-1, j] + setup + P[job_idx, j]
            else:
                C[k, j] = max(C[k-1, j] + setup, C[k, j-1]) + P[job_idx, j]
                
    return C[-1, -1]


def run_internal_neh_insertion(jobs, P, Ts):
    """
    Application de la logique d'insertion NEH (NEH Insertion) standard au sein d'un même groupe.
    """
    if len(jobs) <= 1:
        return jobs
    
    # Tri décroissant initial des tâches du groupe selon la somme des temps de traitement
    job_sums = np.sum(P[jobs, :], axis=1)
    sorted_indices = np.argsort(job_sums)[::-1]
    sorted_jobs = [jobs[i] for i in sorted_indices]
    
    # Début du processus d'insertion
    best_seq = [sorted_jobs[0]]
    
    for i in range(1, len(sorted_jobs)):
        current_job = sorted_jobs[i]
        best_temp_cmax = float('inf')
        best_temp_seq = []
        
        for pos in range(len(best_seq) + 1):
            test_seq = best_seq[:pos] + [current_job] + best_seq[pos:]
            cmax = calculate_cmax_gneh(test_seq, P, Ts)
            
            if cmax < best_temp_cmax:
                best_temp_cmax = cmax
                best_temp_seq = test_seq
                
        best_seq = best_temp_seq
        
    return best_seq


def run_g_neh_s_interface(P_df, Ts_df, Incompat_df):
    """
    Fonction principale d'exécution appelée depuis le bouton de la session dans Streamlit.
    Elle reçoit les objets DataFrame, les convertit en matrices numériques et exécute le G-NEH-S complet.
    """
    # Conversion des données en matrices numpy
    P = P_df.values
    Ts = Ts_df.values
    Y = Incompat_df.values
    
    num_jobs = P.shape[0]
    
    # --- 1. Constitution des groupes (selon la compatibilité Y) ---
    groups = []
    visited = np.zeros(num_jobs, dtype=bool)
    
    for i in range(num_jobs):
        if not visited[i]:
            current_group = [i]
            visited[i] = True
            for j in range(i + 1, num_jobs):
                if not visited[j] and Y[i, j] == 0:
                    current_group.append(j)
                    visited[j] = True
            groups.append(current_group)
            
    num_groups = len(groups)
    
    # --- 2. Ordonnancement des tâches dans chaque groupe (NEH Insertion) ---
    ordered_groups = []
    group_total_p = []
    
    for g in range(num_groups):
        current_jobs = groups[g]
        ordered_seq = run_internal_neh_insertion(current_jobs, P, Ts)
        ordered_groups.append(ordered_seq)
        
        # Calcul de la somme des Pij du groupe pour l'utiliser dans le tri linéaire
        total_p = np.sum(P[current_jobs, :])
        group_total_p.append(total_p)
        
    # --- 3. Fusion linéaire des groupes (par somme des Pij décroissante) ---
    group_priority = np.argsort(group_total_p)[::-1]
    
    final_seq_0_based = []
    for g_idx in group_priority:
        final_seq_0_based.extend(ordered_groups[g_idx])
        
    # --- 4. Conversion en indexation à partir de 1 pour correspondre aux numéros de produits de l'interface (Job 1, Job 2...) ---
    final_seq_1_based = [job + 1 for job in final_seq_0_based]
    
    return final_seq_1_based, num_groups