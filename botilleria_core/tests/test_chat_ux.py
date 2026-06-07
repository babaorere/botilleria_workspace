import uuid
from unittest.mock import MagicMock, AsyncMock, patch
import pytest

from dtos.request import ChatRequest
from exceptions.llm_exceptions import LLMProviderError
from services.chat_service import ChatService
from controllers.chat_controller import chat, chat_stream


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
        mock.return_value.get_by_session_id.return_value = None
        yield mock


@pytest.mark.asyncio
async def test_chat_service_reset_session_on_start_command(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """El comando /start debe ignorar el session_id provisto y generar uno nuevo."""
    chat_svc = ChatService(mock_db, mock_llm_service)

    original_session_id = str(uuid.uuid4())

    new_session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user123",
        platform="telegram",
        message="/start",
        session_id=original_session_id,
        rag_context=None,
    )

    assert new_session_id != original_session_id
    assert response == "Respuesta normal"


@pytest.mark.asyncio
async def test_chat_service_keeps_session_on_normal_message(
    mock_db, mock_tenant, mock_llm_service, mock_user_service, mock_conversation_service
):
    """Mensajes normales deben respetar el session_id provisto."""
    chat_svc = ChatService(mock_db, mock_llm_service)

    original_session_id = str(uuid.uuid4())

    returned_session_id, response, version, state = await chat_svc.process_message(
        tenant=mock_tenant,
        user_id="user123",
        platform="telegram",
        message="Hola",
        session_id=original_session_id,
        rag_context=None,
    )

    assert returned_session_id == original_session_id


@pytest.mark.asyncio
async def test_chat_controller_empathetic_error_fallback(mock_db, mock_tenant):
    """El controlador de chat debe devolver un mensaje empático al capturar LLMProviderError."""
    req = ChatRequest(
        user_id="user123",
        platform="telegram",
        message="Hola",
        session_id=str(uuid.uuid4()),
    )

    mock_llm = MagicMock()
    mock_llm.run_chat = AsyncMock(side_effect=LLMProviderError("Timeout"))

    fastapi_req = MagicMock()

    with patch(
        "controllers.chat_controller.resolve_tenant_from_request",
        new_callable=AsyncMock,
    ) as resolve_mock:
        resolve_mock.return_value = mock_tenant
        with patch("controllers.chat_controller.KBService"):
            with patch("controllers.chat_controller.RAGContextBuilder") as rag_mock:
                rag_mock.return_value.build_context = AsyncMock(return_value=None)

                with patch("services.chat_service.UserService"):
                    with patch("services.chat_service.ConversationService"):
                        response = await chat(
                            request=req,
                            background_tasks=MagicMock(),
                            db=mock_db,
                            llm=mock_llm,
                            fastapi_request=fastapi_req,
                        )

                        assert (
                            response.response
                            == "Disculpa, en este momento estoy revisando la bodega y no puedo responder. ¿Podrías intentar en unos minutos?"
                        )
                        assert response.session_id == req.session_id


@pytest.mark.asyncio
async def test_chat_stream_controller_empathetic_error_fallback(mock_db, mock_tenant):
    """El controlador de chat stream debe emitir un chunk empático al capturar LLMProviderError."""
    req = ChatRequest(
        user_id="user123",
        platform="telegram",
        message="Hola",
        session_id=str(uuid.uuid4()),
    )

    async def failing_stream_generator():
        raise LLMProviderError("Timeout")
        yield "Never reached"

    mock_chat_svc = MagicMock()
    mock_chat_svc.process_message_stream = AsyncMock(
        return_value=(req.session_id, failing_stream_generator(), 1, "NUEVO")
    )

    fastapi_req = MagicMock()

    with patch(
        "controllers.chat_controller.resolve_tenant_from_request",
        new_callable=AsyncMock,
    ) as resolve_mock:
        resolve_mock.return_value = mock_tenant
        with patch("controllers.chat_controller.KBService"):
            with patch("controllers.chat_controller.RAGContextBuilder") as rag_mock:
                rag_mock.return_value.build_context = AsyncMock(return_value=None)
                with patch(
                    "controllers.chat_controller.ChatService",
                    return_value=mock_chat_svc,
                ):
                    response = await chat_stream(
                        request=req,
                        background_tasks=MagicMock(),
                        db=mock_db,
                        llm=MagicMock(),
                        fastapi_request=fastapi_req,
                    )

                    # Consumir el generador
                    generator = response.body_iterator

                    chunks = []
                    async for event in generator:
                        if isinstance(event, dict):
                            chunks.append(event)

                    assert len(chunks) == 2
                    assert chunks[0]["event"] == "chunk"
                    assert "revisando la bodega" in chunks[0]["data"]
                    assert chunks[1]["event"] == "done"
                    assert chunks[1]["data"] == req.session_id
