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
    # eliminar llaves y comandos LaTeX
    text = re.sub(r"[{}]", "", text)
    text = re.sub(r"\\[a-zA-Z]+\s*", "", text)
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
    """
    Retorna True si entry1 debe ir antes que entry2.
    """
    year1 = int(entry1.get("year", 0))
    year2 = int(entry2.get("year", 0))

    if year1 != year2:
        return year1 < year2

    title1 = normalize(entry1.get("title", ""))
    title2 = normalize(entry2.get("title", ""))
    return title1 <= title2

# ---------------- Algoritmo Comb Sort ----------------
def comb_sort(entries):
    n = len(entries)
    gap = n
    shrink = 1.3
    sorted_flag = False

    while not sorted_flag:
        # reducir el gap
        gap = int(gap / shrink)
        if gap <= 1:
            gap = 1
            sorted_flag = True

        i = 0
        while i + gap < n:
            if not compare(entries[i], entries[i + gap]):
                entries[i], entries[i + gap] = entries[i + gap], entries[i]
                sorted_flag = False
            i += 1

    return entries

# ---------------- Función principal ----------------
def sort_bib_file(input_file, output_file):
    parser = BibTexParser(common_strings=True)
    with open(input_file, encoding="utf-8") as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file, parser=parser)

    # medir tiempo
    start = time.perf_counter()
    sorted_entries = comb_sort(bib_database.entries)
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
    print(f"⏱️ Tiempo de ordenamiento (Comb Sort): {elapsed:.6f} segundos")

# ---------------- Ejecución directa ----------------
if __name__ == "__main__":
    INPUT = "unificado.bib"
    OUTPUT = "./files/unificado_ordenado_combsort.bib"
    sort_bib_file(INPUT, OUTPUT)

    
