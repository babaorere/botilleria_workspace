import uuid
import pytest
from unittest.mock import MagicMock, patch
from models.conversation import Conversation
from services.chat_service import ChatService


def test_conversation_state_transitions():
    """Verify that all expanded state transitions are allowed and valid."""
    conv = Conversation(state="CHAT_LIBRE")
    assert conv.state == "CHAT_LIBRE"

    # CHAT_LIBRE -> ESPERANDO_HUMANO
    conv.transition_to("ESPERANDO_HUMANO")
    assert conv.state == "ESPERANDO_HUMANO"
    assert conv.version == 1

    # ESPERANDO_HUMANO -> HUMANO_ATENDIENDO
    conv.transition_to("HUMANO_ATENDIENDO")
    assert conv.state == "HUMANO_ATENDIENDO"
    assert conv.version == 2

    # HUMANO_ATENDIENDO -> POSPUESTA
    conv.transition_to("POSPUESTA")
    assert conv.state == "POSPUESTA"

    # POSPUESTA -> CANCELADA
    conv.transition_to("CANCELADA")
    assert conv.state == "CANCELADA"

    # CANCELADA -> ESPERANDO_HUMANO
    conv.transition_to("ESPERANDO_HUMANO")
    assert conv.state == "ESPERANDO_HUMANO"

    # ESPERANDO_HUMANO -> CHAT_LIBRE
    conv.transition_to("CHAT_LIBRE")
    assert conv.state == "CHAT_LIBRE"

    # Invalid transition: CHAT_LIBRE directly to HUMANO_ATENDIENDO should raise ValueError
    with pytest.raises(ValueError):
        conv.transition_to("HUMANO_ATENDIENDO")


@pytest.mark.asyncio
async def test_chat_service_suppresses_llm_on_human_states():
    """Verify that ChatService returns the correct placeholders and suppresses the LLM in human-agent states."""
    mock_db = MagicMock()
    mock_llm = MagicMock()

    # Setup conversation mock returned by ConversationService
    mock_conv = MagicMock()
    mock_conv.id = 1
    mock_conv.session_id = "test_sess"
    mock_conv.version = 5

    mock_tenant = MagicMock()
    mock_tenant.id = uuid.uuid4()

    chat_svc = ChatService(mock_db, mock_llm)

    with (
        patch("services.chat_service.UserService"),
        patch("services.chat_service.ConversationService") as mock_conv_svc_class,
    ):
        mock_conv_svc = mock_conv_svc_class.return_value
        mock_conv_svc.get_by_session_id.return_value = mock_conv

        # Test ESPERANDO_HUMANO
        mock_conv.state = "ESPERANDO_HUMANO"
        _, resp, _, _ = await chat_svc.process_message(
            tenant=mock_tenant,
            user_id="u123",
            platform="whatsapp",
            message="Hola",
            session_id="test_sess",
            rag_context=None,
        )
        assert "esperando a que un humano" in resp
        mock_llm.run_chat.assert_not_called()

        # Test HUMANO_ATENDIENDO
        mock_conv.state = "HUMANO_ATENDIENDO"
        _, resp, _, _ = await chat_svc.process_message(
            tenant=mock_tenant,
            user_id="u123",
            platform="whatsapp",
            message="Hola",
            session_id="test_sess",
            rag_context=None,
        )
        assert "agente humano te está atendiendo" in resp
        mock_llm.run_chat.assert_not_called()

        # Test POSPUESTA
        mock_conv.state = "POSPUESTA"
        _, resp, _, _ = await chat_svc.process_message(
            tenant=mock_tenant,
            user_id="u123",
            platform="whatsapp",
            message="Hola",
            session_id="test_sess",
            rag_context=None,
        )
        assert "solicitud de atención humana ha sido pospuesta" in resp
        mock_llm.run_chat.assert_not_called()
