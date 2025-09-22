import asyncio
import os
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

        # Screenshot
        await page.screenshot(path="screenshot.png", full_page=True)

        # Iterar sobre resultados
        for i in range(1, 2):  # en tu código solo hace 1 página
            await page.wait_for_selector(".search-result-wrapper li label.checkbox-label")
            checkboxes = await page.query_selector_all(".search-result-wrapper li label.checkbox-label")

            for cb in checkboxes:
                # En Python no hay isChecked() en label, mejor aseguramos click
                await cb.click()
                await page.wait_for_timeout(500)

            print("Página:", i, "checkeada")
            await page.click(".pagination-link")
            await page.wait_for_timeout(2000)

        # Exportar resultados
        await page.click(".export-all-link-text")
        async with page.expect_download() as download_info:
            await page.click('button[data-aa-button="srp-export-multi-bibtex"]')  # el botón que dispara 
            download = await download_info.value
            path = await download.path()   # ruta temporal del archivo descargado
            await download.save_as("descargas/export.bib")  # guardarlo donde quieras
            print("📂 Archivo guardado en descargas/export.bib")

        # No cierro browser por debug
        # await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
