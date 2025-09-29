import os
import bibtexparser
from bibtexparser.bparser import BibTexParser
from collections import Counter
import matplotlib.pyplot as plt

def normalize_author(name):
    """Convertir a minúsculas y quitar espacios extra para uniformizar nombres."""
    return " ".join(name.lower().strip().split())

def top_authors(input_file, top_n=15, save_path=None):
    # Leer archivo .bib
    parser = BibTexParser(common_strings=True)
    with open(input_file, encoding="utf-8") as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file, parser=parser)

    # Contar autores normalizados
    author_counter = Counter()
    for entry in bib_database.entries:
        if "author" in entry:
            authors = [normalize_author(a) for a in entry["author"].split(" and ")]
            author_counter.update(authors)

    # Ordenar descendente por número de apariciones
    sorted_authors = sorted(author_counter.items(), key=lambda x: (-x[1], x[0]))

    # Seleccionar los top N
    top_authors_list = sorted_authors[:top_n]

    # Mostrar resultado
    print(f"📊 Los {top_n} autores con más apariciones:")
    for author, count in top_authors_list:
        print(f"{author}: {count}")

    # ----------------- Gráfica -----------------
    if save_path:
        authors = [a for a, c in top_authors_list]
        counts = [c for a, c in top_authors_list]

        plt.figure(figsize=(12, 6))
        plt.bar(authors, counts, color="lightgreen")
        plt.xlabel("Autores")
        plt.ylabel("Número de apariciones")
        plt.title(f"Top {top_n} autores con más apariciones")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        # Crear carpeta si no existe
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path)
        plt.close()
        print(f" Gráfica guardada en {save_path}")

    return top_authors_list

# ---------- Main ----------
if __name__ == "__main__":
    INPUT = "unificado.bib"
    SAVE_PATH = r"./files/top_authors.png"
    top_authors(INPUT, save_path=SAVE_PATH)
