"""
Implementación de la similitud de Sørensen–Dice para textos.

Proporciona funciones para comparar n textos y obtener una matriz NxN de similitud.
La implementación por defecto usa tokens (palabras) limpiadas, y también permite usar n-grams de caracteres.
"""

from typing import List, Set
import re


# =====================================================
# FUNCIONES AUXILIARES
# =====================================================

def _tokenize(text: str) -> List[str]:
    """Tokenización básica en palabras alfanuméricas."""
    return re.findall(r"\w+", text.lower())


def _ngrams(s: str, n: int) -> Set[str]:
    """Genera n-grams de caracteres."""
    s = s.lower()
    if len(s) < n:
        return {s} if s else set()
    return {s[i:i+n] for i in range(len(s) - n + 1)}


# =====================================================
# ALGORITMO DE SIMILITUD SØRENSEN–DICE
# =====================================================

def dice_between(a: str, b: str, use_char_ngrams: bool = False, n: int = 2) -> float:
    """Calcula la similitud de Sørensen–Dice entre dos cadenas de texto.

    Args:
        a, b: cadenas a comparar.
        use_char_ngrams: si True usa n-grams de caracteres; si False usa tokens (palabras).
        n: tamaño de n-gram para comparación basada en caracteres.

    Returns:
        float en [0,1] indicando la similitud.
    """
    if not a and not b:
        return 1.0

    if use_char_ngrams:
        sa = _ngrams(a, n)
        sb = _ngrams(b, n)
    else:
        sa = set(_tokenize(a))
        sb = set(_tokenize(b))

    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0

    overlap = len(sa.intersection(sb))
    return (2 * overlap) / (len(sa) + len(sb))


# =====================================================
# MATRIZ NxN DE SIMILITUD
# =====================================================

def compare_texts(texts: List[str], use_char_ngrams: bool = False, n: int = 2) -> List[List[float]]:
    """Devuelve matriz NxN de similitud Sørensen–Dice para una lista de textos."""
    texts = ["" if t is None else str(t) for t in texts]
    m = len(texts)
    if m == 0:
        return []
    result = [[0.0] * m for _ in range(m)]
    for i in range(m):
        for j in range(m):
            if i == j:
                result[i][j] = 1.0
            else:
                result[i][j] = dice_between(texts[i], texts[j], use_char_ngrams=use_char_ngrams, n=n)
    return result


# =====================================================
#  EJEMPLO DE USO
# =====================================================

if __name__ == "__main__":
    ejemplos = [
        "Análisis de datos y minería de texto.",
        "Minería de texto y análisis de datos.",
        "Texto distinto sobre astronomía."
    ]

    matriz = compare_texts(ejemplos)

    print("Matriz de similitud Sørensen–Dice:")
    for fila in matriz:
        print([round(x, 3) for x in fila])


