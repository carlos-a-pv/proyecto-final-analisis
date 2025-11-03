"""Implementación de la similitud de Jaccard para textos.

Proporciona funciones para comparar n textos y obtener una matriz NxN de similitud.
La implementación por defecto usa tokens (palabras) limpiadas, y también permite usar n-grams de caracteres.
"""
from typing import List, Tuple, Iterator, Set
import re


def _tokenize(text: str) -> List[str]:
    # tokenización muy simple: palabras alfanuméricas
    return re.findall(r"\w+", text.lower())


def _ngrams(s: str, n: int) -> Set[str]:
    s = s.lower()
    if len(s) < n:
        return {s} if s else set()
    return {s[i:i+n] for i in range(len(s) - n + 1)}


def jaccard_between(a: str, b: str, use_char_ngrams: bool = False, n: int = 3) -> float:
    """Calcula similitud de Jaccard entre dos strings.

    Args:
        a, b: cadenas a comparar.
        use_char_ngrams: si True usa n-grams de caracteres; si False usa tokens (palabras).
        n: longitud de n-gram para n-grams de caracteres.

    Returns:
        float en [0,1]
    """
    if use_char_ngrams:
        sa = _ngrams(a, n)
        sb = _ngrams(b, n)
    else:
        sa = set(_tokenize(a))
        sb = set(_tokenize(b))

    if not sa and not sb:
        return 1.0
    inter = sa.intersection(sb)
    union = sa.union(sb)
    if not union:
        return 0.0
    return len(inter) / len(union)


def compare_texts(texts: List[str], use_char_ngrams: bool = False, n: int = 3) -> List[List[float]]:
    """Devuelve matriz NxN de similitud Jaccard para una lista de textos."""
    texts = ["" if t is None else str(t) for t in texts]
    m = len(texts)
    if m == 0:
        return []
    result = [[0.0] * m for _ in range(m)]
    for i in range(m):
        for j in range(m):
            if i == j:
                # similitud perfecta si ambos no son vacíos, o 1.0 si ambos vacíos
                result[i][j] = 1.0
            else:
                result[i][j] = jaccard_between(texts[i], texts[j], use_char_ngrams=use_char_ngrams, n=n)
    return result


if __name__ == "__main__":
    ejemplos = [
        "Análisis de datos y minería de texto.",
        "Minería de texto y análisis de datos.",
        "Texto distinto sobre astronomía."
    ]
    matriz = compare_texts(ejemplos)
    for fila in matriz:
        print([round(x, 3) for x in fila])
