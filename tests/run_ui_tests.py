#!/usr/bin/env python3
# ===============================================================================
# run_ui_tests.py — Pruebas de Interfaz End-to-End (E2E) con Playwright
# ===============================================================================
# Simula a un humano operando los paneles de administración y del tenant
# realizando combinaciones de opciones en cada caso con navegador visible.
# ===============================================================================

import os
import sys
import time
import subprocess

# --- Auto-instalación de Playwright si no está presente ---
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("[WARN] Playwright no está instalado. Instalándolo en el sistema...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
    from playwright.sync_api import sync_playwright

# --- Cargar configuración del .env.local ---
def get_env_variable(var_name, default=None):
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "botilleria_core", ".env.local")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    if "=" in line:
                        key, val = line.strip().split("=", 1)
                        if key.strip() == var_name:
                            return val.strip()
    return os.environ.get(var_name, default)

ADMIN_API_KEY = get_env_variable("ADMIN_API_KEY", "botilleria-admin-key-2026-v2")
PORT = 8083
BASE_URL = f"http://localhost:{PORT}"

def run_tests():
    print("=====================================================================")
    print(" INICIANDO PRUEBAS E2E DE INTERFAZ DE BOTILLERÍA (MODO HUMANO) ")
    print("=====================================================================")
    
    with sync_playwright() as p:
        # Abrimos el navegador Chrome del sistema visible (headless=False)
        # slow_mo introduce una pausa entre clics y teclas para simular ritmo humano
        browser = p.chromium.launch(headless=False, slow_mo=800, channel="chrome")
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        
        captured_auto_password = ""

        # Manejador global de alertas/diálogos de JavaScript
        def handle_dialog(dialog):
            nonlocal captured_auto_password
            msg = dialog.message
            print(f"[ALERT DIALOG] {msg}")
            if "Contraseña:" in msg:
                for line in msg.split("\n"):
                    if "Contraseña:" in line:
                        captured_auto_password = line.split(":", 1)[1].strip()
            dialog.accept()
            
        page.on("dialog", handle_dialog)
        
        # Console & error logging to debug browser issues
        page.on("console", lambda msg: print(f"[BROWSER CONSOLE] {msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: print(f"[BROWSER ERROR] {err}"))
        
        # -----------------------------------------------------------------------
        # PASO 1: Ingreso al Portal de Administración
        # -----------------------------------------------------------------------
        print("\n[Paso 1] Navegando al Portal de Administración...")
        page.goto(f"{BASE_URL}/admin/")
        # Limpiar localStorage para forzar login de admin
        page.evaluate("() => localStorage.clear()")
        page.reload()
        
        print("Ingresando credenciales de administrador principal...")
        # El username "admin" es de solo lectura, ingresamos la clave
        page.fill("#loginPassword", ADMIN_API_KEY)
        page.click("#loginForm button[type='submit']")
        
        # Esperar a que se oculte el modal de login y cargue la vista
        page.wait_for_selector("#tenantCount")
        print("[OK] ¡Sesión iniciada con éxito como Administrador!")
        time.sleep(1)

        # -----------------------------------------------------------------------
        # PASO 2: Creación de Tenants con Combinación de Claves (Manual y Auto)
        # -----------------------------------------------------------------------
        print("\n[Paso 2] Probando combinatorias de creación de Tenant...")
        
        # Generar sufijo único para hacer la prueba idempotente y evitar colisión
        import random
        suffix = str(random.randint(1000, 9999))
        tenant_slug_manual = f"test_manual_{suffix}"
        tenant_slug_auto = f"test_auto_{suffix}"
        
        # Navegar a la pestaña de Tenants para hacer visible el botón
        page.click("a[data-section='tenants']")
        page.wait_for_selector("#addTenantBtn")
        
        # --- Caso A: Tenant con contraseña manual ---
        print(f"-> Caso A: Creando tenant '{tenant_slug_manual}' con contraseña explícita...")
        page.click("#addTenantBtn")
        page.wait_for_selector("#tenantForm")
        
        page.fill("#tenantSlug", tenant_slug_manual)
        page.fill("#tenantName", f"Botillería Test Manual {suffix}")
        page.fill("#tenantPortalToken", "manualpassword123")
        page.fill("#tenantInstruction", "Eres el bot de pruebas manuales. Sé divertido y ágil.")
        page.click("#tenantForm button[type='submit']")
        time.sleep(2) # Esperar a que se procese, se lance y se acepte la alerta
        print(f"[OK] Tenant '{tenant_slug_manual}' creado con contraseña 'manualpassword123'.")
        
        # --- Caso B: Tenant con contraseña autogenerada ---
        print(f"\n-> Caso B: Creando tenant '{tenant_slug_auto}' con contraseña autogenerada...")
        page.click("#addTenantBtn")
        page.wait_for_selector("#tenantForm")
        
        page.fill("#tenantSlug", tenant_slug_auto)
        page.fill("#tenantName", f"Botillería Autogenerada {suffix}")
        # Dejamos la clave vacía para activar la autogeneración en el backend
        page.fill("#tenantPortalToken", "")
        page.fill("#tenantInstruction", "") # Sin prompt para probar el fallback global
        page.click("#tenantForm button[type='submit']")
        time.sleep(2) # Esperar a que se procese, se lance y se acepte la alerta
        print(f"[OK] Tenant '{tenant_slug_auto}' creado. Clave autogenerada capturada: '{captured_auto_password}'")

        # -----------------------------------------------------------------------
        # PASO 3: Cambio de Contraseña de Tenant (Regla de Negocio)
        # -----------------------------------------------------------------------
        print("\n[Paso 3] Probando cambio de contraseña en panel de admin...")
        # En la tabla de tenants, buscamos la fila del tenant y hacemos clic en el botón de Clave
        key_button_selector = f"//tr[td[text()='{tenant_slug_manual}']]//button[contains(text(), '🔑 Clave')]"
        page.click(key_button_selector)
        page.wait_for_selector("#passwordForm")
        
        print(f"Cambiando la contraseña de '{tenant_slug_manual}' a 'newsecurepassword99'...")
        page.fill("#newPortalToken", "newsecurepassword99")
        page.click("#passwordForm button[type='submit']")
        time.sleep(1)
        print("[OK] Contraseña cambiada exitosamente.")

        # -----------------------------------------------------------------------
        # PASO 4: Ingreso al Portal del Tenant
        # -----------------------------------------------------------------------
        print("\n[Paso 4] Navegando al Portal del Tenant e iniciando sesión...")
        page.goto(f"{BASE_URL}/tenant/")
        # Limpiar localStorage para forzar que se muestre el formulario de login
        page.evaluate("() => localStorage.clear()")
        page.reload()
        
        print(f"Ingresando credenciales del Tenant '{tenant_slug_manual}'...")
        # Llenamos las credenciales en el login de tenant
        page.wait_for_selector("#loginForm")
        # En la interfaz de login, el campo de usuario tiene el id 'loginUsername'
        page.fill("#loginUsername", tenant_slug_manual)
        page.fill("#loginPassword", "newsecurepassword99")
        page.click("#loginForm button[type='submit']")
        
        # Esperamos a que cargue la interfaz del tenant
        page.wait_for_selector("a[data-section='products']")
        print("[OK] Sesión iniciada con éxito en el Portal del Tenant!")
        
        # -----------------------------------------------------------------------
        # PASO 5: Combinatoria de Gestión de Productos
        # -----------------------------------------------------------------------
        print("\n[Paso 5] Creando categorías y probando creación/edición de productos...")
        
        # --- Crear Categoría Cervezas ---
        print("Creando categoría 'Cervezas'...")
        page.click("a[data-section='categories']")
        page.wait_for_selector("#addCategoryBtn")
        page.click("#addCategoryBtn")
        page.wait_for_selector("#categoryForm")
        page.fill("#catName", "Cervezas")
        page.fill("#catDesc", "Todo tipo de cervezas y cervezas artesanales")
        page.click("#categoryForm button[type='submit']")
        time.sleep(1.5)
        
        # --- Crear Categoría Destilados ---
        print("Creando categoría 'Destilados'...")
        page.click("#addCategoryBtn")
        page.wait_for_selector("#categoryForm")
        page.fill("#catName", "Destilados")
        page.fill("#catDesc", "Pisco, Ron, Whisky, Vodka y otros destilados")
        page.click("#categoryForm button[type='submit']")
        time.sleep(1.5)
        
        # --- Ir a Productos ---
        page.click("a[data-section='products']")
        page.wait_for_selector("#addProductBtn")
        
        # --- Crear Producto 1 ---
        print("-> Agregando Producto 1 (Cerveza Corona)...")
        page.click("#addProductBtn")
        page.wait_for_selector("#productForm")
        
        page.fill("#prodName", "Cerveza Corona Extra 355ml")
        page.fill("#prodDesc", "Cerveza rubia tipo lager, importada de México.")
        page.fill("#prodPrice", "1500")
        page.fill("#prodStock", "24")
        page.select_option("#prodCategory", value="Cervezas")
        page.click("#productForm button[type='submit']")
        time.sleep(1.5)
        print("[OK] Producto 1 creado.")
        
        # --- Crear Producto 2 ---
        print("-> Agregando Producto 2 (Pisco Mistral)...")
        page.click("#addProductBtn")
        page.wait_for_selector("#productForm")
        
        page.fill("#prodName", "Pisco Mistral 35º 750ml")
        page.fill("#prodDesc", "Pisco de uvas Pedro Jiménez y Moscatel envejecido en barricas de roble.")
        page.fill("#prodPrice", "7200")
        page.fill("#prodStock", "12")
        page.select_option("#prodCategory", value="Destilados")
        page.click("#productForm button[type='submit']")
        time.sleep(1.5)
        print("[OK] Producto 2 creado.")
        
        # --- Editar Producto ---
        print("-> Modificando precio y stock del Producto 1...")
        # Ubicamos la fila de 'Cerveza Corona Extra 355ml' en la tabla de productos
        edit_button_selector = "//tr[td[text()='Cerveza Corona Extra 355ml']]//button[contains(text(), 'Editar')]"
        page.click(edit_button_selector)
        page.wait_for_selector("#productForm")
        
        # Editamos el precio a 1600 y stock a 48
        page.fill("#prodPrice", "1600")
        page.fill("#prodStock", "48")
        page.click("#productForm button[type='submit']")
        time.sleep(1.5)
        print("[OK] Producto modificado con éxito.")
        
        # -----------------------------------------------------------------------
        # PASO 6: Prueba de Disponibilidad Humana (Visual y Funcional)
        # -----------------------------------------------------------------------
        print("\n[Paso 6] Probando toggle de disponibilidad humana en el panel...")
        page.click("a[data-section='dashboard']")
        page.wait_for_selector(".human-available-toggle label.switch")
        
        # Hacemos clic en el toggle para cambiar el estado
        print("Activando disponibilidad humana...")
        page.click(".human-available-toggle label.switch")
        time.sleep(1)
        status_text = page.locator("#humanAvailableStatus").text_content()
        print(f"Estado de disponibilidad en pantalla: '{status_text}'")
        
        print("Desactivando disponibilidad humana...")
        page.click(".human-available-toggle label.switch")
        time.sleep(1)
        status_text = page.locator("#humanAvailableStatus").text_content()
        print(f"Estado de disponibilidad en pantalla: '{status_text}'")
        print("[OK] Disponibilidad humana probada.")

        # -----------------------------------------------------------------------
        # PASO 7: Limpieza de Datos de Prueba (Eliminar tenants creados)
        # -----------------------------------------------------------------------
        print("\n[Paso 7] Limpiando datos de prueba (Eliminando tenants creados)...")
        page.goto(f"{BASE_URL}/admin/")
        if page.locator("#loginPassword").is_visible():
            print("Iniciando sesión en el Portal de Administración para limpieza...")
            page.fill("#loginPassword", ADMIN_API_KEY)
            page.click("#loginForm button[type='submit']")
        
        page.wait_for_selector("#tenantCount")
        page.click("a[data-section='tenants']")
        page.wait_for_selector("#addTenantBtn")
        
        # Eliminar tenant_slug_manual
        delete_manual_selector = f"//tr[td[text()='{tenant_slug_manual}']]//button[contains(text(), 'Eliminar')]"
        print(f"Eliminando tenant '{tenant_slug_manual}'...")
        page.click(delete_manual_selector)
        time.sleep(1.5)
        
        # Eliminar tenant_slug_auto
        delete_auto_selector = f"//tr[td[text()='{tenant_slug_auto}']]//button[contains(text(), 'Eliminar')]"
        print(f"Eliminando tenant '{tenant_slug_auto}'...")
        page.click(delete_auto_selector)
        time.sleep(1.5)
        print("[OK] Limpieza completada.")

        browser.close()

if __name__ == "__main__":
    run_tests()
