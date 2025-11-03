import os
import re
import unicodedata
import json
import csv
from pathlib import Path
import bibtexparser
import networkx as nx
import matplotlib.pyplot as plt
from src.r2_bibliometria.overlap_similarity import overlap_between


# ------------------------------------------------------------
# 🔹 1. Normalización avanzada de texto
# ------------------------------------------------------------
def clean_latex_text(text: str) -> str:
    """Elimina comandos y llaves de LaTeX en los textos .bib."""
    if not text:
        return ""
    text = re.sub(r"[{}]", "", text)              # quitar llaves
    text = re.sub(r"\\[a-zA-Z]+\s*", "", text)    # quitar comandos LaTeX
    return text


def normalize(text: str) -> str:
    """Normaliza texto: quita LaTeX, acentos y pasa a minúsculas."""
    text = clean_latex_text(text)
    text = text.lower()
    text = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
    return text.strip()


# ------------------------------------------------------------
# 🔹 2. Cargar artículos desde el archivo .bib
# ------------------------------------------------------------
# Precompilamos regex para acelerar
_RE_LTX_CMD = re.compile(r"\\[a-zA-Z]+\s*")
_RE_BRACES = re.compile(r"[{}]")
_RE_SPLIT_AUTH = re.compile(r'\s+and\s+|;|,|&')
_RE_SPLIT_KW = re.compile(r',|;|\|')
_RE_YEAR = re.compile(r'\d{4}')

def clean_latex_text(text: str) -> str:
    if not text:
        return ""
    text = _RE_BRACES.sub("", text)
    text = _RE_LTX_CMD.sub("", text)
    return text

def normalize(text: str) -> str:
    if not text:
        return ""
    text = clean_latex_text(text)
    text = text.lower()
    text = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
    return text.strip()

def split_authors(auth_str):
    if not auth_str:
        return []
    parts = _RE_SPLIT_AUTH.split(auth_str)
    return [normalize(p) for p in parts if p.strip()]

def split_keywords(kw):
    if not kw:
        return []
    parts = _RE_SPLIT_KW.split(kw)
    return [normalize(p) for p in parts if p.strip()]

def cargar_articulos(ruta_bib):
    """Carga artículos de un .bib grande de forma eficiente."""
    print(f"Cargando artículos desde {ruta_bib}...")
    with open(ruta_bib, encoding="utf-8") as bibtex_file:
        bib_str = bibtex_file.read()

    parser = bibtexparser.bparser.BibTexParser(common_strings=True)
    parser.ignore_nonstandard_types = True
    parser.homogenize_fields = False
    bib_database = bibtexparser.loads(bib_str, parser=parser)

    articulos = []
    for entry in bib_database.entries:
        if not isinstance(entry, dict):
            continue

        year = None
        year_raw = entry.get("year", "")
        match = _RE_YEAR.search(year_raw)
        if match:
            try:
                year = int(match.group(0))
            except:
                pass

        autores = split_authors(entry.get("author", ""))
        articulos.append({
            "id": entry.get("ID", ""),
            "titulo": entry.get("title", ""),
            "titulo_norm": normalize(entry.get("title", "")),
            "autor_primario": autores[0] if autores else "",
            "autores": autores,
            "keywords": split_keywords(entry.get("keywords", "")),
            "year": year,
        })

    print(f"✅ Se cargaron {len(articulos)} artículos correctamente.")
    return articulos


