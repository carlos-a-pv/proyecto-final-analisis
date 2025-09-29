# tim_sort.py
import re
import unicodedata
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
import time

MIN_MERGE = 32


def calcMinRun(n):
    """Returns the minimum length of a
    run from 23 - 64 so that
    the len(array)/minrun is less than or
    equal to a power of 2.

    e.g. 1=>1, ..., 63=>63, 64=>32, 65=>33,
    ..., 127=>64, 128=>32, ...
    """
    r = 0
    while n >= MIN_MERGE:
        r |= n & 1
        n >>= 1
    return n + r


# ---------- Normalización ----------
def clean_latex_text(s: str) -> str:
    if not s:
        return ""
    s = str(s)
    s = s.replace("{", "").replace("}", "")
    s = re.sub(r'\\[a-zA-Z]+(?:\*?)\s*\{([^}]*)\}', r'\1', s)
    s = re.sub(r'\\[\'`\^\"~=.]{1}([A-Za-z])', r'\1', s)
    s = re.sub(r'\\+', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def remove_diacritics(s: str) -> str:
    nkfd = unicodedata.normalize('NFKD', s)
    return ''.join(ch for ch in nkfd if not unicodedata.combining(ch))

def normalize_title_for_sort(entry) -> str:
    raw = entry.get("title", "") or ""
    cleaned = clean_latex_text(raw)
    cleaned = remove_diacritics(cleaned)
    cleaned = cleaned.strip().lower()
    cleaned = re.sub(r'^[^0-9a-z]+', '', cleaned)
    return cleaned

def normalize_year_for_sort(entry) -> int:
    raw = entry.get("year", "") or ""
    m = re.search(r'(\d{4})', str(raw))
    return int(m.group(1)) if m else 9999

# ---------- Algoritmo TIMSORT ----------
def timsort(entries):
    """
    Ordena entries .bib por (year asc, title asc), usando algoritmo Timsort.
    """
    # Precalcular claves
    wrapped = [
        (entry, normalize_year_for_sort(entry), normalize_title_for_sort(entry), idx)
        for idx, entry in enumerate(entries)
    ]

    MIN_RUN = 32

    def insertion_sort(sublist, left, right):
        for i in range(left + 1, right + 1):
            key = sublist[i]
            j = i - 1
            while j >= left and (key[1], key[2], key[3]) < (sublist[j][1], sublist[j][2], sublist[j][3]):
                sublist[j + 1] = sublist[j]
                j -= 1
            sublist[j + 1] = key

    def merge(sublist, l, m, r):
        left = sublist[l:m + 1]
        right = sublist[m + 1:r + 1]
        i = j = 0
        k = l
        while i < len(left) and j < len(right):
            if (left[i][1], left[i][2], left[i][3]) <= (right[j][1], right[j][2], right[j][3]):
                sublist[k] = left[i]
                i += 1
            else:
                sublist[k] = right[j]
                j += 1
            k += 1
        while i < len(left):
            sublist[k] = left[i]
            i += 1
            k += 1
        while j < len(right):
            sublist[k] = right[j]
            j += 1
            k += 1

    n = len(wrapped)

    # 1. Divide en runs y aplica insertion sort
    for start in range(0, n, MIN_RUN):
        end = min(start + MIN_RUN - 1, n - 1)
        insertion_sort(wrapped, start, end)

    # 2. Merge runs
    size = MIN_RUN
    while size < n:
        for left in range(0, n, 2 * size):
            mid = min(n - 1, left + size - 1)
            right = min((left + 2 * size - 1), n - 1)
            if mid < right:
                merge(wrapped, left, mid, right)
        size *= 2

    return [w[0] for w in wrapped]

# ---------- Función principal ----------
def sort_bib_file(input_file, output_file):
    # Leer archivo .bib
    parser = BibTexParser(common_strings=True)
    with open(input_file, encoding="utf-8") as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file, parser=parser)

    # Ordenar entradas con timsort

    start = time.perf_counter()
    sorted_entries = timsort(bib_database.entries)
    end = time.perf_counter()
    elapsed = end - start

    # Guardar en nuevo archivo .bib
    db_sorted = bibtexparser.bibdatabase.BibDatabase()
    db_sorted.entries = sorted_entries

    writer = BibTexWriter()
    writer.indent = "    "  # formato más legible
    writer.order_entries_by = None  # respetar nuestro orden
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(writer.write(db_sorted))

        print(f"✅ Archivo ordenado guardado en {output_file}")
        print(f"⏱️ Tiempo de ordenamiento: {elapsed:.6f} segundos")

# ---------- Ejecución ----------
if __name__ == "__main__":
    INPUT = "unificado.bib"
    OUTPUT = "./files/unificado_ordenado_timsort.bib"
    sort_bib_file(INPUT, OUTPUT)
