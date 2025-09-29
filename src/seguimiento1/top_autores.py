import bibtexparser
from bibtexparser.bparser import BibTexParser
from collections import Counter

def top_authors(input_file, top_n=15):
    # Leer archivo .bib
    parser = BibTexParser(common_strings=True)
    with open(input_file, encoding="utf-8") as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file, parser=parser)

    # Contar autores
    author_counter = Counter()
    for entry in bib_database.entries:
        if "author" in entry:
            authors = [a.strip() for a in entry["author"].split(" and ")]
            author_counter.update(authors)

    # Ordenar ascendente por número de apariciones
    sorted_authors = sorted(author_counter.items(), key=lambda x: (x[1], x[0]))

    # Seleccionar los 15 primeros
    top_authors_list = sorted_authors[:top_n]

    # Mostrar resultado
    print("📊 Los 15 primeros autores con más apariciones (ascendente):")
    for author, count in top_authors_list:
        print(f"{author}: {count}")

    return top_authors_list

# ---------- Main ----------
if __name__ == "__main__":
    INPUT = "unificado.bib"
    top_authors(INPUT)
