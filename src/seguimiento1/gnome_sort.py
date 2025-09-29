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


# ---------------- Comparador ----------------
def compare(entry1, entry2):
    year1, year2 = int(entry1.get("year", 0)), int(entry2.get("year", 0))
    if year1 < year2:
        return -1
    elif year1 > year2:
        return 1
    else:
        title1 = normalize(entry1.get("title", ""))
        title2 = normalize(entry2.get("title", ""))
        if title1 < title2:
            return -1
        elif title1 > title2:
            return 1
        else:
            return 0


# ---------------- Gnome Sort ----------------
def gnome_sort(arr):
    n = len(arr)
    index = 0
    while index < n:
        if index == 0 or compare(arr[index], arr[index - 1]) >= 0:
            index += 1
        else:
            arr[index], arr[index - 1] = arr[index - 1], arr[index]
            index -= 1
    return arr


# ---------------- Función principal ----------------
def sort_bib_file(input_file, output_file):
    parser = BibTexParser(common_strings=True)
    with open(input_file, encoding="utf-8") as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file, parser=parser)

    # medir tiempo
    start = time.perf_counter()
    sorted_entries = gnome_sort(bib_database.entries)
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
    print(f"⏱️ Tiempo de ordenamiento (GnomeSort): {elapsed:.6f} segundos")
    print(f"📚 Número de entradas ordenadas: {len(bib_database.entries)}")


# ---------------- Ejecución directa ----------------
if __name__ == "__main__":
    INPUT = "unificado.bib"
    OUTPUT = "./files/unificado_ordenado_gnome.bib"
    sort_bib_file(INPUT, OUTPUT)
