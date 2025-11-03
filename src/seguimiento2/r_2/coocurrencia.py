from src.r3_frecuencia.analyze_frequency import (
    read_bib_abstracts,
    normalize_text,
    count_seed_occurrences,
    discover_candidates,
    compute_candidate_stats
)

import os
import re
import networkx as nx
import matplotlib.pyplot as plt
from itertools import combinations

class GrafoCoocurrenciaTerminos:
    def __init__(self, ruta_bib, semillas, max_candidatos=15):
        self.ruta_bib = ruta_bib
        self.semillas = semillas
        self.max_candidatos = max_candidatos
        self.docs = []
        self.terminos = []
        self.grafo = nx.Graph()

    def cargar_documentos(self):
        self.docs = read_bib_abstracts(self.ruta_bib)
        print(f"🔹 Se cargaron {len(self.docs)} abstracts.")

    def obtener_terminos_frecuentes(self):
        seed_counts, doc_has_seed = count_seed_occurrences(self.docs, self.semillas)
        candidatos = discover_candidates(self.docs, self.semillas, max_new=self.max_candidatos)
        stats = compute_candidate_stats(self.docs, candidatos, doc_has_seed)
        candidatos_filtrados = [row["candidate"] for row in stats]
        self.terminos = list(set(self.semillas + candidatos_filtrados))
        print(f"🔹 Términos utilizados en el grafo: {len(self.terminos)} (semillas + candidatos)")

    def construir_grafo(self):
        for doc in self.docs:
            texto = normalize_text(doc)
            presentes = [t for t in self.terminos if re.search(rf"\b{re.escape(t)}\b", texto)]
            for t1, t2 in combinations(presentes, 2):
                if self.grafo.has_edge(t1, t2):
                    self.grafo[t1][t2]["weight"] += 1
                else:
                    self.grafo.add_edge(t1, t2, weight=1)
        print(f"🔹 Grafo construido con {len(self.grafo.nodes)} nodos y {len(self.grafo.edges)} aristas.")

    def calcular_grados(self):
        grados = dict(self.grafo.degree())
        print("🔹 Grado de cada término:")
        for t, g in sorted(grados.items(), key=lambda x: -x[1]):
            print(f"  {t}: {g}")
        return grados

    def detectar_componentes_conexas(self):
        componentes = list(nx.connected_components(self.grafo))
        print(f"🔹 Se detectaron {len(componentes)} grupos de términos conectados.")
        return componentes

    def visualizar_grafo(self, ruta_salida=None):
        if ruta_salida is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            ruta_salida = os.path.join(base_dir, "grafo_coocurrencia.png")

        plt.figure(figsize=(12, 10))
        pos = nx.spring_layout(self.grafo, seed=42, k=1.2)
        nx.draw_networkx_nodes(self.grafo, pos, node_color="lightblue", node_size=1200)
        nx.draw_networkx_labels(self.grafo, pos, font_size=8)
        nx.draw_networkx_edges(self.grafo, pos, width=1.2)
        labels = nx.get_edge_attributes(self.grafo, "weight")
        nx.draw_networkx_edge_labels(self.grafo, pos, edge_labels=labels, font_size=6)
        plt.title("🔹 Grafo de Coocurrencia de Términos (R2)")
        plt.tight_layout()
        plt.savefig(ruta_salida, dpi=300)
        plt.close()
        print(f"🔹 Grafo guardado como: {ruta_salida}")

if __name__ == "__main__":
    # 🔹 Ruta al archivo .bib
    ruta_bib = os.path.join(os.path.dirname(__file__), '..','..', '..', 'descargas', 'unificado.bib')
    ruta_bib= os.path.abspath(ruta_bib)

    # 🔹 Ruta al archivo .txt con semillas (una por línea)
    ruta_semillas = os.path.join(os.path.dirname(__file__),'..', '..', 'r3_frecuencia', 'seeds','ai_concepts.txt')
    ruta_semillas = os.path.abspath(ruta_semillas)

    # 🔹 Leer semillas desde archivo
    with open(ruta_semillas, encoding="utf-8") as f:
        semillas = [line.strip() for line in f if line.strip()]

    # 🔹 Ruta de salida para la imagen del grafo
    ruta_salida = os.path.join(os.path.dirname(__file__),'..', '..', 'seguimiento2', 'r_2','grafo_coocurrencia.png') 
    ruta_salida = os.path.abspath(ruta_salida)

    # 🔹 Número máximo de candidatos
    max_candidatos = 15

    # 🔹 Ejecución directa
    grafo = GrafoCoocurrenciaTerminos(ruta_bib, semillas, max_candidatos)
    grafo.cargar_documentos()
    grafo.obtener_terminos_frecuentes()
    grafo.construir_grafo()
    grafo.calcular_grados()
    grafo.detectar_componentes_conexas()
    grafo.visualizar_grafo(ruta_salida)
    