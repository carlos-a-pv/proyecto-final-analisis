"""Implementación del coeficiente de Overlap (Szymkiewicz–Simpson).

Proporciona funciones para comparar n textos y obtener una matriz NxN.
Soporta tokens y n-grams de caracteres.
"""
from typing import List, Set
import re


def _tokenize(text: str) -> List[str]:
    return re.findall(r"\w+", (text or "").lower())


def _ngrams(s: str, n: int) -> Set[str]:
    s = (s or "").lower()
    if len(s) < n:
        return {s} if s else set()
    return {s[i:i+n] for i in range(len(s) - n + 1)}


def overlap_between(a: str, b: str, use_char_ngrams: bool = False, n: int = 3) -> float:
    """Devuelve el coeficiente de Overlap entre dos strings en [0,1].

    Overlap = |A ∩ B| / min(|A|, |B|)
    """
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
    inter = sa.intersection(sb)
    denom = min(len(sa), len(sb))
    if denom == 0:
        return 0.0
    return len(inter) / denom


def compare_texts(texts: List[str], use_char_ngrams: bool = False, n: int = 3):
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
                result[i][j] = float(overlap_between(texts[i], texts[j], use_char_ngrams=use_char_ngrams, n=n))
    return result


if __name__ == '__main__':
    ejemplos = ["análisis de datos", "minería de texto y análisis de datos", "astronomía"]
    m = compare_texts(ejemplos)
    for fila in m:
        print([round(x, 3) for x in fila])
