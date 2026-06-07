from __future__ import annotations

import uuid
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from services.chat_service import ChatService
from services.spell_corrector import BotilleriaSpellCorrector, KBSpellCorrector
from controllers.chat_controller import chat
from dtos.request import ChatRequest
from exceptions.llm_exceptions import LLMProviderError


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_tenant():
    tenant = MagicMock()
    tenant.id = uuid.uuid4()
    tenant.slug = "test_tenant"
    return tenant


@pytest.fixture
def mock_llm_service():
    llm = MagicMock()
    llm.run_chat = AsyncMock(return_value="Respuesta normal")
    return llm


@pytest.fixture
def mock_user_service():
    with patch("services.chat_service.UserService") as mock:
        user_mock = MagicMock()
        user_mock.id = uuid.uuid4()
        mock.return_value.get_or_create.return_value = user_mock
        yield mock


@pytest.fixture
def mock_conversation_service():
    with patch("services.chat_service.ConversationService") as mock:
        conv_mock = MagicMock()
        conv_mock.id = 1
        conv_mock.state = "NUEVO"
        conv_mock.version = 1
        mock.return_value.get_by_session_id.return_value = conv_mock
        yield mock


@pytest.mark.asyncio
async def test_saludo_basico(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe responder a saludos en lenguaje natural."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Hola, buenas tardes!",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_saludo_coloquial_chela(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe entender jerga chilena como 'chela'."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Wena, tienen chelas?",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_saludo_coloquial_copete(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe entender 'copete' como referencia a bebidas alcohólicas."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Qué copete tienen?",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_consulta_horario_atencion(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe responder a consultas de horario en lenguaje natural."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="A qué hora cierran hoy?",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_consulta_horario_domingo(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe responder a consultas de horario para día específico."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Los domingos atienden?",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_consulta_direccion(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe responder a consultas de ubicación."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Dónde quedan?",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_consulta_telefono(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe responder a consultas de contacto."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Me pasas el número de teléfono?",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_compra_producto_simple(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe procesar intención de compra directa."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Quiero comprar una cerveza Corona",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_compra_con_cantidad(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe procesar compras con cantidad específica."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Agrega 3 piscos sour",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_compra_multiple_productos(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe procesar compras de múltiples productos en una conversación."""
    chat_svc = ChatService(mock_db, mock_llm_service)

    session_id = str(uuid.uuid4())

    _, r1, _, _ = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Dame una cerveza Kunstmann",
        session_id=session_id,
    )
    assert r1 == "Respuesta normal"

    _, r2, _, _ = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Agrega un vino tinto también",
        session_id=session_id,
    )
    assert r2 == "Respuesta normal"

    _, r3, _, _ = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Y necesito papas fritas",
        session_id=session_id,
    )
    assert r3 == "Respuesta normal"


@pytest.mark.asyncio
async def test_ver_carrito(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe mostrar el contenido del carrito."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Qué tengo en el carro?",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_consulta_stock(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe responder a consultas de stock."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Tienen pisco Control?",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_consulta_precio(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe responder a consultas de precio."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Cuánto vale el whisky Johnnie Walker?",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_ver_catalogo(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe mostrar el catálogo de productos."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Muéstrame el catálogo",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_cancelar_compra(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe permitir cancelar una compra."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Quiero cancelar mi pedido",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_vaciar_carrito(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe permitir vaciar el carrito."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Vacía mi carro por favor",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_cancelar_con_insulto(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe mantener la compostura ante insultos."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Este sistema es una mierda, quiero cancelar todo",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_insulto_directo(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema no debe responder con agresividad ante insultos directos."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Eres un inútil, contesta algo útil",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_lenguaje_grosero(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe manejar lenguaje soez sin escalar."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="CTM, llevo horas esperando, weón!",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_spam_caracteres(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe manejar mensajes con spam de caracteres."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="AAAAAAAAAAA AHHHHHHH AAAAAAAAAAAA",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_mensaje_vacio(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe manejar mensajes vacíos o de solo espacios."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="   ",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_mensaje_solo_emojis(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe manejar mensajes compuestos solo de emojis."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="🍺🍷🥃",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_cambio_direccion(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe manejar cambios de dirección en un pedido."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Cambié de dirección, ahora es Av. Siempre Viva 123",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_cambio_producto(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe manejar cambios de producto en el pedido."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="En vez de la corona, quiero una heineken",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_cambio_cantidad(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe manejar cambios de cantidad en el pedido."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Agrega 2 más de las mismas",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_consulta_delivery(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe responder a consultas sobre delivery."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Hacen delivery? Cuánto cobran?",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_consulta_metodos_pago(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe responder a consultas sobre métodos de pago."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Aceptan tarjeta de crédito?",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_contactar_humano(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe transferir a un humano cuando el usuario lo solicite."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Quiero hablar con un humano",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_consulta_promociones(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe responder a consultas sobre promociones."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Tienen alguna promo?",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_devolucion_producto(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe manejar solicitudes de devolución."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Compré una cerveza mala, quiero devolverla",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_reclamo(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe manejar reclamos de clientes."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Llevo 2 horas esperando mi pedido, quiero hacer un reclamo",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_consulta_producto_con_error_tipeo(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe entender productos aunque tengan errores de tipeo."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Tienen sirveza artesanal?",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_mensaje_mayusculas(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe manejar mensajes en mayúsculas sostenidas."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="QUIERO COMPRAR UNA CERVEZA AHORA",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_mensaje_sin_acentos(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe entender mensajes sin acentos."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Una cerveza por favor, tengo toda la sed",
        session_id=str(uuid.uuid4()),
    )
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_conversacion_compra_completa(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe manejar un flujo completo de compra."""
    chat_svc = ChatService(mock_db, mock_llm_service)
    session_id = str(uuid.uuid4())

    _, r1, _, _ = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Hola, quiero comprar algo",
        session_id=session_id,
    )
    assert r1 == "Respuesta normal"

    _, r2, _, _ = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Tienen cerveza artesanal?",
        session_id=session_id,
    )
    assert r2 == "Respuesta normal"

    _, r3, _, _ = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Agrega 2 Kunstmann Torobayo",
        session_id=session_id,
    )
    assert r3 == "Respuesta normal"

    _, r4, _, _ = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user1",
        platform="whatsapp",
        message="Cuánto es el total?",
        session_id=session_id,
    )
    assert r4 == "Respuesta normal"


@pytest.mark.asyncio
async def test_estado_esperando_humano(
    mock_db,
    mock_tenant,
    mock_llm_service,
    mock_user_service,
):
    """Cuando el estado es ESPERANDO_HUMANO, el sistema debe responder acorde."""
    conv_mock = MagicMock()
    conv_mock.id = 1
    conv_mock.state = "ESPERANDO_HUMANO"
    conv_mock.version = 1

    with patch("services.chat_service.ConversationService") as conv_svc:
        conv_svc.return_value.get_by_session_id.return_value = conv_mock
        chat_svc = ChatService(mock_db, mock_llm_service)

        session_id, response, version, state = await chat_svc.process_message(
            tenant=mock_tenant,
            user_id="user1",
            platform="whatsapp",
            message="Hola?",
            session_id=str(uuid.uuid4()),
        )
        assert "humano" in response.lower()
        assert "espera" in response.lower()
        assert state == "ESPERANDO_HUMANO"


@pytest.mark.asyncio
async def test_estado_checkout_bloqueado(
    mock_db,
    mock_tenant,
    mock_llm_service,
    mock_user_service,
):
    """Cuando el estado es CHECKOUT_BLOQUEADO, el sistema debe responder acorde."""
    conv_mock = MagicMock()
    conv_mock.id = 1
    conv_mock.state = "CHECKOUT_BLOQUEADO"
    conv_mock.version = 1

    with patch("services.chat_service.ConversationService") as conv_svc:
        conv_svc.return_value.get_by_session_id.return_value = conv_mock
        chat_svc = ChatService(mock_db, mock_llm_service)

        session_id, response, version, state = await chat_svc.process_message(
            tenant=mock_tenant,
            user_id="user1",
            platform="whatsapp",
            message="Dónde está mi pedido?",
            session_id=str(uuid.uuid4()),
        )
        assert "pago" in response.lower()
        assert state == "CHECKOUT_BLOQUEADO"


@pytest.mark.asyncio
async def test_ghost_click_version_mismatch(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe rechazar ghost clicks con versión desactualizada."""
    conv_mock = MagicMock()
    conv_mock.id = 1
    conv_mock.state = "NUEVO"
    conv_mock.version = 5

    with patch("services.chat_service.ConversationService") as conv_svc:
        conv_svc.return_value.get_by_session_id.return_value = conv_mock
        chat_svc = ChatService(mock_db, mock_llm_service)

        session_id, response, version, state = await chat_svc.process_message(
            tenant=mock_tenant,
            user_id="user1",
            platform="whatsapp",
            message="v3:COMPRAR",
            session_id=str(uuid.uuid4()),
        )
        assert "expi" in response.lower() or "caduc" in response.lower()


@pytest.mark.asyncio
async def test_ghost_click_version_match(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El sistema debe aceptar clicks con versión correcta."""
    conv_mock = MagicMock()
    conv_mock.id = 1
    conv_mock.state = "NUEVO"
    conv_mock.version = 5

    with patch("services.chat_service.ConversationService") as conv_svc:
        conv_svc.return_value.get_by_session_id.return_value = conv_mock
        chat_svc = ChatService(mock_db, mock_llm_service)

        session_id, response, version, state = await chat_svc.process_message(
            tenant=mock_tenant,
            user_id="user1",
            platform="whatsapp",
            message="v5:COMPRAR",
            session_id=str(uuid.uuid4()),
        )
        assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_error_llm_fallback(
    mock_db,
    mock_tenant,
):
    """El controller debe devolver fallback empático cuando el LLM falla."""
    req = ChatRequest(
        user_id="user1",
        platform="whatsapp",
        message="Hola",
        session_id=str(uuid.uuid4()),
    )
    mock_llm = MagicMock()
    mock_llm.run_chat = AsyncMock(side_effect=LLMProviderError("Error de conexión"))

    with patch(
        "controllers.chat_controller.resolve_tenant_from_request",
        new_callable=AsyncMock,
    ) as resolve:
        resolve.return_value = mock_tenant
        with patch("controllers.chat_controller.KBService"):
            with patch("controllers.chat_controller.RAGContextBuilder") as rag:
                rag.return_value.build_context = AsyncMock(return_value=None)
                with patch("services.chat_service.UserService"):
                    with patch("services.chat_service.ConversationService"):
                        response = await chat(
                            request=req,
                            background_tasks=MagicMock(),
                            db=mock_db,
                            llm=mock_llm,
                            fastapi_request=MagicMock(),
                        )
                        assert "revisando la bodega" in response.response


class TestBotilleriaSpellCorrector:
    def test_correccion_cerveza(self):
        assert BotilleriaSpellCorrector.correct("cerveza") == "Cervezas"

    def test_correccion_chela(self):
        assert BotilleriaSpellCorrector.correct("chela") == "Cervezas"

    def test_correccion_piscos(self):
        assert BotilleriaSpellCorrector.correct("piscos") == "Destilados"

    def test_correccion_tinto(self):
        assert BotilleriaSpellCorrector.correct("tinto") == "Vinos"

    def test_correccion_snack(self):
        assert BotilleriaSpellCorrector.correct("snack") == "Snacks"

    def test_correccion_bebida(self):
        assert BotilleriaSpellCorrector.correct("bebida") == "Bebidas"

    def test_correccion_texto_vacio(self):
        assert BotilleriaSpellCorrector.correct("") == ""

    def test_correccion_sin_match(self):
        result = BotilleriaSpellCorrector.correct("algo raro")
        assert result is not None


class TestKBSpellCorrector:
    def test_correccion_envio(self):
        assert KBSpellCorrector.correct("envio") == "Delivery"

    def test_correccion_horario(self):
        assert KBSpellCorrector.correct("horario") == "Horarios"

    def test_correccion_pago(self):
        assert KBSpellCorrector.correct("pago") == "Metodos de Pago"

    def test_correccion_direccion(self):
        assert KBSpellCorrector.correct("direccion") == "Ubicacion"

    def test_correccion_devolucion(self):
        assert KBSpellCorrector.correct("devolucion") == "Devoluciones"

    def test_correccion_reclamo(self):
        assert KBSpellCorrector.correct("reclamo") == "Reclamos"

    def test_correccion_queja(self):
        assert KBSpellCorrector.correct("queja") == "Reclamos"

    def test_correccion_promo(self):
        assert KBSpellCorrector.correct("promo") == "Precios y Ofertas"