# ------------------------------------------------------------
# 🔹 3. Construcción del grafo de citaciones (por similitud)
# ------------------------------------------------------------
def construir_grafo_citaciones(articulos, umbral=0.5):
    """
    Construye un grafo dirigido de citaciones inferidas por similitud.
    Optimizado: evita duplicados y reduce comparaciones redundantes.
    """
    G = nx.DiGraph()

    # 🔹 1. Crear un conjunto para evitar nodos duplicados
    ids_vistos = set()
    for art in articulos:
        node_id = art["id"].strip() or art["titulo_norm"]
        if node_id in ids_vistos:
            continue  # evitar duplicados
        ids_vistos.add(node_id)

        G.add_node(node_id,
                   titulo=art["titulo"],
                   autores=art["autores"],
                   keywords=art["keywords"],
                   year=art["year"])

    n = len(articulos)
    print(f"Creando grafo inferido (comparaciones: {n*(n-1)//2})...")

    # 🔹 2. Solo comparamos cada par una vez (i < j)
    for i in range(n):
        a = articulos[i]
        for j in range(i + 1, n):
            b = articulos[j]

            # Filtrado temporal (solo si ambos tienen año)
            if a["year"] and b["year"]:
                if a["year"] < b["year"]:
                    origen, destino = a, b
                else:
                    origen, destino = b, a
            else:
                origen, destino = a, b

            # Calcular similitudes solo una vez por par
            peso_titulo = overlap_between(a["titulo_norm"], b["titulo_norm"])
            peso_autores = overlap_between(a["autor_primario"], b["autor_primario"])
            kw_a = " ".join(a["keywords"])
            kw_b = " ".join(b["keywords"])
            peso_keywords = overlap_between(kw_a, kw_b)

            similitud = round((peso_titulo + peso_autores + peso_keywords) / 3, 2)

            if similitud >= umbral:
                cost = round(1 - similitud, 4)
                G.add_edge(
                    origen["id"].strip() or origen["titulo_norm"],
                    destino["id"].strip() or destino["titulo_norm"],
                    weight=cost,
                    similarity=similitud
                )

    return G

