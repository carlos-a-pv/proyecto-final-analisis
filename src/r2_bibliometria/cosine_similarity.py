"""Módulo para calcular similitud textual usando similitud coseno con TF-IDF.

Funciones públicas
- compare_texts(texts: List[str]) -> List[List[float]]: devuelve la matriz de similitud NxN
- pairwise_similarities(texts: List[str]) -> Iterator[Tuple[int,int,float]]: generador de tuplas (i,j,sim)

El módulo está escrito en español en docstrings y maneja análisis para n citas.
"""
from typing import List, Iterator, Tuple
import math

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import linear_kernel
    _SKLEARN_AVAILABLE = True
except Exception:
    TfidfVectorizer = None  # type: ignore
    linear_kernel = None  # type: ignore
    _SKLEARN_AVAILABLE = False
    import re
    from collections import Counter


    def _tokenize_simple(text: str):
        return re.findall(r"\w+", text.lower())

    def _build_tfidf(texts):
        # Simple TF-IDF: compute tf (raw count) and idf = log((N)/(df))
        N = len(texts)
        toks = [_tokenize_simple(t) for t in texts]
        df = {}
        for terms in toks:
            for t in set(terms):
                df[t] = df.get(t, 0) + 1
        vocab = {w: i for i, w in enumerate(sorted(df.keys()))}
        import math

        idf = {w: math.log((N) / (df[w])) if df[w] > 0 else 0.0 for w in df}
        vectors = []
        for terms in toks:
            cnt = Counter(terms)
            vec = [0.0] * len(vocab)
            for w, idx in vocab.items():
                tf = cnt.get(w, 0)
                vec[idx] = tf * idf.get(w, 0.0)
            vectors.append(vec)
        return vectors

    def _cosine_matrix_from_vectors(vectors):
        import math

        n = len(vectors)
        sim = [[0.0] * n for _ in range(n)]
        norms = [math.sqrt(sum(x * x for x in vec)) for vec in vectors]
        for i in range(n):
            for j in range(n):
                if norms[i] == 0 or norms[j] == 0:
                    # if both zero-length, make 1.0, else 0.0
                    sim[i][j] = 1.0 if norms[i] == 0 and norms[j] == 0 else 0.0
                else:
                    dot = sum(a * b for a, b in zip(vectors[i], vectors[j]))
                    sim[i][j] = max(0.0, min(1.0, dot / (norms[i] * norms[j])))
        return sim


def _normalize_texts(texts: List[str]) -> List[str]:
    """Normaliza la lista de textos: convierte None a cadena vacía y asegura strings.

    Args:
        texts: lista de textos (posiblemente None)

    Returns:
        Lista de strings limpias.
    """
    return ["" if t is None else str(t) for t in texts]


def compare_texts(texts: List[str]) -> List[List[float]]:
    """Calcula la matriz de similitud coseno entre n textos usando TF-IDF.

    Args:
        texts: lista de cadenas a comparar. Se aceptan 0 o más elementos.

    Returns:
        Matriz (lista de listas) NxN con valores en [0,1].

    Notas:
        - Si la lista está vacía retorna lista vacía.
        - La diagonal es 1.0 para textos que no estén completamente vacíos; si ambos
          textos son vacíos el valor será 1.0 por convención (vectores nulos tratados igual).
    """
    texts = _normalize_texts(texts)
    n = len(texts)
    if n == 0:
        return []

    # Vectorizar con TF-IDF: usar sklearn si está disponible, sino fallback simple
    if _SKLEARN_AVAILABLE and TfidfVectorizer is not None:
        vectorizer = TfidfVectorizer()
        try:
            tfidf = vectorizer.fit_transform(texts)
        except ValueError:
            # Ocurre si todos los textos son vacíos o no hay vocabulario
            result = [[0.0] * n for _ in range(n)]
            for i in range(n):
                for j in range(n):
                    result[i][j] = 1.0 if texts[i] == "" and texts[j] == "" else 0.0
            return result

        # Usamos linear_kernel para producto punto normalizado (coseno)
        sim_matrix = linear_kernel(tfidf, tfidf)

        # clip y convertir a lista de listas
        for i in range(n):
            for j in range(n):
                val = sim_matrix[i, j]
                if val < 0:
                    val = 0.0
                if val > 1:
                    val = 1.0
                sim_matrix[i, j] = float(val)
        return [list(map(float, sim_matrix[i])) for i in range(n)]
    else:
        vectors = _build_tfidf(texts)
        return _cosine_matrix_from_vectors(vectors)


def pairwise_similarities(texts: List[str]) -> Iterator[Tuple[int, int, float]]:
    """Generador que produce tuplas (i, j, similitud) para i < j.

    Útil para procesar grandes conjuntos sin construir una matriz completa en memoria.
    """
    texts = _normalize_texts(texts)
    n = len(texts)
    if n <= 1:
        return

    vectorizer = TfidfVectorizer()
    try:
        tfidf = vectorizer.fit_transform(texts)
    except ValueError:
        # Todos vacíos o sin vocabulario: yield 1.0 para pares vacíos, 0.0 en otro caso
        for i in range(n):
            for j in range(i + 1, n):
                yield (i, j, 1.0 if texts[i] == "" and texts[j] == "" else 0.0)
        return

    sim_matrix = linear_kernel(tfidf, tfidf)
    for i in range(n):
        for j in range(i + 1, n):
            val = float(sim_matrix[i, j])
            if val < 0:
                val = 0.0
            if val > 1:
                val = 1.0
            yield (i, j, val)


if __name__ == "__main__":
    # Pequeño ejemplo de uso
    ejemplos = [
        "Análisis de datos y minería de texto.",
        "Minería de texto y análisis de datos.",
        "Un texto totalmente distinto sobre astronomía."
    ]
    matriz = compare_texts(ejemplos)
    for fila in matriz:
        print([round(x, 3) for x in fila])
