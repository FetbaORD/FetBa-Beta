"""
Algorithme 5 - version Python sans IBM CPLEX.

Ce module reprend le modèle de CPLEX.mod et le résout avec scipy.optimize.milp.
Les données ne viennent PAS de CPLEX.dat : elles sont reçues directement depuis
Ordonancement.py (Pij, Ts et Incompatibilite).
"""

import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix


def _to_array(data, dtype=float):
    if hasattr(data, "to_numpy"):
        return np.asarray(data.to_numpy(), dtype=dtype)
    return np.asarray(data, dtype=dtype)


def solve_algorithm5(Pij, Ts, Incompatibilite):
    """Résout le modèle et retourne (sequence_1_based, Cmax)."""
    P = _to_array(Pij, float)
    ts = _to_array(Ts, float)
    Y = _to_array(Incompatibilite, float)

    if P.ndim != 2 or ts.ndim != 2 or Y.ndim != 2:
        raise ValueError("Pij, Ts et Incompatibilite doivent être des matrices 2D.")

    n, m = P.shape
    if ts.shape != (n, n):
        raise ValueError(f"Ts doit être de taille ({n}, {n}), mais vaut {ts.shape}.")
    if Y.shape != (n, n):
        raise ValueError(f"Incompatibilite doit être de taille ({n}, {n}), mais vaut {Y.shape}.")
    if n < 1 or m < 1:
        raise ValueError("Il faut au moins un job et une machine.")

    # -------------------------
    # Indexation des variables
    # X[i,k] : job i placé en position k
    # W[i,i2,k] : i puis i2 dans deux positions consécutives
    # S[k,j] : début de la position k sur la machine j
    # Cmax : makespan
    # -------------------------
    x0 = 0
    nx = n * n

    w0 = x0 + nx
    nw = n * n * max(n - 1, 0)

    s0 = w0 + nw
    ns = n * m

    cmax_idx = s0 + ns
    N = cmax_idx + 1

    def x_idx(i, k):
        return x0 + i * n + k

    def w_idx(i, i2, k):
        # k = 0..n-2
        return w0 + (k * n + i) * n + i2

    def s_idx(k, j):
        return s0 + k * m + j

    # Objective: minimize Cmax
    c = np.zeros(N)
    c[cmax_idx] = 1.0

    # Bounds: X/W binary, S/Cmax non-negative
    lower = np.zeros(N)
    upper = np.full(N, np.inf)
    upper[x0:w0] = 1.0
    if nw:
        upper[w0:s0] = 1.0

    # Integrality: X and W integer/binary; S and Cmax continuous
    integrality = np.zeros(N, dtype=int)
    integrality[x0:w0] = 1
    if nw:
        integrality[w0:s0] = 1

    rows = []
    lbs = []
    ubs = []

    def add_constraint(coeffs, lb=-np.inf, ub=np.inf):
        rows.append(coeffs)
        lbs.append(lb)
        ubs.append(ub)

    # 1) Chaque job apparaît exactement une fois.
    for i in range(n):
        row = {}
        for k in range(n):
            row[x_idx(i, k)] = 1.0
        add_constraint(row, 1.0, 1.0)

    # 2) Chaque position contient exactement un job.
    for k in range(n):
        row = {}
        for i in range(n):
            row[x_idx(i, k)] = 1.0
        add_constraint(row, 1.0, 1.0)

    # 3) W[i,i2,k] >= X[i,k] + X[i2,k+1] - 1
    for i in range(n):
        for i2 in range(n):
            for k in range(n - 1):
                row = {
                    w_idx(i, i2, k): 1.0,
                    x_idx(i, k): -1.0,
                    x_idx(i2, k + 1): -1.0,
                }
                add_constraint(row, -1.0, np.inf)

    # 4) S[0,0] == 0  (S[1][1] du modèle OPL)
    add_constraint({s_idx(0, 0): 1.0}, 0.0, 0.0)

    # 5) Passage d'une position à la suivante sur chaque machine.
    # S[k+1,j] >= S[k,j] + processing(k,j) + setup(k -> k+1,j)
    for k in range(n - 1):
        for j in range(m):
            row = {
                s_idx(k + 1, j): 1.0,
                s_idx(k, j): -1.0,
            }

            for i in range(n):
                row[x_idx(i, k)] = row.get(x_idx(i, k), 0.0) - P[i, j]

            for i in range(n):
                for i2 in range(n):
                    row[w_idx(i, i2, k)] = row.get(w_idx(i, i2, k), 0.0) - Y[i, i2] * ts[i, i2]

            add_constraint(row, 0.0, np.inf)

    # 6) Passage d'une machine à la suivante pour la même position.
    # S[k,j] >= S[k,j-1] + processing(k,j-1)
    for k in range(n):
        for j in range(1, m):
            row = {
                s_idx(k, j): 1.0,
                s_idx(k, j - 1): -1.0,
            }
            for i in range(n):
                row[x_idx(i, k)] = row.get(x_idx(i, k), 0.0) - P[i, j - 1]
            add_constraint(row, 0.0, np.inf)

    # 7) Cmax >= S[k,j] + processing(k,j)
    for k in range(n):
        for j in range(m):
            row = {
                cmax_idx: 1.0,
                s_idx(k, j): -1.0,
            }
            for i in range(n):
                row[x_idx(i, k)] = row.get(x_idx(i, k), 0.0) - P[i, j]
            add_constraint(row, 0.0, np.inf)

    # Sparse constraint matrix
    A = lil_matrix((len(rows), N), dtype=float)
    for r, coeffs in enumerate(rows):
        for col, value in coeffs.items():
            if value:
                A[r, col] = value

    result = milp(
        c=c,
        integrality=integrality,
        bounds=Bounds(lower, upper),
        constraints=LinearConstraint(A.tocsr(), np.asarray(lbs), np.asarray(ubs)),
        options={"disp": False},
    )

    if not result.success:
        raise RuntimeError(f"Le solveur n'a pas trouvé une solution : {result.message}")

    solution = result.x

    sequence = []
    for k in range(n):
        selected = np.argmax([solution[x_idx(i, k)] for i in range(n)])
        sequence.append(int(selected) + 1)  # 1-based pour l'interface

    best_cmax = float(solution[cmax_idx])
    return sequence, best_cmax
