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


# ---------------- Bitonic Sort helpers ----------------
def comp_and_swap(arr, i, j, direction):
    """Compara y hace swap según la dirección"""
    if (direction == 1 and compare(arr[i], arr[j]) > 0) or (direction == 0 and compare(arr[i], arr[j]) < 0):
        arr[i], arr[j] = arr[j], arr[i]


def bitonic_merge(arr, low, cnt, direction):
    """Fusiona una secuencia bitónica en orden dado"""
    if cnt > 1:
        k = cnt // 2
        for i in range(low, low + k):
            comp_and_swap(arr, i, i + k, direction)
        bitonic_merge(arr, low, k, direction)
        bitonic_merge(arr, low + k, k, direction)


def bitonic_sort_recursive(arr, low, cnt, direction):
    """Ordena recursivamente en orden bitónico"""
    if cnt > 1:
        k = cnt // 2
        bitonic_sort_recursive(arr, low, k, 1)  # ascendente
        bitonic_sort_recursive(arr, low + k, k, 0)  # descendente
        bitonic_merge(arr, low, cnt, direction)


def bitonic_sort(arr):
    """Ordena en orden ascendente usando Bitonic Sort"""
    n = len(arr)
    # Para BitonicSort, el tamaño debe ser potencia de 2
    # Si no lo es, se rellena con elementos vacíos que se quitan luego
    pow2 = 1
    while pow2 < n:
        pow2 *= 2

    # Relleno con None para completar potencia de 2
    arr_extended = arr + [None] * (pow2 - n)

    def compare_with_none(a, b):
        if a is None: return 1
        if b is None: return -1
        return compare(a, b)

    # Usamos los mismos métodos pero adaptados para None
    def comp_and_swap_safe(arr, i, j, direction):
        if arr[i] is None or arr[j] is None:
            return
        if (direction == 1 and compare_with_none(arr[i], arr[j]) > 0) or \
           (direction == 0 and compare_with_none(arr[i], arr[j]) < 0):
            arr[i], arr[j] = arr[j], arr[i]

    def bitonic_merge_safe(arr, low, cnt, direction):
        if cnt > 1:
            k = cnt // 2
            for i in range(low, low + k):
                comp_and_swap_safe(arr, i, i + k, direction)
            bitonic_merge_safe(arr, low, k, direction)
            bitonic_merge_safe(arr, low + k, k, direction)

    def bitonic_sort_recursive_safe(arr, low, cnt, direction):
        if cnt > 1:
            k = cnt // 2
            bitonic_sort_recursive_safe(arr, low, k, 1)
            bitonic_sort_recursive_safe(arr, low + k, k, 0)
            bitonic_merge_safe(arr, low, cnt, direction)

    bitonic_sort_recursive_safe(arr_extended, 0, pow2, 1)
    return [x for x in arr_extended if x is not None]


# ---------------- Función principal ----------------
def sort_bib_file(input_file, output_file):
    parser = BibTexParser(common_strings=True)
    with open(input_file, encoding="utf-8") as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file, parser=parser)

    # medir tiempo
    start = time.perf_counter()
    sorted_entries = bitonic_sort(bib_database.entries)
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
    print(f"⏱️ Tiempo de ordenamiento (BitonicSort): {elapsed:.6f} segundos")
    print(f"📚 Total de entradas ordenadas: {len(sorted_entries)}")


# ---------------- Ejecución directa ----------------
if __name__ == "__main__":
    INPUT = "unificado.bib"
    OUTPUT = "./files/unificado_ordenado_bitonic.bib"
    sort_bib_file(INPUT, OUTPUT)
