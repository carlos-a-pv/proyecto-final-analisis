import asyncio
import os
import random
import bibtexparser
from pathlib import Path
from playwright.async_api import async_playwright
from dotenv import load_dotenv


# =========================
#  Funciones antidetector mejoradas
# =========================

async def human_delay(page, min_ms=1500, max_ms=5000):
    """Espera aleatoria con microvariaciones (simula atención humana)"""
    base_delay = random.randint(min_ms, max_ms)
    # A veces mete pausas pequeñas extra
    if random.random() < 0.3:
        base_delay += random.randint(500, 1500)
    await page.wait_for_timeout(base_delay)


async def human_mouse_move(page):
    """Mueve el mouse de manera más natural (curvas + paradas pequeñas)"""
    width, height = 1920, 1080
    x, y = random.randint(100, width-100), random.randint(100, height-100)
    steps = random.randint(20, 50)
    for _ in range(steps):
        x += random.randint(-50, 50)
        y += random.randint(-50, 50)
        await page.mouse.move(max(0, min(width, x)), max(0, min(height, y)))
        await page.wait_for_timeout(random.randint(30, 120))
        # A veces se detiene un poco más
        if random.random() < 0.1:
            await page.wait_for_timeout(random.randint(500, 1500))


async def human_scroll(page):
    """Hace scroll con pausas como si leyera"""
    for _ in range(random.randint(2, 5)):
        delta_y = random.randint(200, 1000)
        await page.mouse.wheel(0, delta_y)
        await page.wait_for_timeout(random.randint(800, 2000))
        # Simula mirar hacia arriba
        if random.random() < 0.2:
            await page.mouse.wheel(0, -random.randint(100, 500))
            await page.wait_for_timeout(random.randint(800, 1500))


async def human_type_safe(page, selector, text, min_delay=80, max_delay=200):
    """Escribe texto como un humano pero sin errores (seguro para búsquedas)"""
    await page.click(selector)
    for char in text:
        await page.keyboard.type(char)
        await page.wait_for_timeout(random.randint(min_delay, max_delay))
    await page.wait_for_timeout(random.randint(500, 1200))




# =========================
#  Automatizaciones
# =========================

async def download_from_science_direct():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, channel="chrome")
        context = await browser.new_context(storage_state="googleAuth.json")
        page = await context.new_page()

        await page.goto("https://www-sciencedirect-com.crai.referencistas.com/")
        await page.click("#btn-google")
        await human_delay(page)
        await human_mouse_move(page)

        # Buscar término con escritura humana
        await human_type_safe(page, "#qs", "\"generative artificial intelligence\"")
        await page.click("button[type=submit]")
        await human_delay(page, 4000, 6000)

        await page.click('a[data-aa-name="srp-100-results-per-page"]')
        await human_delay(page)

        for i in range(1, 43):
            await human_mouse_move(page)
            await page.click('label[for="select-all-results"]')
            await human_delay(page, 1500, 3000)

            # Exportar resultados
            await page.click(".export-all-link-text")
            async with page.expect_download() as download_info:
                await page.click('button[data-aa-button="srp-export-multi-bibtex"]')
                download = await download_info.value
                await download.save_as(f"descargas/science_direct/pagina{i}.bib")
                print(f"Archivo guardado en descargas/science_direct/pagina{i}.bib")

            await page.click('label[for="select-all-results"]')
            print("Página:", i, "checkeada")

            await page.click(".next-link")
            await human_delay(page, 2000, 4000)

            # Simular distracción aleatoria
            if random.random() < 0.25:  # 25% probabilidad
                await page.wait_for_timeout(random.randint(5000, 10000))
                await human_scroll(page)


async def download_from_ieee():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, channel="chrome")
        context = await browser.new_context(storage_state="googleAuth.json")
        page = await context.new_page()

        await page.goto("https://ieeexplore-ieee-org.crai.referencistas.com/Xplore/home.jsp")
        await page.click("#btn-google")
        await human_delay(page)
        await human_mouse_move(page)

        await human_type_safe(page, 'input[aria-label="main"]', "\"generative artificial intelligence\"")
        await page.click('button[aria-label="Search"]')
        await human_delay(page, 8000, 12000)

        await page.get_by_text('Items Per Page').click()
        await human_delay(page)
        await page.get_by_role("button", name="100").click()
        await human_delay(page)

        for i in range(1, 15):
            await human_delay(page, 1000, 3000)
            chechbox_all_results = await page.query_selector('.results-actions-selectall-checkbox')
            if chechbox_all_results:
                await chechbox_all_results.click()
                await human_delay(page, 500, 1500)

                await page.get_by_text('Export').click()
                await page.get_by_text("Citations").nth(1).click()

                radios = await page.query_selector_all('input[name="download-format"]')
                await radios[1].check()
                async with page.expect_download() as download_info:
                    await page.click('.stats-SearchResults_Citation_Download')
                    download = await download_info.value
                    await download.save_as(f"descargas/ieee/pagina{i}.bib")
                    await page.get_by_text('Cancel').click()
                    await human_delay(page, 2500, 4000)

                next_button = await page.query_selector('button[aria-label="Next page of search results"]')
                if next_button:
                    await next_button.click()
                    await human_delay(page, 2000, 5000)
                else:
                    break
            else:
                print("No se encontró el checkbox para seleccionar todos los resultados.")
                break

            # Simular distracción
            if random.random() < 0.25:
                await page.wait_for_timeout(random.randint(5000, 10000))
                await human_scroll(page)

            print(f"Página {i} checkeada")


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
        await human_delay(page, 2000, 4000)
        await page.fill('input[type="password"]', os.getenv("GOOGLE_PASS"))
        async with page.expect_navigation():
            await page.click('button:has-text("Siguiente")')
        print("✅ Login exitoso")
        await page.context.storage_state(path="googleAuth.json")
        await browser.close()


def merge_bib_files(base_dir="descargas", output_file="descargas/unificado.bib", repetidos_file="descargas/repetidos.bib"):
    entradas_unicas = []
    entradas_repetidas = []
    titulos_vistos = set()

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

    db_unicos = bibtexparser.bibdatabase.BibDatabase()
    db_unicos.entries = entradas_unicas
    writer = bibtexparser.bwriter.BibTexWriter()
    writer.indent = "    "

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(writer.write(db_unicos))

    if entradas_repetidas:
        db_repes = bibtexparser.bibdatabase.BibDatabase()
        db_repes.entries = entradas_repetidas
        with open(repetidos_file, "w", encoding="utf-8") as f:
            f.write(writer.write(db_repes))

    print(f"✅ Archivo unificado: {output_file}")
    print(f"⚠️ Repetidos encontrados: {len(entradas_repetidas)} (guardados en {repetidos_file})")


async def main():
    load_dotenv()
    #await login_google_account()
    #await download_from_science_direct()
    await download_from_ieee()
    merge_bib_files(base_dir="descargas", output_file="descargas/unificado.bib", repetidos_file="descargas/repetidos.bib")


if __name__ == "__main__":
    asyncio.run(main())
