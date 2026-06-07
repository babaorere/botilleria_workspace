import sys
import requests
import uuid
import time

# Direct DB queries for assertions (runs inside the docker container)
from config.database import SessionLocal
from models import CartItem

TENANT_ID = "e82fe25b-10c8-42c9-91f4-c97264cb09d0"
BASE_URL = "http://localhost:8000"


def get_db_cart(session_id):
    db = SessionLocal()
    try:
        items = db.query(CartItem).filter(CartItem.session_id == session_id).all()
        result = []
        for item in items:
            result.append(
                {"quantity": item.quantity, "product_name": item.product.name}
            )
        return result
    finally:
        db.close()


def send_chat_message(session_id, user_id, message):
    headers = {"X-Tenant-ID": TENANT_ID, "Content-Type": "application/json"}
    payload = {
        "user_id": user_id,
        "platform": "whatsapp",
        "message": message,
        "session_id": session_id,
    }
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/chat", json=payload, headers=headers)
    response.raise_for_status()
    latency = time.time() - start_time
    data = response.json()
    print(f"👤 Usuario: {message}")
    print(f"🤖 Asistente (Latencia: {latency:.2f}s): {data.get('response')}\n")
    return data


def run_scenario_1_support():
    print("==============================================================")
    print("ESCENARIO 1: ATENCIÓN AL CLIENTE Y FAQS")
    print("==============================================================")
    session_id = str(uuid.uuid4())
    user_id = f"user_support_{int(time.time())}"

    # 1. Saludo inicial
    send_chat_message(session_id, user_id, "Hola, buenas tardes.")

    # 2. Preguntar dirección y horarios
    send_chat_message(
        session_id, user_id, "¿Dónde están ubicados y hasta qué hora atienden?"
    )

    # 3. Preguntar por producto inexistente
    send_chat_message(
        session_id, user_id, "¿Tienen whisky azul etiqueta dorada de 50 años?"
    )

    # 4. Preguntar por catálogo de cervezas
    send_chat_message(session_id, user_id, "¿Qué cervezas tienen en stock?")

    print("✓ Escenario 1 completado.\n")


def run_scenario_2_cancellation():
    print("==============================================================")
    print("ESCENARIO 2: COMPRA Y CANCELACIÓN DE PEDIDO")
    print("==============================================================")
    session_id = str(uuid.uuid4())
    user_id = f"user_cancel_{int(time.time())}"

    # 1. Agregar productos
    send_chat_message(
        session_id, user_id, "Hola, por favor agrega 3 cervezas Heineken al carro."
    )
    time.sleep(1)

    # Verificación en BD
    items = get_db_cart(session_id)
    print(f"[BD Check] Items en carrito: {len(items)}")
    assert len(items) == 1, "Debería haber 1 tipo de item en el carrito."
    assert items[0]["quantity"] == 3, "Debería haber 3 Heineken."
    assert "Heineken" in items[0]["product_name"]

    # 2. Cancelar pedido / Vaciar carro
    send_chat_message(
        session_id,
        user_id,
        "No, mejor ya no quiero comprar nada. Cancela todo y vacía mi carro.",
    )
    time.sleep(1)

    # Verificación en BD
    items = get_db_cart(session_id)
    print(f"[BD Check] Items en carrito después de cancelar: {len(items)}")
    assert len(items) == 0, "El carrito debería estar vacío tras la cancelación."

    print("✓ Escenario 2 completado con verificación en BD.\n")


def run_scenario_3_changes():
    print("==============================================================")
    print("ESCENARIO 3: COMPRA CON MODIFICACIONES / CAMBIO DE CANTIDAD")
    print("==============================================================")
    session_id = str(uuid.uuid4())
    user_id = f"user_change_{int(time.time())}"

    # 1. Agregar Kunstmann
    send_chat_message(
        session_id, user_id, "Buenas, agrégame 2 cervezas Kunstmann Torobayo al carro."
    )
    time.sleep(1)

    # Verificación en BD
    items = get_db_cart(session_id)
    print(f"[BD Check] Items en carrito: {len(items)}")
    assert len(items) == 1, "Debería haber 1 producto en el carrito."
    assert items[0]["quantity"] == 2, "La cantidad debería ser 2."

    # 2. Modificación: cambiar cantidad (limpiando y re-agregando en lenguaje natural)
    send_chat_message(
        session_id,
        user_id,
        "Oye, mejor cambia la cantidad a 4 de esas Kunstmann por favor. Limpia el carro primero y pon las 4.",
    )
    time.sleep(1)

    # Verificación en BD
    items = get_db_cart(session_id)
    print(f"[BD Check] Items en carrito tras cambio: {len(items)}")
    assert len(items) == 1, "Debería seguir habiendo 1 producto en el carrito."
    assert items[0]["quantity"] == 4, (
        "La cantidad de Kunstmann debería haberse actualizado a 4."
    )

    print("✓ Escenario 3 completado con verificación en BD.\n")


def run_scenario_4_abuse():
    print("==============================================================")
    print("ESCENARIO 4: DETECCIÓN DE GARABATOS Y REDIRECCIÓN A HUMANO")
    print("==============================================================")
    session_id = str(uuid.uuid4())
    user_id = f"user_abuse_{int(time.time())}"

    # 1. Insulto inicial
    send_chat_message(session_id, user_id, "Eres una soberana basura de bot estúpido.")

    # 2. Insistencia y solicitud de humano
    send_chat_message(
        session_id,
        user_id,
        "No me sirves para nada inútil de mierda, pásame con alguien de verdad.",
    )

    print("✓ Escenario 4 completado.\n")


def main():
    print("==============================================================")
    print("INICIANDO PRUEBAS COMPRENSIVAS DE CAPACIDAD DE INTERACCIÓN E2E")
    print("==============================================================")

    try:
        run_scenario_1_support()
        # Pequeña pausa entre escenarios para no estresar el servidor
        time.sleep(2)

        run_scenario_2_cancellation()
        time.sleep(2)

        run_scenario_3_changes()
        time.sleep(2)

        run_scenario_4_abuse()

        print("==============================================================")
        print("🎉 ¡TODOS LOS ESCENARIOS DE INTERACCIÓN COMPLETADOS CON ÉXITO!")
        print("==============================================================")
    except Exception as e:
        print(f"❌ Error durante la ejecución de los escenarios: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
