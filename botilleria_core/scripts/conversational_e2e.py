import sys
import requests
import uuid
import time

# We can query the database directly in the script since it runs inside the container
from config.database import SessionLocal
from models import CartItem, Conversation, Message

TENANT_ID = "e82fe25b-10c8-42c9-91f4-c97264cb09d0"
BASE_URL = "http://localhost:8000"

def check_cart(session_id):
    db = SessionLocal()
    try:
        items = db.query(CartItem).filter(CartItem.session_id == session_id).all()
        print(f"\n--- [DB Check] Carrito para la sesión {session_id} ---")
        if not items:
            print("El carrito está vacío.")
        for item in items:
            print(f"• {item.quantity}x {item.product.name} (${item.product.price})")
        print("----------------------------------------------------\n")
        return items
    finally:
        db.close()

def check_messages(session_id):
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.session_id == session_id).first()
        if not conv:
            print("Conversación no encontrada en BD.")
            return
        messages = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at).all()
        print(f"\n--- [DB Check] Mensajes guardados para la conversación {conv.id} ---")
        for m in messages:
            print(f"[{m.role.upper()}]: {m.content[:80]}...")
        print("----------------------------------------------------\n")
    finally:
        db.close()

def run_e2e():
    session_id = str(uuid.uuid4())
    user_id = "whatsapp_e2e_user_" + str(int(time.time()))
    
    headers = {
        "X-Tenant-ID": TENANT_ID,
        "Content-Type": "application/json"
    }

    # Turnos de conversación
    turns = [
        ("/start", "Turno 1: Inicialización de sesión"),
        ("Hola, buenas. ¿Qué cervezas tienen disponibles y a qué precio?", "Turno 2: Consulta de catálogo"),
        ("Perfecto. Agrega 6 cervezas Corona al carrito porfa.", "Turno 3: Agregar al carrito"),
        ("¿Tienen alguna promo o algo para comer?", "Turno 4: Consulta de cross-selling / snacks"),
        ("Ya, genial. Agrega también 1 Papas Fritas Lays y muestra mi carrito.", "Turno 5: Agregar snack y ver carrito"),
        ("Excelente. Quiero confirmar el pedido.", "Turno 6: Solicitar confirmación"),
        ("Soy Juan Pérez, mi teléfono es +56912345678, y quiero despacho a Av. Vitacura 1234.", "Turno 7: Proporcionar datos de confirmación")
    ]

    print("==============================================================")
    print("INICIANDO TEST CONVERSACIONAL E2E")
    print(f"Session ID: {session_id}")
    print(f"User ID: {user_id}")
    print("==============================================================")

    for message, label in turns:
        print(f"\n🔹 {label}")
        print(f"👤 Usuario: {message}")
        
        payload = {
            "user_id": user_id,
            "platform": "whatsapp",
            "message": message,
            "session_id": session_id
        }

        # Medir latencia
        start_time = time.time()
        try:
            response = requests.post(f"{BASE_URL}/chat", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"❌ Error al enviar mensaje: {e}")
            sys.exit(1)
        
        latency = time.time() - start_time
        print(f"🤖 Asistente (Latencia: {latency:.2f}s, Estado: {data.get('state')}, Versión: {data.get('version')}):")
        print(f"   {data.get('response')}")

        # Realizar verificaciones en la base de datos en puntos clave
        if message == "Perfecto. Agrega 6 cervezas Corona al carrito porfa.":
            # Esperar un momento a que las tareas en segundo plano guarden los datos
            time.sleep(1)
            items = check_cart(session_id)
            assert len(items) == 1, "Debería haber 1 producto en el carrito."
            assert items[0].quantity == 6, "La cantidad de Cerveza Corona debería ser 6."
            assert "Corona" in items[0].product.name

        elif message == "Ya, genial. Agrega también 1 Papas Fritas Lays y muestra mi carrito.":
            time.sleep(1)
            items = check_cart(session_id)
            assert len(items) == 2, "Debería haber 2 productos en el carrito."

        elif "despacho" in message:
            time.sleep(1)
            items = check_cart(session_id)
            assert len(items) == 0, "El carrito debería estar vacío tras confirmar el pedido."
            check_messages(session_id)

    print("\n==============================================================")
    print("🎉 ¡TEST CONVERSACIONAL E2E COMPLETADO CON ÉXITO!")
    print("==============================================================")

if __name__ == "__main__":
    run_e2e()
