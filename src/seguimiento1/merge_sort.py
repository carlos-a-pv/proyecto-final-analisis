import bibtexparser

def merge_sort(entries):
    if len(entries) <= 1:
        return entries

    mid = len(entries) // 2
    left = merge_sort(entries[:mid])
    right = merge_sort(entries[mid:])

    return merge(left, right)


def merge(left, right):
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        year_left = int(left[i].get("year", 0))
        year_right = int(right[j].get("year", 0))

        if year_left < year_right:
            result.append(left[i])
            i += 1
        elif year_left > year_right:
            result.append(right[j])
            j += 1
        else:
            title_left = left[i].get("title", "").lower()
            title_right = right[j].get("title", "").lower()
            if title_left <= title_right:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1

    result.extend(left[i:])
    result.extend(right[j:])
    return result


def sort_bib_file(input_file, output_file):
    # Leer archivo .bib
    with open(input_file, encoding="utf-8") as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)

    # Ordenar entradas
    sorted_entries = merge_sort(bib_database.entries)

    # Guardar en nuevo archivo .bib
    db_sorted = bibtexparser.bibdatabase.BibDatabase()
    db_sorted.entries = sorted_entries

    writer = bibtexparser.bwriter.BibTexWriter()
    writer.indent = "    "  # formato más legible
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(writer.write(db_sorted))

    print(f"✅ Archivo ordenado guardado en {output_file}")


# -------------------------
# 📌 Ejemplo de uso
if __name__ == "__main__":
    sort_bib_file("unificado.bib", "unificado_ordenado.bib")
