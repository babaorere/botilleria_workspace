"""
Tests for keyboard functionality in Sprint 1.
"""
from __future__ import annotations

import sys
import os
# Add the parent directory of the current file to sys.path so we can import botilleria_core
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import pytest
from unittest.mock import Mock

# Mock the telegram imports since we don't need the actual implementation for these tests
sys.modules['telegram'] = Mock()
sys.modules['telegram'].ReplyKeyboardMarkup = Mock
sys.modules['telegram'].KeyboardButton = Mock
sys.modules['telegram'].InlineKeyboardMarkup = Mock
sys.modules['telegram'].InlineKeyboardButton = Mock

# Now we can import from botilleria_core
from botilleria_core.keyboards import (
    get_main_keyboard,
    get_categories_keyboard,
    get_cart_items_keyboard,
    get_order_method_keyboard,
    get_order_confirmation_keyboard,
    get_cart_button_text,
    get_status_button_text
)


def test_get_main_keyboard():
    """Test main keyboard generation."""
    keyboard = get_main_keyboard(tenant_id=1, is_open=True)
    
    assert hasattr(keyboard, 'keyboard')  # ReplyKeyboardMarkup
    assert len(keyboard.keyboard) == 2
    assert len(keyboard.keyboard[0]) == 4  # 4 buttons in first row
    assert len(keyboard.keyboard[1]) == 2  # 2 buttons in second row
    
    # Check button text
    assert keyboard.keyboard[0][0].text == "🔍 Catálogo"
    assert keyboard.keyboard[0][1].text == "🛒 Carro"  # Will be updated with badge
    assert keyboard.keyboard[0][2].text == "📦 Mis Pedidos"
    assert keyboard.keyboard[0][3].text == "👤 Mi Perfil"
    assert keyboard.keyboard[1][0].text == "🟢 ABIERTO"
    assert keyboard.keyboard[1][1].text == "🤝 Humano"


def test_get_main_keyboard_closed():
    """Test main keyboard when closed."""
    keyboard = get_main_keyboard(tenant_id=1, is_open=False)
    assert keyboard.keyboard[1][0].text == "🔴 CERRADO"


def test_get_categories_keyboard():
    """Test categories keyboard generation."""
    categories = ["Cervezas", "Vinos", "Piscos", "Licores"]
    keyboard = get_categories_keyboard(categories)
    
    assert len(keyboard.inline_keyboard) >= 2  # At least 2 rows
    # First row should have 3 buttons
    assert len(keyboard.inline_keyboard[0]) == 3
    assert keyboard.inline_keyboard[0][0].text == "🍺 Cervezas"
    assert keyboard.inline_keyboard[0][1].text == "🍷 Vinos"
    assert keyboard.inline_keyboard[0][2].text == "🥃 Piscos"
    # Second row should have remaining button + "Ver todo"
    assert len(keyboard.inline_keyboard[1]) == 2
    assert keyboard.inline_keyboard[1][0].text == "🍾 Licores"
    assert keyboard.inline_keyboard[1][1].text == "📋 Ver todo"


def test_get_cart_items_keyboard():
    """Test cart items keyboard generation."""
    cart_items = [
        {"product_id": 1, "name": "Cristal 350cc", "quantity": 2, "price": 1200},
        {"product_id": 2, "name": "Kunstmann", "quantity": 1, "price": 2800}
    ]
    keyboard = get_cart_items_keyboard(cart_items)
    
    # Should have 2 item rows + 1 action row
    assert len(keyboard.inline_keyboard) == 3
    
    # First item row
    assert keyboard.inline_keyboard[0][0].text == "• Cristal 350cc..."
    assert keyboard.inline_keyboard[0][1].text == "[−]"
    assert keyboard.inline_keyboard[0][2].text == "2"
    assert keyboard.inline_keyboard[0][3].text == "[+]"
    assert keyboard.inline_keyboard[0][4].text == "[🗑]"
    
    # Action row
    assert keyboard.inline_keyboard[2][0].text == "🗑 Vaciar Carro"
    assert keyboard.inline_keyboard[2][1].text == "🟢 PEDIR AHORA"


def test_get_order_method_keyboard():
    """Test order method keyboard."""
    keyboard = get_order_method_keyboard()
    assert len(keyboard.inline_keyboard) == 1
    assert len(keyboard.inline_keyboard[0]) == 2
    assert "RETIRO" in keyboard.inline_keyboard[0][0].text
    assert "DESPACHO" in keyboard.inline_keyboard[0][1].text


def test_get_order_confirmation_keyboard():
    """Test order confirmation keyboard."""
    keyboard = get_order_confirmation_keyboard()
    assert len(keyboard.inline_keyboard) == 1
    assert len(keyboard.inline_keyboard[0]) == 2
    assert "CONFIRMAR" in keyboard.inline_keyboard[0][0].text
    assert "CANCELAR" in keyboard.inline_keyboard[0][1].text


def test_get_cart_button_text():
    """Test cart button text with badge."""
    assert get_cart_button_text(0) == "🛒 Carro"
    assert get_cart_button_text(3) == "🛒 Carro (3)"
    assert get_cart_button_text(10) == "🛒 Carro (10)"


def test_get_status_button_text():
    """Test status button text."""
    assert get_status_button_text(True) == "🟢 ABIERTO"
    assert get_status_button_text(False) == "🔴 CERRADO"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])