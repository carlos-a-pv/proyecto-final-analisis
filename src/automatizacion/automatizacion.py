import asyncio
import os
import re
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

def merge_bib_files():
    pass

def main():
    load_dotenv()
    # asyncio.run((login_google_account()))
    # asyncio.run((download_from_science_direct()))
    asyncio.run((download_from_ieee()))
    
if __name__ == "__main__":
    main()
    
