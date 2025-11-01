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


# ---------------- Funciones Radix Sort ----------------
def get_key(entry: dict) -> str:
    """Construir clave año|titulo para ordenar."""
    year = str(entry.get("year", "0000"))
    title = normalize(entry.get("title", ""))
    return f"{year}|{title}"

def counting_sort(entries, index):
    """Ordenamiento estable basado en el carácter en la posición index (Unicode seguro)."""
    n = len(entries)
    output = [None] * n

    # Construir lista de claves de cada entry en ese índice
    keys = []
    for entry in entries:
        key = get_key(entry)
        if index < len(key):
            keys.append(ord(key[index]))
        else:
            keys.append(0)

    # Encontrar el máximo valor de char para definir la lista de conteo
    max_char = max(keys)
    count = [0] * (max_char + 1)

    # Contar ocurrencias
    for char in keys:
        count[char] += 1

    # Posiciones acumuladas
    for i in range(1, len(count)):
        count[i] += count[i - 1]

    # Colocar elementos en la posición correcta
    for i in range(n - 1, -1, -1):
        char = keys[i]
        output[count[char] - 1] = entries[i]
        count[char] -= 1

    return output

def radix_sort(entries):
    """Radix Sort por caracteres de la clave compuesta año|titulo (Unicode seguro)."""
    if not entries:
        return entries

    max_len = max(len(get_key(e)) for e in entries)
    for index in range(max_len - 1, -1, -1):  # derecha → izquierda
        entries = counting_sort(entries, index)

    return entries

# ---------------- Función principal ----------------
def sort_bib_file(input_file, output_file):
    parser = BibTexParser(common_strings=True)
    with open(input_file, encoding="utf-8") as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file, parser=parser)

    start = time.perf_counter()
    sorted_entries = radix_sort(bib_database.entries)
    end = time.perf_counter()
    elapsed = end - start

    db_sorted = bibtexparser.bibdatabase.BibDatabase()
    db_sorted.entries = sorted_entries

    writer = BibTexWriter()
    writer.indent = "    "
    writer.order_entries_by = None
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(writer.write(db_sorted))

    print(f"✅ Archivo ordenado guardado en {output_file}")
    print(f"⏱️ Tiempo de ordenamiento (Radix Sort): {elapsed:.6f} segundos")
    print(f"📚 Total de entradas ordenadas: {len(sorted_entries)}")


# ---------------- Ejecución directa ----------------
if __name__ == "__main__":
    INPUT = "unificado.bib"
    OUTPUT = "./files/unificado_ordenado_radix.bib"
    sort_bib_file(INPUT, OUTPUT)
