"""Implementación de la similitud Jaro y Jaro-Winkler.

Funciones públicas:
- jaro_similarity(s1: str, s2: str) -> float
- jaro_winkler(s1: str, s2: str, prefix_scaling: float = 0.1) -> float
- compare_texts(texts: List[str], method: str = 'jaro_winkler') -> List[List[float]]

Esta implementación es en puro Python y no requiere dependencias externas.
"""
from typing import List


def _matching_window(s1: str, s2: str) -> int:
    return max((max(len(s1), len(s2)) // 2) - 1, 0)


def jaro_similarity(s1: str, s2: str) -> float:
    """Calcula la similitud Jaro entre dos strings en [0,1]."""
    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    match_dist = _matching_window(s1, s2)

    s1_matches = [False] * len(s1)
    s2_matches = [False] * len(s2)

    matches = 0
    transpositions = 0

    # Encontrar matches
    for i, ch in enumerate(s1):
        start = max(0, i - match_dist)
        end = min(i + match_dist + 1, len(s2))
        for j in range(start, end):
            if not s2_matches[j] and ch == s2[j]:
                s1_matches[i] = True
                s2_matches[j] = True
                matches += 1
                break

    if matches == 0:
        return 0.0

    # Contar transpositions
    k = 0
    for i in range(len(s1)):
        if s1_matches[i]:
            while not s2_matches[k]:
                k += 1
            if s1[i] != s2[k]:
                transpositions += 1
            k += 1

    transpositions /= 2

    return (
        (matches / len(s1) + matches / len(s2) + (matches - transpositions) / matches) / 3.0
    )


def jaro_winkler(s1: str, s2: str, prefix_scaling: float = 0.1) -> float:
    """Calcula la similitud Jaro-Winkler entre dos strings.

    prefix_scaling: factor de escala para el prefijo común (por defecto 0.1)
    """
    jaro_sim = jaro_similarity(s1, s2)
    if jaro_sim == 0.0:
        return 0.0

    # Longitud del prefijo común (hasta 4 caracteres según la definición original)
    prefix_len = 0
    max_prefix = 4
    for a, b in zip(s1, s2):
        if a == b and prefix_len < max_prefix:
            prefix_len += 1
        else:
            break

    return jaro_sim + prefix_len * prefix_scaling * (1 - jaro_sim)


def compare_texts(texts: List[str], method: str = "jaro_winkler") -> List[List[float]]:
    """Compara una lista de textos y devuelve la matriz NxN usando Jaro-Winkler o Jaro.

    Args:
        texts: lista de strings
        method: 'jaro_winkler' o 'jaro'
    """
    func = jaro_winkler if method == "jaro_winkler" else jaro_similarity
    n = len(texts)
    result: List[List[float]] = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                result[i][j] = 1.0
            else:
                result[i][j] = float(func(texts[i], texts[j]))
    return result


if __name__ == "__main__":
    ejemplos = ["MARTHA", "MARHTA", "DWAYNE", "DUANE"]
    m = compare_texts(ejemplos)
    for fila in m:
        print([round(x, 4) for x in fila])
