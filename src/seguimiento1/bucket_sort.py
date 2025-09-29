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

# ---------------- Insertion Sort (para ordenar dentro de cada bucket) ----------------
def insertion_sort(bucket):
    for i in range(1, len(bucket)):
        key = bucket[i]
        j = i - 1

        while j >= 0:
            year_j = int(bucket[j].get("year", 0))
            year_key = int(key.get("year", 0))

            # comparar por año
            if year_j > year_key:
                bucket[j + 1] = bucket[j]
            elif year_j == year_key:
                # si año es igual, comparar por título
                if normalize(bucket[j].get("title", "")) > normalize(key.get("title", "")):
                    bucket[j + 1] = bucket[j]
                else:
                    break
            else:
                break
            j -= 1
        bucket[j + 1] = key
    return bucket

# ---------------- Bucket Sort ----------------
def bucket_sort(entries, bucket_size=5):
    if not entries:
        return []

    years = [int(e.get("year", 0)) for e in entries]
    min_year, max_year = min(years), max(years)
    bucket_count = (max_year - min_year) // bucket_size + 1

    # Crear buckets
    buckets = [[] for _ in range(bucket_count)]

    # Distribuir entradas en buckets según rango de año
    for entry in entries:
        year = int(entry.get("year", 0))
        index = (year - min_year) // bucket_size
        buckets[index].append(entry)

    # Ordenar cada bucket con insertion sort
    sorted_entries = []
    for bucket in buckets:
        if bucket:
            insertion_sort(bucket)  # ordenar in-place
            sorted_entries.extend(bucket)

    return sorted_entries

# ---------------- Función principal ----------------
def sort_bib_file(input_file, output_file, bucket_size=5):
    parser = BibTexParser(common_strings=True)
    with open(input_file, encoding="utf-8") as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file, parser=parser)

    # medir tiempo
    start = time.perf_counter()
    sorted_entries = bucket_sort(bib_database.entries, bucket_size)
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
    print(f"⏱️ Tiempo de ordenamiento (Bucket Sort): {elapsed:.6f} segundos")

# ---------------- Ejecución directa ----------------
if __name__ == "__main__":
    INPUT = "unificado.bib"
    OUTPUT = "./files/unificado_ordenado_bucket.bib"
    sort_bib_file(INPUT, OUTPUT, bucket_size=5)
