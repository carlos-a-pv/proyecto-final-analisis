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

# ---------------- Pigeonhole Sort ----------------
def pigeonhole_sort(entries):
    if not entries:
        return []

    years = [int(e.get("year", 0)) for e in entries]
    min_year, max_year = min(years), max(years)
    size = max_year - min_year + 1

    # Crear "pigeonholes" (buckets por año)
    holes = [[] for _ in range(size)]

    # Distribuir entradas en sus buckets correspondientes
    for entry in entries:
        year = int(entry.get("year", 0))
        holes[year - min_year].append(entry)

    # Recoger resultados ordenados
    sorted_entries = []
    for bucket in holes:
        if bucket:
            # Ordenar dentro del bucket por título
            bucket.sort(key=lambda e: normalize(e.get("title", "")))
            sorted_entries.extend(bucket)

    return sorted_entries

# ---------------- Función principal ----------------
def sort_bib_file(input_file, output_file):
    parser = BibTexParser(common_strings=True)
    with open(input_file, encoding="utf-8") as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file, parser=parser)

    # medir tiempo
    start = time.perf_counter()
    sorted_entries = pigeonhole_sort(bib_database.entries)
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
    print(f"⏱️ Tiempo de ordenamiento (Pigeonhole Sort): {elapsed:.6f} segundos")
    print(f"📚 Total entradas ordenadas: {len(sorted_entries)}")

# ---------------- Ejecución directa ----------------
if __name__ == "__main__":
    INPUT = "unificado.bib"
    OUTPUT = "./files/unificado_ordenado_pigeonhole.bib"
    sort_bib_file(INPUT, OUTPUT)
