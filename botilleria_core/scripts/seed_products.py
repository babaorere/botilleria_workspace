# ruff: noqa: E402, F401
from __future__ import annotations

import sys
import os
import logging

# Configurar el logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agregar la raíz del proyecto al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.database import SessionLocal, set_tenant_context, _sync_engine, Base
# Importar todos los modelos para registrarlos en la metadata de SQLAlchemy
from models import Product, Tenant, Category, Conversation, User, Message, KnowledgeBase, CartItem, KBCategory


def seed() -> None:
    # 1. Asegurar que las tablas existan en la base de datos
    logger.info("Creando tablas si no existen...")
    Base.metadata.create_all(bind=_sync_engine)
    logger.info("Tablas verificadas.")

    db = SessionLocal()
    try:
        # 2. Obtener o crear tenant por defecto
        tenant = db.query(Tenant).filter(Tenant.slug == "el_buen_trago").first()
        if not tenant:
            logger.info("Creando tenant por defecto 'el_buen_trago'...")
            tenant = Tenant(
                slug="el_buen_trago",
                name="Botillería El Buen Trago",
                status="active",
                email="contacto@elbuentrago.cl",
                phone="+56 9 1234 5678",
                address="Av. Providencia 1234",
                city="Santiago",
                website="https://elbuentrago.cl",
                business_hours={
                    "lunes": {"open": "10:00", "close": "22:00"},
                    "martes": {"open": "10:00", "close": "22:00"},
                    "miercoles": {"open": "10:00", "close": "22:00"},
                    "jueves": {"open": "10:00", "close": "22:00"},
                    "viernes": {"open": "10:00", "close": "22:00"},
                    "sabado": {"open": "10:00", "close": "22:00"},
                    "domingo": {"open": "12:00", "close": "20:00"},
                },
                config={
                    "instruction": (
                        "Eres el asistente virtual de la Botillería El Buen Trago. "
                        "Tu rol es atender consultas de clientes, ayudarlos con pedidos, "
                        "listar categorías de productos, y al final confirmar el pedido "
                        "enviando el resumen a Telegram.\n\n"
                        "REGLAS:\n"
                        "1. Sé amable y cordial en español.\n"
                        "2. Guía al usuario usando categorías o buscando productos si es necesario.\n"
                        "3. Si desean comprar algo, usa el tool de agregar al carrito.\n"
                        "4. Cuando quieran finalizar la compra, pídeles Nombre, Teléfono y método "
                        "de entrega (Retiro o Despacho). Luego llama al tool confirmar_pedido.\n"
                        "5. Nunca inventes información de catálogo o precios."
                    ),
                    "model": "openrouter/nvidia/nemotron-3-super-120b-a12b:free",
                    "api_key": os.getenv("OPENROUTER_API_KEY", ""),
                    "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
                    "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
                },
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
            logger.info("Tenant por defecto creado exitosamente.")

        tenant_id = tenant.id
        set_tenant_context(db, str(tenant_id))

        # Seed categories (always sync the 10 most common categories sorted by name)
        logger.info("Sembrando las 10 categorías principales ordenadas por nombre...")
        db.query(Category).filter(Category.tenant_id == tenant_id).delete(synchronize_session=False)
        db.commit()

        cats = [
            Category(tenant_id=tenant_id, name="Bebidas", description="Gaseosas, jugos y aguas mineralizadas"),
            Category(tenant_id=tenant_id, name="Cervezas", description="Cervezas nacionales, importadas y artesanales"),
            Category(tenant_id=tenant_id, name="Coctelería", description="Mixers, tónicas y bebidas preparadas"),
            Category(tenant_id=tenant_id, name="Destilados", description="Pisco, ron, gin, vodka y whisky"),
            Category(tenant_id=tenant_id, name="Espumantes", description="Champaña, sparkling y espumantes"),
            Category(tenant_id=tenant_id, name="General", description="Categoría general por defecto"),
            Category(tenant_id=tenant_id, name="Hielo", description="Hielo en cubos y hielo picado"),
            Category(tenant_id=tenant_id, name="Licores", description="Licores dulces, cremas y bajativos"),
            Category(tenant_id=tenant_id, name="Snacks", description="Papas fritas, frutos secos y complementos para picar"),
            Category(tenant_id=tenant_id, name="Tabacos", description="Cigarrillos, tabaco para enrolar y accesorios"),
            Category(tenant_id=tenant_id, name="Vinos", description="Vinos tintos, blancos y rosados")
        ]
        cats.sort(key=lambda c: c.name)
        db.add_all(cats)
        db.commit()
        logger.info("Categorías sembradas exitosamente.")

        # Seed KBCategory (always sync the 11 most common categories sorted by name)
        logger.info("Sembrando las 11 categorías de respuestas ordenadas por nombre...")
        db.query(KBCategory).filter(KBCategory.tenant_id == tenant_id).delete(synchronize_session=False)
        db.commit()

        kb_cats = [
            KBCategory(tenant_id=tenant_id, name="Contacto", description="Información de contacto, teléfono, correo y redes sociales"),
            KBCategory(tenant_id=tenant_id, name="Delivery", description="Horarios de despacho, zonas de cobertura y costos de envío"),
            KBCategory(tenant_id=tenant_id, name="Devoluciones", description="Políticas de devolución, cambios y garantías de productos"),
            KBCategory(tenant_id=tenant_id, name="Eventos", description="Servicios para fiestas, barriles de cerveza y shoperas"),
            KBCategory(tenant_id=tenant_id, name="General", description="Categoría de respuestas general por defecto"),
            KBCategory(tenant_id=tenant_id, name="Horarios", description="Horarios de atención de la botillería"),
            KBCategory(tenant_id=tenant_id, name="Metodos de Pago", description="Formas de pago aceptadas (efectivo, tarjetas, transferencias)"),
            KBCategory(tenant_id=tenant_id, name="Precios y Ofertas", description="Promociones, descuentos y lista de precios"),
            KBCategory(tenant_id=tenant_id, name="Reclamos", description="Canal para ingresar quejas, reclamos o sugerencias"),
            KBCategory(tenant_id=tenant_id, name="Stock y Pedidos", description="Consulta de stock, pedidos mayoristas y compras"),
            KBCategory(tenant_id=tenant_id, name="Ubicacion", description="Dirección física de la tienda y cómo llegar")
        ]
        kb_cats.sort(key=lambda c: c.name)
        db.add_all(kb_cats)
        db.commit()
        logger.info("Categorías de respuestas sembradas exitosamente.")

        # 3. Verificar si ya existen productos para este tenant
        existing_count = db.query(Product).filter(Product.tenant_id == tenant_id).count()
        if existing_count > 0:
            logger.info("El catálogo ya contiene %s productos. Omitiendo la siembra de datos.", existing_count)
            return

        # 4. Lista de productos realistas
        products = [
            # Cervezas
            Product(
                tenant_id=tenant_id,
                name="Cerveza Corona 355ml",
                category="Cervezas",
                price=1500.00,
                stock=100,
                description="Cerveza rubia tipo Pilsener, importada de México.",
                is_available=True,
            ),
            Product(
                tenant_id=tenant_id,
                name="Cerveza Kunstmann Torobayo 330ml",
                category="Cervezas",
                price=1800.00,
                stock=50,
                description="Cerveza artesanal de Valdivia, tipo Amber Ale.",
                is_available=True,
            ),
            Product(
                tenant_id=tenant_id,
                name="Cerveza Heineken 330ml",
                category="Cervezas",
                price=1300.00,
                stock=80,
                description="Cerveza Lager premium de origen holandés.",
                is_available=True,
            ),
            Product(
                tenant_id=tenant_id,
                name="Cerveza Cristal 350ml (Lata)",
                category="Cervezas",
                price=800.00,
                stock=150,
                description="Cerveza Lager nacional, ligera y refrescante.",
                is_available=True,
            ),
            Product(
                tenant_id=tenant_id,
                name="Cerveza Escudo 350ml (Lata)",
                category="Cervezas",
                price=800.00,
                stock=120,
                description="Cerveza Lager nacional con mayor cuerpo y carácter.",
                is_available=True,
            ),
            # Destilados
            Product(
                tenant_id=tenant_id,
                name="Pisco Alto del Carmen 35° 1L",
                category="Destilados",
                price=7990.00,
                stock=40,
                description="Pisco chileno elaborado con uvas moscatel.",
                is_available=True,
            ),
            Product(
                tenant_id=tenant_id,
                name="Pisco Mistral 35° 750ml",
                category="Destilados",
                price=6990.00,
                stock=45,
                description="Pisco añejado en barricas de roble americano.",
                is_available=True,
            ),
            Product(
                tenant_id=tenant_id,
                name="Whisky Johnnie Walker Red Label 750ml",
                category="Destilados",
                price=14990.00,
                stock=20,
                description="Blended Scotch Whisky de fama mundial, notas especiadas.",
                is_available=True,
            ),
            Product(
                tenant_id=tenant_id,
                name="Ron Pampero Especial 750ml",
                category="Destilados",
                price=8490.00,
                stock=25,
                description="Ron dorado añejo venezolano de sabor suave.",
                is_available=True,
            ),
            Product(
                tenant_id=tenant_id,
                name="Gin Tanqueray 750ml",
                category="Destilados",
                price=18990.00,
                stock=15,
                description="Gin premium estilo London Dry, notas herbáceas y cítricas.",
                is_available=True,
            ),
            # Vinos
            Product(
                tenant_id=tenant_id,
                name="Vino Casillero del Diablo Cabernet Sauvignon 750ml",
                category="Vinos",
                price=5490.00,
                stock=30,
                description="Vino tinto estructurado y aromático, Valle Central.",
                is_available=True,
            ),
            Product(
                tenant_id=tenant_id,
                name="Vino Santa Rita 120 Merlot 750ml",
                category="Vinos",
                price=3990.00,
                stock=35,
                description="Vino tinto joven, suave, frutoso y fácil de beber.",
                is_available=True,
            ),
            Product(
                tenant_id=tenant_id,
                name="Vino Gato Negro Sauvignon Blanc 750ml",
                category="Vinos",
                price=2990.00,
                stock=40,
                description="Vino blanco fresco y joven, notas cítricas.",
                is_available=True,
            ),
            # Bebidas
            Product(
                tenant_id=tenant_id,
                name="Bebida Coca Cola Original 2.5L",
                category="Bebidas",
                price=2200.00,
                stock=60,
                description="Refresco sabor cola original en formato familiar.",
                is_available=True,
            ),
            Product(
                tenant_id=tenant_id,
                name="Bebida Sprite 2.5L",
                category="Bebidas",
                price=2000.00,
                stock=40,
                description="Refresco sabor lima-limón en formato familiar.",
                is_available=True,
            ),
            Product(
                tenant_id=tenant_id,
                name="Bebida Tonica Canada Dry 1.5L",
                category="Bebidas",
                price=1500.00,
                stock=30,
                description="Agua tónica premium, ideal para acompañar con Gin.",
                is_available=True,
            ),
            # Snacks
            Product(
                tenant_id=tenant_id,
                name="Papas Fritas Lays Clasicas 250g",
                category="Snacks",
                price=2500.00,
                stock=40,
                description="Papas fritas saladas crujientes, tamaño familiar.",
                is_available=True,
            ),
            Product(
                tenant_id=tenant_id,
                name="Maní Salado Marco Polo 150g",
                category="Snacks",
                price=1500.00,
                stock=50,
                description="Maní tostado y salado, el acompañamiento perfecto.",
                is_available=True,
            ),
        ]

        db.add_all(products)
        db.commit()
        logger.info(
            "Se sembraron %s productos exitosamente para 'el_buen_trago'.",
            len(products),
        )
    except Exception as e:
        db.rollback()
        logger.error("Error al sembrar los productos: %s", e)
    finally:
        db.close()


if __name__ == "__main__":
    seed()
