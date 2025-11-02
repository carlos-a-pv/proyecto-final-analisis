import re
import bibtexparser
import numpy as np
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import linkage, dendrogram, cophenet

# ------------------------------------------------------------
# 1️⃣ Cargar los abstracts o títulos desde el archivo .bib
# ------------------------------------------------------------
def cargar_abstracts(ruta_bib):
    with open(ruta_bib, encoding="utf-8") as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)

    textos = []
    for entry in bib_database.entries:
        if "abstract" in entry:
            textos.append(entry["abstract"])
        elif "title" in entry:
            textos.append(entry["title"])
    return textos

# ------------------------------------------------------------
# 2️⃣ Limpieza de texto y vectorización TF-IDF
# ------------------------------------------------------------
def limpiar_texto(texto):
    texto = texto.lower()
    texto = re.sub(r'[^a-záéíóúüñ\s]', '', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def vectorizar_textos(lista_textos):
    textos_limpios = [limpiar_texto(t) for t in lista_textos]
    vectorizer = TfidfVectorizer(stop_words='english')
    matriz_tfidf = vectorizer.fit_transform(textos_limpios)
    return matriz_tfidf, vectorizer

# ------------------------------------------------------------
# 3️⃣ Generación de clusters jerárquicos
# ------------------------------------------------------------
def generar_clusters(lista_textos, metodo="ward"):
    matriz_tfidf, _ = vectorizar_textos(lista_textos)
    distancias = pdist(matriz_tfidf.toarray(), metric='euclidean')
    linkage_matrix = linkage(distancias, method=metodo)
    return linkage_matrix, matriz_tfidf

# ------------------------------------------------------------
# 4️⃣ Evaluación del agrupamiento
# ------------------------------------------------------------
def evaluar_clusters(linkage_matrix, matriz_tfidf):
    distancias = pdist(matriz_tfidf.toarray())
    coef_cophenetico, _ = cophenet(linkage_matrix, distancias)
    return coef_cophenetico

# ------------------------------------------------------------
# 5️⃣ Visualización del dendrograma
# ------------------------------------------------------------
def mostrar_dendrograma(linkage_matrix, etiquetas):
    plt.figure(figsize=(10, 5))
    dendrogram(linkage_matrix, labels=etiquetas, leaf_rotation=90)
    plt.title("Dendrograma de Agrupamiento Jerárquico")
    plt.xlabel("Documentos")
    plt.ylabel("Distancia")
    plt.tight_layout()
    ruta_salida = "./dendrograma.png"
    plt.savefig(ruta_salida, dpi=300)
    print(f"🖼️ Dendrograma guardado en: {ruta_salida}") 
    plt.close()

# ------------------------------------------------------------
# 6️⃣ Ejecución principal
# ------------------------------------------------------------
def main():
    ruta = "../../descargas/unificado.bib"
    #textos = cargar_abstracts(ruta)
    textos = cargar_abstracts(ruta)[:100]  


    if not textos:
        print("⚠️ No se encontraron abstracts ni títulos en el archivo.")
        return

    print(f"📚 Procesando {len(textos)} documentos...")

    # Métodos jerárquicos a comparar
    metodos = ["ward", "average", "complete"]
    resultados = {}

    for metodo in metodos:
        print(f"\n🔹 Ejecutando clustering con método: {metodo.upper()}")

        linkage_matrix, matriz_tfidf = generar_clusters(textos, metodo)
        coef = evaluar_clusters(linkage_matrix, matriz_tfidf)
        resultados[metodo] = coef

        print(f"   ✅ Coeficiente cophenético: {coef:.3f}")

        # Guarda un dendrograma por método
        etiquetas = [f"Doc {i+1}" for i in range(len(textos))]
        nombre_salida = f"./dendrograma_{metodo}.png"
        plt.figure(figsize=(10, 5))
        dendrogram(linkage_matrix, labels=etiquetas, leaf_rotation=90)
        plt.title(f"Dendrograma ({metodo})")
        plt.xlabel("Documentos")
        plt.ylabel("Distancia")
        plt.tight_layout()
        plt.savefig(nombre_salida, dpi=300)
        plt.close()
        print(f"   🖼️ Dendrograma guardado en: {nombre_salida}")

    # Mostrar cuál método fue más coherente
    mejor_metodo = max(resultados, key=resultados.get)
    print("\n🏆 RESULTADO FINAL")
    for m, c in resultados.items():
        print(f"   {m:<10} → Coeficiente: {c:.3f}")
    print(f"\n👉 El método más coherente es: **{mejor_metodo.upper()}** ({resultados[mejor_metodo]:.3f})")

if __name__ == "__main__":
    main()
