import numpy as np
from docplex.mp.model import Model


def _to_array(data, dtype=float):
    if hasattr(data, "to_numpy"):
        return np.asarray(data.to_numpy(), dtype=dtype)
    return np.asarray(data, dtype=dtype)


def solve_algorithm5_cplex(Pij, Ts, Incompatibilite, time_limit=60):
    """
    Résout le modèle de Flow Shop avec CPLEX (docplex).
    
    Parameters:
    -----------
    Pij : array-like (n, m)
        Matrix of processing times.
    Ts : array-like (n, n)
        Matrix of sequence-dependent setup times.
    Incompatibilite : array-like (n, n)
        Binary matrix for lot incompatibility (1 if incompatible, 0 otherwise).
    time_limit : int
        Time limit in seconds for CPLEX solver.
        
    Returns:
    --------
    sequence_1_based : list
        The optimal sequence of jobs (1-indexed).
    best_cmax : float
        The minimum makespan (Cmax).
    """
    P = _to_array(Pij, float)
    ts = _to_array(Ts, float)
    Y = _to_array(Incompatibilite, float)

    n, m = P.shape

    # Vérification des dimensions des matrices
    if ts.shape != (n, n) or Y.shape != (n, n):
        raise ValueError(f"Dimensions des matrices incompatibles. Ts et Incompatibilite doivent être de taille ({n}, {n}).")

    # 1. Création du modèle CPLEX
    mdl = Model(name="FlowShop_Scheduling")
    mdl.time_limit = time_limit  # Définition de la limite de temps en secondes

    # 2. Définition des variables
    # X[i, k] = 1 si la tâche i est placée à la position k
    X = mdl.binary_var_matrix(n, n, name="X")

    # W[i, i2, k] = 1 si la tâche i puis i2 sont exécutées aux positions k et k+1
    W = mdl.binary_var_cube(n, n, range(n - 1), name="W")

    # S[k, j] : instant de début de la position k sur la machine j
    S = mdl.continuous_var_matrix(n, m, lb=0.0, name="S")

    # Cmax : temps d'achèvement total (Makespan)
    cmax = mdl.continuous_var(lb=0.0, name="Cmax")

    # 3. Formulation de la fonction objectif (minimiser Cmax)
    mdl.minimize(cmax)

    # 4. Ajout des contraintes (Constraints)

    # Contrainte 1 : chaque tâche est placée à une seule position
    for i in range(n):
        mdl.add_constraint(mdl.sum(X[i, k] for k in range(n)) == 1, ctname=f"job_{i}_once")

    # Contrainte 2 : chaque position contient une seule tâche
    for k in range(n):
        mdl.add_constraint(mdl.sum(X[i, k] for i in range(n)) == 1, ctname=f"pos_{k}_once")

    # Contrainte 3 : liaison des variables de succession W aux variables X
    for i in range(n):
        for i2 in range(n):
            for k in range(n - 1):
                mdl.add_constraint(W[i, i2, k] >= X[i, k] + X[i2, k + 1] - 1, ctname=f"link_W_{i}_{i2}_{k}")

    # Contrainte 4 : le début de la première position sur la première machine est égal à 0
    mdl.add_constraint(S[0, 0] == 0, ctname="start_0_0")

    # Contrainte 5 : transition entre positions sur la même machine (inclut temps de traitement et de réglage)
    for k in range(n - 1):
        for j in range(m):
            proc_time = mdl.sum(P[i, j] * X[i, k] for i in range(n))
            setup_time = mdl.sum(Y[i, i2] * ts[i, i2] * W[i, i2, k] for i in range(n) for i2 in range(n))
            mdl.add_constraint(S[k + 1, j] >= S[k, j] + proc_time + setup_time, ctname=f"seq_mach_{k}_{j}")

    # Contrainte 6 : transition entre machines pour la même position
    for k in range(n):
        for j in range(1, m):
            proc_time_prev = mdl.sum(P[i, j - 1] * X[i, k] for i in range(n))
            mdl.add_constraint(S[k, j] >= S[k, j - 1] + proc_time_prev, ctname=f"seq_job_{k}_{j}")

    # Contrainte 7 : définition de Cmax selon l'instant de fin de la dernière position sur toutes les machines
    for k in range(n):
        for j in range(m):
            proc_time = mdl.sum(P[i, j] * X[i, k] for i in range(n))
            mdl.add_constraint(cmax >= S[k, j] + proc_time, ctname=f"cmax_bound_{k}_{j}")

    # 5. Lancement du solveur (Solve)
    solution = mdl.solve(log_output=True)

    if solution is None:
        raise RuntimeError("CPLEX n'a pas pu trouver de solution acceptable dans les contraintes et le temps disponibles.")

    # 6. Extraction de la séquence obtenue (Sequence)
    sequence = []
    for k in range(n):
        for i in range(n):
            if solution.get_value(X[i, k]) > 0.5:
                sequence.append(i + 1)  # 1-indexed
                break

    best_cmax = solution.get_value(cmax)
    return sequence, best_cmax


# ==========================================
# Test du code sur un cas 10x5
# ==========================================
if __name__ == "__main__":
    np.random.seed(42)

    n_jobs = 10
    n_machines = 5

    # Génération de données de test
    Pij = np.random.randint(10, 50, size=(n_jobs, n_machines))
    Ts = np.random.randint(1, 10, size=(n_jobs, n_jobs))
    np.fill_diagonal(Ts, 0)
    Incompatibilite = np.random.randint(0, 2, size=(n_jobs, n_jobs))
    np.fill_diagonal(Incompatibilite, 0)

    print(f"--- Résolution du cas {n_jobs}x{n_machines} avec CPLEX ---")
    try:
        seq, cmax_val = solve_algorithm5_cplex(Pij, Ts, Incompatibilite, time_limit=30)
        print("\n" + "=" * 40)
        print(f"Séquence obtenue (Sequence) : {seq}")
        print(f"Meilleure valeur de Cmax : {cmax_val}")
        print("=" * 40)
    except Exception as e:
        print(f"Une erreur est survenue pendant la résolution : {e}")
