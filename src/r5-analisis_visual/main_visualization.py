import bibtexparser
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
from fpdf import FPDF

# ------------------------------------------------------------
# 1️⃣ Cargar y procesar datos desde el archivo .bib
# ------------------------------------------------------------
def cargar_datos_bib(ruta_bib):
    with open(ruta_bib, encoding="utf-8") as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)

    datos = []
    for entry in bib_database.entries:
        # Extraer solo el primer autor
        autor = entry.get("author", "Desconocido").split(" and ")[0]

        anio = entry.get("year", "Sin año")
        revista = entry.get("journal", "Sin revista")
        keywords = entry.get("keywords", "")
        abstract = entry.get("abstract", "")

        datos.append({
            "autor": autor,
            "anio": anio,
            "revista": revista,
            "keywords": keywords,
            "abstract": abstract
        })

    return pd.DataFrame(datos)


# ------------------------------------------------------------
# 2️⃣ Mapa de calor geográfico (distribución por país)
# ------------------------------------------------------------
def generar_mapa_calor(df):
    try:
        df.columns = df.columns.str.strip().str.lower()
        col_autor = next((c for c in ["autor", "first_author", "author"] if c in df.columns), None)
        if not col_autor:
            print("No se encontró columna válida para autor.")
            return None

        df['primer_autor'] = df[col_autor].str.split(" and ").str[0]
        conteo = df.groupby('primer_autor').size().reset_index(name='Número de Publicaciones')
        conteo = conteo.sort_values('Número de Publicaciones', ascending=False)

        # Limitar Top 20 autores
        conteo_top = conteo.head(20)
        heatmap_data = conteo_top.set_index('primer_autor')

        plt.figure(figsize=(10, len(conteo_top)*0.5))
        sns.heatmap(heatmap_data, annot=True, cmap="YlGnBu", cbar_kws={'label': 'N° de publicaciones'})
        plt.title("Mapa de calor de publicaciones por primer autor (Top 20)")
        plt.xlabel("Número de publicaciones")
        plt.ylabel("Primer autor")
        plt.tight_layout()

        ruta_mapa = "./mapa_calor.png"
        plt.savefig(ruta_mapa, dpi=300)
        plt.close()
        print("Mapa de calor generado correctamente y guardado como mapa_calor.png")
        return ruta_mapa

    except Exception as e:
        print(f"Error al generar el mapa de calor: {e}")
        return None


# ------------------------------------------------------------
# 3️⃣ Nube de palabras dinámica (abstracts + keywords)
# ------------------------------------------------------------
def generar_nube_palabras(df):
    texto_total = " ".join(df["abstract"].astype(str)) + " " + " ".join(df["keywords"].astype(str))
    nube = WordCloud(width=1000, height=600, background_color="white", colormap="viridis").generate(texto_total)
    plt.figure(figsize=(10,6))
    plt.imshow(nube, interpolation="bilinear")
    plt.axis("off")
    plt.title("Nube de Palabras Frecuentes en Abstracts y Keywords")
    ruta_nube = "./nube_palabras.png"
    plt.tight_layout()
    plt.savefig(ruta_nube, dpi=300)
    plt.close()
    print(f"Nube de palabras guardada en: {ruta_nube}")
    return ruta_nube

# ------------------------------------------------------------
# 4️⃣ Línea temporal de publicaciones
# ------------------------------------------------------------
def generar_linea_temporal(df):
    conteo_anios = df.groupby("anio").size()
    conteo_revistas = df.groupby("revista").size().sort_values(ascending=False).head(10)

    fig, axes = plt.subplots(1, 2, figsize=(12,5))

    conteo_anios.plot(kind="line", ax=axes[0], marker='o')
    axes[0].set_title("Publicaciones por año")
    axes[0].set_xlabel("Año")
    axes[0].set_ylabel("Cantidad")

    conteo_revistas.plot(kind="bar", ax=axes[1], color="skyblue")
    axes[1].set_title("Publicaciones por revista (Top 10)")
    axes[1].set_xlabel("Revista")
    axes[1].set_ylabel("Cantidad")
    plt.xticks(rotation=45, ha='right')

    ruta_linea = "./linea_temporal.png"
    plt.tight_layout()
    plt.savefig(ruta_linea, dpi=300)
    plt.close()
    print(f"Línea temporal guardada en: {ruta_linea}")
    return ruta_linea

# ------------------------------------------------------------
# 5️⃣ Exportar resultados al PDF
# ------------------------------------------------------------
def exportar_a_pdf(rutas_imagenes):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Analisis Visual de la Produccion Cientifica", ln=True, align="C")

    for img in rutas_imagenes:
        pdf.image(img, x=10, y=None, w=180)
        pdf.ln(10)

    ruta_pdf = "./analisis_visual.pdf"
    pdf.output(ruta_pdf)
    print(f"PDF generado en: {ruta_pdf}")

# ------------------------------------------------------------
# 6️⃣ Ejecución principal
# ------------------------------------------------------------
def main():
    ruta = "../../descargas/unificado.bib"
    df = cargar_datos_bib(ruta)
    #df = cargar_datos_bib(ruta)[:100]  
    print(f" {len(df)} registros cargados correctamente.")

    mapa = generar_mapa_calor(df)
    nube = generar_nube_palabras(df)
    linea = generar_linea_temporal(df)

    exportar_a_pdf([mapa, nube, linea])

if __name__ == "__main__":
    main()
