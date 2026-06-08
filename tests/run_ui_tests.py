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
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
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
        # Abrimos el navegador Chromium visible (headless=False)
        # slow_mo introduce una pausa entre clics y teclas para simular ritmo humano
        browser = p.chromium.launch(headless=False, slow_mo=800)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        
        # -----------------------------------------------------------------------
        # PASO 1: Ingreso al Portal de Administración
        # -----------------------------------------------------------------------
        print("\n[Paso 1] Navegando al Portal de Administración...")
        page.goto(f"{BASE_URL}/admin/")
        
        print("Ingresando credenciales de administrador principal...")
        # El username "admin" es de solo lectura, ingresamos la clave
        page.fill("#loginPassword", ADMIN_API_KEY)
        page.click("button[type='submit']")
        
        # Esperar a que se oculte el modal de login y cargue la vista
        page.wait_for_selector("#addTenantBtn")
        print("[OK] ¡Sesión iniciada con éxito como Administrador!")
        time.sleep(1)

        # -----------------------------------------------------------------------
        # PASO 2: Creación de Tenants con Combinación de Claves (Manual y Auto)
        # -----------------------------------------------------------------------
        print("\n[Paso 2] Probando combinatorias de creación de Tenant...")
        
        # --- Caso A: Tenant con contraseña manual ---
        print("-> Caso A: Creando tenant 'test_manual' con contraseña explícita...")
        page.click("#addTenantBtn")
        page.wait_for_selector("#tenantForm")
        
        page.fill("#tenantSlug", "test_manual")
        page.fill("#tenantName", "Botillería Test Manual")
        page.fill("#tenantPortalToken", "manualpassword123")
        page.fill("#tenantInstruction", "Eres el bot de pruebas manuales. Sé divertido y ágil.")
        page.click("button[type='submit']")
        
        # El navegador disparará una alerta (JavaScript alert) con las credenciales
        # Configuramos un handler para capturarla y cerrarla automáticamente
        def handle_alert(dialog):
            print(f"[ALERT DIALOG] {dialog.message}")
            dialog.accept()
            
        page.once("dialog", handle_alert)
        time.sleep(1) # Esperar a que el modal se procese y lance la alerta
        print("[OK] Tenant 'test_manual' creado con contraseña 'manualpassword123'.")
        
        # --- Caso B: Tenant con contraseña autogenerada ---
        print("\n-> Caso B: Creando tenant 'test_auto' con contraseña autogenerada...")
        page.click("#addTenantBtn")
        page.wait_for_selector("#tenantForm")
        
        page.fill("#tenantSlug", "test_auto")
        page.fill("#tenantName", "Botillería Autogenerada")
        # Dejamos la clave vacía para activar la autogeneración en el backend
        page.fill("#tenantPortalToken", "")
        page.fill("#tenantInstruction", "") # Sin prompt para probar el fallback global
        
        captured_auto_password = ""
        def handle_auto_alert(dialog):
            nonlocal captured_auto_password
            msg = dialog.message
            print(f"[ALERT DIALOG] {msg}")
            # Extraer contraseña del mensaje de alerta
            for line in msg.split("\n"):
                if "Contraseña:" in line:
                    captured_auto_password = line.split(":", 1)[1].strip()
            dialog.accept()
            
        page.once("dialog", handle_auto_alert)
        page.click("button[type='submit']")
        time.sleep(1)
        print(f"[OK] Tenant 'test_auto' creado. Clave autogenerada capturada: '{captured_auto_password}'")

        # -----------------------------------------------------------------------
        # PASO 3: Cambio de Contraseña de Tenant (Regla de Negocio)
        # -----------------------------------------------------------------------
        print("\n[Paso 3] Probando cambio de contraseña en panel de admin...")
        # En la tabla de tenants, buscamos la fila del tenant 'test_manual' y hacemos clic en el botón de Clave
        # Localizamos el botón "🔑 Clave" del tenant 'test_manual'
        key_button_selector = "//tr[td[text()='test_manual']]//button[contains(text(), '🔑 Clave')]"
        page.click(key_button_selector)
        page.wait_for_selector("#passwordForm")
        
        print("Cambiando la contraseña de 'test_manual' a 'newsecurepassword99'...")
        page.fill("#newPortalToken", "newsecurepassword99")
        page.click("#passwordForm button[type='submit']")
        time.sleep(1)
        print("[OK] Contraseña cambiada exitosamente.")

        # -----------------------------------------------------------------------
        # PASO 4: Ingreso al Portal del Tenant
        # -----------------------------------------------------------------------
        print("\n[Paso 4] Navegando al Portal del Tenant e iniciando sesión...")
        page.goto(f"{BASE_URL}/tenant/")
        
        print("Ingresando credenciales del Tenant 'test_manual'...")
        # Llenamos las credenciales en el login de tenant
        page.wait_for_selector("#loginForm")
        # En la interfaz de login, el campo de usuario tiene el id 'loginUsername'
        page.fill("#loginUsername", "test_manual")
        page.fill("#loginPassword", "newsecurepassword99")
        page.click("button[type='submit']")
        
        # Esperamos a que cargue la interfaz del tenant
        page.wait_for_selector("a[data-section='products']")
        print("[OK] Sesión iniciada con éxito en el Portal del Tenant!")
        
        # -----------------------------------------------------------------------
        # PASO 5: Combinatoria de Gestión de Productos
        # -----------------------------------------------------------------------
        print("\n[Paso 5] Probando creación y edición de productos en el catálogo...")
        page.click("a[data-section='products']")
        page.wait_for_selector("#addProductBtn")
        
        # --- Crear Producto 1 ---
        print("-> Agregando Producto 1 (Cerveza Corona)...")
        page.click("#addProductBtn")
        page.wait_for_selector("#productForm")
        
        page.fill("#productName", "Cerveza Corona Extra 355ml")
        page.fill("#productDescription", "Cerveza rubia tipo lager, importada de México.")
        page.fill("#productPrice", "1500")
        page.fill("#productStock", "24")
        page.fill("#productCategory", "Cervezas")
        page.click("#productForm button[type='submit']")
        time.sleep(1)
        print("[OK] Producto 1 creado.")
        
        # --- Crear Producto 2 ---
        print("-> Agregando Producto 2 (Pisco Mistral)...")
        page.click("#addProductBtn")
        page.wait_for_selector("#productForm")
        
        page.fill("#productName", "Pisco Mistral 35º 750ml")
        page.fill("#productDescription", "Pisco de uvas Pedro Jiménez y Moscatel envejecido en barricas de roble.")
        page.fill("#productPrice", "7200")
        page.fill("#productStock", "12")
        page.fill("#productCategory", "Destilados")
        page.click("#productForm button[type='submit']")
        time.sleep(1)
        print("[OK] Producto 2 creado.")
        
        # --- Editar Producto ---
        print("-> Modificando precio y stock del Producto 1...")
        # Ubicamos la fila de 'Cerveza Corona Extra 355ml' en la tabla de productos
        edit_button_selector = "//tr[td[text()='Cerveza Corona Extra 355ml']]//button[contains(text(), 'Editar')]"
        page.click(edit_button_selector)
        page.wait_for_selector("#productForm")
        
        # Editamos el precio a 1600 y stock a 48
        page.fill("#productPrice", "1600")
        page.fill("#productStock", "48")
        page.click("#productForm button[type='submit']")
        time.sleep(1)
        print("[OK] Producto modificado con éxito.")
        
        # -----------------------------------------------------------------------
        # PASO 6: Prueba de Disponibilidad Humana (Visual y Funcional)
        # -----------------------------------------------------------------------
        print("\n[Paso 6] Probando toggle de disponibilidad humana en el panel...")
        page.click("a[data-section='dashboard']")
        page.wait_for_selector("#humanAvailableToggle")
        
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

        # Finalización
        print("\n=====================================================================")
        print(" ✓ TODAS LAS PRUEBAS E2E TERMINARON EXITOSAMENTE ")
        print("=====================================================================")
        time.sleep(2)
        browser.close()

if __name__ == "__main__":
    run_tests()
