import time
import matplotlib.pyplot as plt
import bibtexparser
from bibtexparser.bparser import BibTexParser

# Importa tus algoritmos (suponiendo que cada uno está en su archivo .py)
from tim_sort import timsort
from comb_sort import comb_sort
from selection_sort import selection_sort
from tree_sort import tree_sort
from pigeonhole_sort import pigeonhole_sort
from bucket_sort import bucket_sort
from quick_sort import quick_sort
from heap_sort import heap_sort
from bitonic_sort import bitonic_sort
from gnome_sort import gnome_sort
from binary_insertion_sort import binary_insertion_sort
from radix_sort import radix_sort  # el counting sort
# Si quieres, también podrías probar radix_sort_buckets

# ---------- Utilidad ----------
def get_entries(file_path):
    parser = BibTexParser(common_strings=True)
    with open(file_path, encoding="utf-8") as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file, parser=parser)
    return bib_database.entries

def benchmark(entries):
    algorithms = {
        "TimSort": timsort,
        "CombSort": comb_sort,
        "SelectionSort": selection_sort,
        "TreeSort": tree_sort,
        "PigeonholeSort": pigeonhole_sort,
        "BucketSort": bucket_sort,
        "QuickSort": quick_sort,
        "HeapSort": heap_sort,
        "BitonicSort": bitonic_sort,
        "GnomeSort": gnome_sort,
        "BinaryInsertionSort": binary_insertion_sort,
        "RadixSort": radix_sort,
    }

    results = {}

    for name, algo in algorithms.items():
        data = entries.copy()
        start = time.perf_counter()
        algo(data)  # cada algoritmo devuelve lista ordenada
        end = time.perf_counter()
        elapsed = end - start
        results[name] = elapsed
        print(f"{name}: {elapsed:.6f} segundos")

    return results

def plot_results(results):
    # Ordenar resultados por tiempo ascendente
    sorted_items = sorted(results.items(), key=lambda x: x[1])
    names = [x[0] for x in sorted_items]
    times = [x[1] for x in sorted_items]

    plt.figure(figsize=(12, 6))
    plt.bar(names, times, color="skyblue")
    plt.xlabel("Algoritmo de ordenamiento")
    plt.ylabel("Tiempo (segundos)")
    plt.title("Comparación de tiempos de ordenamiento (ascendente)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig("./files/benchmark.png")
    plt.show()
    plt.close()  

# ---------- Main ----------
if __name__ == "__main__":
    INPUT = "unificado.bib"
    entries = get_entries(INPUT)
    results = benchmark(entries)
    plot_results(results)
