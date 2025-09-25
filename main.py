import asyncio
import os
import re
from pathlib import Path
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()  # Cargar variables de entorno (.env)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, channel="chrome")
        page = await browser.new_page()

        # Ir al login de Google
        await page.goto("https://accounts.google.com/")

        # Login con usuario y contraseña desde .env
        await page.fill('input[type="email"]', os.getenv("GOOGLE_USER"))
        await page.click('button:has-text("Siguiente")')
        await page.wait_for_timeout(2000)
        await page.fill('input[type="password"]', os.getenv("GOOGLE_PASS"))
        async with page.expect_navigation():
            await page.click('button:has-text("Siguiente")')

        # Esperar redirección tras login
        # await page.wait_for_load_state("networkidle")
        # await page.wait_for_navigation()
        print("✅ Login exitoso")

        # Guardar el estado de sesión
        await page.context.storage_state(path="googleAuth.json")

        # Entrar a ScienceDirect con login de Google
        await page.goto("https://www-sciencedirect-com.crai.referencistas.com/")
        await page.click("#btn-google")
        await page.wait_for_timeout(5000)

        # Buscar término
        await page.fill("#qs", "generative artificial intelligence")
        await page.click("button[type=submit]")

        # Iterar sobre resultados
        for i in range(1, 200):  # en tu código solo hace 1 página
            await page.wait_for_selector(".search-result-wrapper li label.checkbox-label")
            checkboxes = await page.query_selector_all(".search-result-wrapper li label.checkbox-label")

            for cb in checkboxes:
                # En Python no hay isChecked() en label, mejor aseguramos click
                await cb.click()
                await page.wait_for_timeout(500)

            print("Página:", i, "checkeada")
            await page.click(".next-link")
            await page.wait_for_timeout(2000)

        # for i in range(0, 100, 25):  # 0, 25, 50
        #     url = f"https://www-sciencedirect-com.crai.referencistas.com/search?qs=generative%20artificial%20intelligence&show=25&offset={i}"
        #     await page.goto(url)
        #     await page.wait_for_selector(".search-result-wrapper li label.checkbox-label")

        #     checkboxes = await page.query_selector_all(".search-result-wrapper li label.checkbox-label")
        #     for cb in checkboxes:
        #         await cb.click()
        #         await page.wait_for_timeout(500)

        #     print(f"Página con offset {i} checkeada")


        # Exportar resultados
        await page.click(".export-all-link-text")
        async with page.expect_download() as download_info:
            await page.click('button[data-aa-button="srp-export-multi-bibtex"]')  # el botón que dispara 
            download = await download_info.value
            path = await download.path()   
            await download.save_as("descargas/sciencedirect.bib") 
            print("📂 Archivo guardado en descargas/export.bib")

        # No cierro browser por debug
        # await browser.close()

async def ieee():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, channel="chrome")
        context = await browser.new_context(storage_state="googleAuth.json")
        page = await context.new_page()

        # Ir a IEEE Xplore
        await page.goto("https://ieeexplore-ieee-org.crai.referencistas.com/Xplore/home.jsp")
        await page.click("#btn-google")
        await page.wait_for_timeout(5000)

        # Buscar término
        await page.fill('input[aria-label="main"]', "generative artificial intelligence")
        await page.click('button[aria-label="Search"]')
        await page.wait_for_timeout(10000)

        for i in range(1,5):
            chechbox_all_results = await page.query_selector('.results-actions-selectall-checkbox')
            if chechbox_all_results:
                await chechbox_all_results.click()
                await page.wait_for_timeout(500)
                
                await page.get_by_text('Export').click()
                await page.get_by_text("Citations").nth(1).click()
                radios = await page.query_selector_all('input[name="download-format"]')
                await radios[1].check()  
                async with page.expect_download() as download_info:
                    await page.click('.stats-SearchResults_Citation_Download')  # el botón que dispara
                    download = await download_info.value
                    path = await download.path()   
                    await download.save_as(f"descargas/ieee{i}.bib") 
                    # print("📂 Archivo guardado en descargas/ieee.bib")
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
    extract_number()



def extract_number():
    folder = Path("descargas")
    files = folder.glob("ieee*.bib")
    with open(folder / "todo.bib", "w", encoding="utf-8") as out:
        for f in files:
            out.write(f.read_text(encoding="utf-8").strip() + "\n\n")


def login_google_account():
    pass

def download_from_science_direct():
    pass

def download_from_ieee():
    pass

def merge_bib_files():
    pass


    
if __name__ == "__main__":
    # asyncio.run(main())
    asyncio.run(ieee())
