import os
import sys
import logging
from datetime import datetime, timedelta

# Add parent directory to path to allow importing from config/models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import SessionLocal
from models.cart_item import CartItem
from models.conversation import Conversation
from models.tenant import Tenant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_abandoned_carts(minutes_threshold: int = 30):
    """
    Busca carritos que han estado inactivos por más del tiempo especificado
    y que no han sido confirmados/vaciados.
    """
    logger.info("Iniciando escaneo de carritos abandonados (más de %d mins)...", minutes_threshold)
    from datetime import timezone
    threshold_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=minutes_threshold)
    
    
    with SessionLocal() as db:
        # Buscamos todos los cart_items que no se han actualizado
        stale_items = db.query(CartItem).filter(
            CartItem.updated_at < threshold_time
        ).all()
        
        if not stale_items:
            logger.info("No se encontraron carritos abandonados en este momento.")
            return
            
        # Agrupamos por session_id (cada session representa un usuario en un canal)
        carts_by_session = {}
        for item in stale_items:
            if item.session_id not in carts_by_session:
                carts_by_session[item.session_id] = {
                    "tenant_id": str(item.tenant_id),
                    "items": [],
                    "last_updated": item.updated_at
                }
            carts_by_session[item.session_id]["items"].append(item)
            
            # Mantenemos el updated_at más reciente de los items del carrito
            if item.updated_at > carts_by_session[item.session_id]["last_updated"]:
                carts_by_session[item.session_id]["last_updated"] = item.updated_at
                
        for session_id, data in carts_by_session.items():
            tenant_id = data["tenant_id"]
            items_count = sum(i.quantity for i in data["items"])
            
            logger.info(
                "[RECUPERACIÓN] El usuario de la sesión '%s' abandonó su carrito hace %s mins con %d productos.",
                session_id, 
                int((datetime.now(timezone.utc).replace(tzinfo=None) - data["last_updated"]).total_seconds() / 60),
                items_count
            )
            
            # Buscar la configuración del tenant para obtener el token de Telegram
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if tenant:
                bot_token = tenant.config.get("telegram_bot_token") or os.getenv("TELEGRAM_BOT_TOKEN")
                if bot_token:
                    # session_id típicamente corresponde al chat_id de Telegram en la configuración actual
                    message = (
                        "👀 *¡Hola! ¿Te dio sed?*\n\n"
                        f"Vi que dejaste {items_count} producto(s) pendiente(s) en tu carrito de {tenant.name}. "
                        "¿Te gustaría retomar tu pedido o necesitas ayuda con algo?"
                    )
                    from services.telegram_service import send_telegram_message
                    success = send_telegram_message(bot_token, session_id, message)
                    if success:
                        logger.info("Mensaje de recuperación enviado a %s exitosamente.", session_id)
                    else:
                        logger.error("Fallo al enviar mensaje de recuperación a %s.", session_id)
                else:
                    logger.warning("No hay token de Telegram configurado para el tenant %s.", tenant.name)

if __name__ == "__main__":
    check_abandoned_carts()
