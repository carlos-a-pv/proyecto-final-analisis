import time
import re
import unicodedata
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter

# ---------------- Normalización de texto ----------------
def clean_latex_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"[{}]", "", text)              # quitar llaves
    text = re.sub(r"\\[a-zA-Z]+\s*", "", text)    # quitar comandos LaTeX
    return text

def normalize(text: str) -> str:
    text = clean_latex_text(text)
    text = text.lower()
    text = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
    return text.strip()

# ---------------- Comparación entre entradas ----------------
def compare(entry1, entry2) -> bool:
    """True si entry1 debe ir antes que entry2"""
    year1 = int(entry1.get("year", 0))
    year2 = int(entry2.get("year", 0))

    if year1 != year2:
        return year1 < year2

    title1 = normalize(entry1.get("title", ""))
    title2 = normalize(entry2.get("title", ""))
    return title1 <= title2

# ---------------- Definición del BST ----------------
class Node:
    def __init__(self, entry):
        self.entry = entry
        self.left = None
        self.right = None

def insert(root, entry):
    if root is None:
        return Node(entry)
    if compare(entry, root.entry):
        root.left = insert(root.left, entry)
    else:
        root.right = insert(root.right, entry)
    return root

def inorder_traversal(root, result):
    if root is not None:
        inorder_traversal(root.left, result)
        result.append(root.entry)
        inorder_traversal(root.right, result)

# ---------------- Algoritmo Tree Sort ----------------
def tree_sort(entries):
    root = None
    for entry in entries:
        root = insert(root, entry)

    result = []
    inorder_traversal(root, result)
    return result

# ---------------- Función principal ----------------
def sort_bib_file(input_file, output_file):
    parser = BibTexParser(common_strings=True)
    with open(input_file, encoding="utf-8") as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file, parser=parser)

    # medir tiempo
    start = time.perf_counter()
    sorted_entries = tree_sort(bib_database.entries)
    end = time.perf_counter()
    elapsed = end - start

    # guardar archivo
    db_sorted = bibtexparser.bibdatabase.BibDatabase()
    db_sorted.entries = sorted_entries

    writer = BibTexWriter()
    writer.indent = "    "
    writer.order_entries_by = None
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(writer.write(db_sorted))

    print(f"✅ Archivo ordenado guardado en {output_file}")
    print(f"⏱️ Tiempo de ordenamiento (Tree Sort): {elapsed:.6f} segundos")
    print(f"📚 Entradas ordenadas: {len(sorted_entries)}")

# ---------------- Ejecución directa ----------------
if __name__ == "__main__":
    INPUT = "unificado.bib"
    OUTPUT = "./files/unificado_ordenado_treesort.bib"
    sort_bib_file(INPUT, OUTPUT)
