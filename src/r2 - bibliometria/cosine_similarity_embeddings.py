"""
Implementación de similitud textual basada en IA usando embeddings y coseno.

Utiliza Sentence Transformers (modelo all-MiniLM-L6-v2) para representar textos como vectores
y calcula la similitud del coseno entre ellos. Devuelve una matriz NxN con las similitudes.
"""

from typing import List
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np


def embed_texts(texts: List[str], model_name: str = "all-MiniLM-L6-v2") -> np.ndarray:
    """Convierte una lista de textos en embeddings vectoriales."""
    model = SentenceTransformer(model_name)
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return embeddings


def compare_texts(texts: List[str]) -> np.ndarray:
    """Calcula la matriz NxN de similitud de coseno para una lista de textos."""
    embeddings = embed_texts(texts)
    sim_matrix = cosine_similarity(embeddings)
    return sim_matrix


if __name__ == "__main__":
    ejemplos = [
        "El aprendizaje automático es una rama de la inteligencia artificial.",
        "La inteligencia artificial incluye técnicas como el aprendizaje automático.",
        "La biología estudia los organismos vivos y sus procesos vitales."
    ]

    print("📘 Calculando similitud de coseno con embeddings...\n")
    matriz = compare_texts(ejemplos)

    # Mostrar matriz redondeada
    for fila in matriz:
        print([round(x, 3) for x in fila])
