import asyncio
import os
import re
import bibtexparser
from pathlib import Path
from playwright.async_api import async_playwright
from dotenv import load_dotenv

async def download_from_science_direct():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, channel="chrome")
        context = await browser.new_context(storage_state="googleAuth.json")
        page = await context.new_page()

        # Entrar a ScienceDirect 
        await page.goto("https://www-sciencedirect-com.crai.referencistas.com/")
        await page.click("#btn-google")
        await page.wait_for_timeout(5000)

        # Buscar término
        await page.fill("#qs", "\"generative artificial intelligence\"")
        await page.click("button[type=submit]")
        await page.wait_for_timeout(5000)
        # await page.get_by_text('100').nth(1).click()
        await page.click('a[data-aa-name="srp-100-results-per-page"]')

        await page.wait_for_timeout(5000)
        # Iterar sobre resultados
        for i in range(1, 43): 
            await page.click('label[for="select-all-results"]')
            await page.wait_for_timeout(2000)
        # Exportar resultados
            await page.click(".export-all-link-text")
            async with page.expect_download() as download_info:
                await page.click('button[data-aa-button="srp-export-multi-bibtex"]')
                download = await download_info.value
                path = await download.path()   
                await download.save_as(f"descargas/science_direct/pagina{i}.bib") 
                print(f"Archivo guardado en descargas/science_direct/pagina{i}.bib")

                await page.click('label[for="select-all-results"]')
                print("Página:", i, "checkeada")
                
                await page.click(".next-link")
                await page.wait_for_timeout(2000)
                
async def download_from_ieee():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, channel="chrome")
        context = await browser.new_context(storage_state="googleAuth.json")
        page = await context.new_page()

        # Ir a IEEE Xplore
        await page.goto("https://ieeexplore-ieee-org.crai.referencistas.com/Xplore/home.jsp")
        await page.click("#btn-google")
        await page.wait_for_timeout(5000)

        # Buscar término
        await page.fill('input[aria-label="main"]', "\"generative artificial intelligence\"")
        await page.click('button[aria-label="Search"]')
        await page.wait_for_timeout(10000)

        await page.get_by_text('Items Per Page').click()
        await page.wait_for_timeout(2000)
        await page.get_by_role("button", name="100").click()
        await page.wait_for_timeout(5000)        

        for i in range(1,15):
            await page.wait_for_timeout(2000)
            chechbox_all_results = await page.query_selector('.results-actions-selectall-checkbox')
            if chechbox_all_results:
                await chechbox_all_results.click()
                await page.wait_for_timeout(500)
                
                await page.get_by_text('Export').click()
                await page.get_by_text("Citations").nth(1).click()
                # await page.click('#ngb-nav-4')
                radios = await page.query_selector_all('input[name="download-format"]')
                await radios[1].check()  
                async with page.expect_download() as download_info:
                    await page.click('.stats-SearchResults_Citation_Download')  # el botón que dispara
                    download = await download_info.value
                    path = await download.path()   
                    await download.save_as(f"descargas/ieee/pagina{i}.bib") 
                    await page.get_by_text('Cancel').click()
                    await page.wait_for_timeout(3000)
                
                next_button = await page.query_selector('button[aria-label="Next page of search results"]')
                if next_button:
                    await next_button.click()
                    await page.wait_for_timeout(2000)
                else:
                    break  # No hay más páginas

                # Exportar resultados
            else:
                print("No se encontró el checkbox para seleccionar todos los resultados.")
                break

            print(f"Página {i} checkeada")
    # extract_number()

def extract_number():
    folder = Path("descargas")
    files = folder.glob("ieee*.bib")
    with open(folder / "todo.bib", "w", encoding="utf-8") as out:
        for f in files:
            out.write(f.read_text(encoding="utf-8").strip() + "\n\n")

async def login_google_account():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, channel="chrome")
        page = await browser.new_page()
        await page.goto("https://accounts.google.com/")
        await page.fill('input[type="email"]', os.getenv("GOOGLE_USER"))
        await page.click('button:has-text("Siguiente")')
        await page.wait_for_timeout(2000)
        await page.fill('input[type="password"]', os.getenv("GOOGLE_PASS"))
        async with page.expect_navigation():
            await page.click('button:has-text("Siguiente")')
        print("✅ Login exitoso")
        await page.context.storage_state(path="googleAuth.json")
        browser.close()


def merge_bib_files(base_dir="descargas", output_file="descargas/unificado.bib", repetidos_file="/descargas/repetidos.bib"):
    entradas_unicas = []
    entradas_repetidas = []
    titulos_vistos = set()

    # Recorrer las carpetas ieee y sciencedirect
    for db in ["ieee", "science_direct"]:
        folder = os.path.join(base_dir, db)
        if not os.path.exists(folder):
            continue

        for file in os.listdir(folder):
            if file.endswith(".bib"):
                ruta = os.path.join(folder, file)
                with open(ruta, encoding="utf-8") as bibtex_file:
                    bib_database = bibtexparser.load(bibtex_file)

                for entry in bib_database.entries:
                    title = entry.get("title", "").strip().lower()

                    if title in titulos_vistos:
                        entradas_repetidas.append(entry)
                    else:
                        titulos_vistos.add(title)
                        entradas_unicas.append(entry)

    # Guardar únicos
    db_unicos = bibtexparser.bibdatabase.BibDatabase()
    db_unicos.entries = entradas_unicas
    writer = bibtexparser.bwriter.BibTexWriter()
    writer.indent = "    "

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(writer.write(db_unicos))

    # Guardar repetidos
    if entradas_repetidas:
        db_repes = bibtexparser.bibdatabase.BibDatabase()
        db_repes.entries = entradas_repetidas
        with open(repetidos_file, "w", encoding="utf-8") as f:
            f.write(writer.write(db_repes))

    print(f"✅ Archivo unificado: {output_file}")
    print(f"⚠️ Repetidos encontrados: {len(entradas_repetidas)} (guardados en {repetidos_file})")


async def main():
    load_dotenv()
    # asyncio.run((login_google_account()))
    # asyncio.run((download_from_science_direct()))
    # asyncio.run((download_from_ieee()))
    merge_bib_files(base_dir="descargas", output_file="descargas/unificado.bib", repetidos_file="descargas/repetidos.bib")
    
if __name__ == "__main__":
    main()
    