# ------------------------------------------------------------
# 🔹 4. Algoritmos de análisis en el grafo
# ------------------------------------------------------------
def caminos_minimos(G, ruta_json="./src/seguimiento2/r_1/caminos_minimos.json", ruta_csv="./src/seguimiento2/r_1/distancias_promedio.csv"):
    """
    Calcula los caminos mínimos entre todos los pares de nodos
    utilizando únicamente el algoritmo de Dijkstra.
    Además, guarda los resultados en JSON (completos) y CSV (resumen).
    """
    print("Usando método de caminos mínimos: Dijkstra (optimizado)")

    # Cálculo de distancias mínimas entre todos los pares de nodos
    caminos = dict(nx.all_pairs_dijkstra_path_length(G, weight='weight'))
    print("Cálculo de caminos mínimos completado correctamente.")

    # 🔹 Crear carpeta de salida
    Path(ruta_json).parent.mkdir(parents=True, exist_ok=True)

    # 🔹 Guardar todos los caminos en JSON
    caminos_json = {str(k): {str(kk): float(vv) for kk, vv in v.items()} for k, v in caminos.items()}
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(caminos_json, f, indent=2, ensure_ascii=False)
    print(f"Caminos mínimos guardados en: {Path(ruta_json).resolve()}")

    # 🔹 Guardar resumen en CSV (distancia promedio por nodo)
    with open(ruta_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Nodo", "Distancia_Promedio", "Caminos_Validos"])
        for nodo, destinos in caminos.items():
            if destinos:
                promedio = sum(destinos.values()) / len(destinos)
                writer.writerow([nodo, round(promedio, 4), len(destinos)])
    print(f"Resumen de distancias promedio guardado en: {Path(ruta_csv).resolve()}")

    return caminos
# ------------------------------------------------------------
# 🔹 5. Visualización del grafo
# ------------------------------------------------------------
def visualizar_grafo(G, ruta_salida=None):
    """Dibuja y guarda el grafo de citaciones."""
    nodos_aislados = list(nx.isolates(G))
    print(f"Nodos aislados: {len(nodos_aislados)}")
    G_conectado = G.copy()
    G_conectado.remove_nodes_from(nodos_aislados)

    if ruta_salida is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        ruta_salida = os.path.join(base_dir, "grafo_citaciones.png")

    plt.figure(figsize=(12, 10))
    pos = nx.kamada_kawai_layout(G_conectado)

    nx.draw_networkx_nodes(G_conectado, pos, node_color="skyblue", node_size=900)
    nx.draw_networkx_labels(G_conectado, pos, font_size=7)
    nx.draw_networkx_edges(G_conectado, pos, arrows=True, arrowstyle="-|>", width=1.3)

    labels = nx.get_edge_attributes(G_conectado, "similarity")
    nx.draw_networkx_edge_labels(G_conectado, pos, edge_labels=labels, font_size=6)

    plt.title("Red de Citaciones Inferidas (Nodos Conectados)")
    plt.tight_layout()
    plt.savefig(ruta_salida, dpi=300)
    plt.close()
    print(f"Grafo guardado como: {ruta_salida}")

    with open("nodos_aislados.txt", "w", encoding="utf-8") as f:
        for n in nodos_aislados:
            f.write(f"{n}\n")

def guardar_grafo_gexf(G):
    """Guarda el grafo en formato GEXF eliminando atributos inválidos."""
    # 🔹 Crear ruta relativa al archivo actual
    ruta_salida = os.path.join(os.path.dirname(__file__), 'grafo_citaciones.gexf')
    ruta_salida = os.path.abspath(ruta_salida)

    G_limpio = nx.DiGraph()
    
    for n, attrs in G.nodes(data=True):
        G_limpio.add_node(n)
        # Asegurar que todos los valores sean cadenas
        for k, v in attrs.items():
            G_limpio.nodes[n][k] = str(v) if not isinstance(v, (int, float, str)) else v

    for u, v, attrs in G.edges(data=True):
        # Validar peso
        peso = attrs.get("weight", 1.0)
        if isinstance(peso, (int, float)):
            G_limpio.add_edge(u, v, weight=peso)
        else:
            try:
                G_limpio.add_edge(u, v, weight=float(peso))
            except:
                G_limpio.add_edge(u, v, weight=1.0)

    nx.write_gexf(G_limpio, ruta_salida)
    print(f"Grafo exportado correctamente a {ruta_salida}")


def guardar_grafo_graphml(G):
    """Guarda el grafo en formato GraphML, asegurando que todos los atributos sean válidos."""
    # 🔹 Crear ruta relativa al archivo actual
    ruta_salida = os.path.join(os.path.dirname(__file__), 'grafo_citaciones.graphml')
    ruta_salida = os.path.abspath(ruta_salida)

    G_limpio = nx.DiGraph()
    
    for n, attrs in G.nodes(data=True):
        G_limpio.add_node(n)
        for k, v in attrs.items():
            # Convertir listas, tuplas o cualquier otro tipo a cadena
            if isinstance(v, (list, dict, tuple, set)):
                G_limpio.nodes[n][k] = ", ".join(map(str, v))
            else:
                G_limpio.nodes[n][k] = v

    for u, v, attrs in G.edges(data=True):
        G_limpio.add_edge(u, v)
        for k, v2 in attrs.items():
            if isinstance(v2, (list, dict, tuple, set)):
                G_limpio[u][v][k] = ", ".join(map(str, v2))
            else:
                G_limpio[u][v][k] = v2

    nx.write_graphml(G_limpio, ruta_salida)
    print(f"Grafo exportado correctamente a {ruta_salida}")

def componentes_fuertemente_conexas(G):
    """Identifica componentes fuertemente conexas."""
    return list(nx.strongly_connected_components(G))



# ------------------------------------------------------------
# 🔹 6. Ejecución principal
# ------------------------------------------------------------
def main():
    ruta = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'descargas', 'unificado.bib')
    ruta = os.path.abspath(ruta)

    articulos = cargar_articulos(ruta)

    print(f"Se cargaron {len(articulos)} artículos correctamente.")

    G = construir_grafo_citaciones(articulos)
    print(f"Grafo creado con {len(G.nodes)} nodos y {len(G.edges)} aristas.")

    visualizar_grafo(G)

    caminos = caminos_minimos(G)
    print("Caminos mínimos calculados correctamente.")

    componentes = componentes_fuertemente_conexas(G)
    print(f"Componentes fuertemente conexas encontradas: {len(componentes)}")

    # Guardado del grafo
    guardar_grafo_gexf(G)
    guardar_grafo_graphml(G)

    print("Grafo almacenado en formatos GEXF y GraphML.")


if __name__ == "__main__":
    main()
