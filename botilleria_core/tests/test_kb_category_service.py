import uuid
import pytest
from unittest.mock import MagicMock
from services.spell_corrector import KBSpellCorrector
from services.kb_category_service import KBCategoryService
from models.kb_category import KBCategory


def test_kb_spell_corrector_exact_matches():
    # Test standard KB categories
    assert KBSpellCorrector.correct("General") == "General"
    assert KBSpellCorrector.correct("general") == "General"
    assert KBSpellCorrector.correct("Delivery") == "Delivery"
    assert KBSpellCorrector.correct("delivery") == "Delivery"


def test_kb_spell_corrector_typo_matches():
    # Test common typos
    assert KBSpellCorrector.correct("envio") == "Delivery"
    assert KBSpellCorrector.correct("despachos") == "Delivery"
    assert KBSpellCorrector.correct("horario") == "Horarios"
    assert KBSpellCorrector.correct("atencion") == "Horarios"
    assert KBSpellCorrector.correct("transferencia") == "Metodos de Pago"
    assert KBSpellCorrector.correct("direccion") == "Ubicacion"
    assert KBSpellCorrector.correct("cambios") == "Devoluciones"
    assert KBSpellCorrector.correct("ofertas") == "Precios y Ofertas"


def test_kb_spell_corrector_unmatched():
    assert KBSpellCorrector.correct("alguna pregunta") == "Alguna Pregunta"
    assert KBSpellCorrector.correct("  otras consultas  ") == "Otras Consultas"


def test_kb_category_service_create():
    mock_db = MagicMock()
    tenant_id = uuid.uuid4()
    
    service = KBCategoryService(mock_db, tenant_id)
    
    service.repo.find_by_name_and_tenant = MagicMock(return_value=None)
    service.repo.save = MagicMock(side_effect=lambda x: x)
    
    new_cat = service.create_category("envios", "Información de despachos")
    
    assert new_cat.name == "Delivery" # corrected
    assert new_cat.description == "Información de despachos"
    assert new_cat.tenant_id == tenant_id
    service.repo.save.assert_called_once()


def test_kb_category_service_protect_general():
    mock_db = MagicMock()
    tenant_id = uuid.uuid4()
    service = KBCategoryService(mock_db, tenant_id)

    cat_general = KBCategory(id=uuid.uuid4(), tenant_id=tenant_id, name="General", description="System")
    service.repo.find_by_id_and_tenant = MagicMock(return_value=cat_general)

    with pytest.raises(ValueError, match="no se puede editar"):
        service.update_category(cat_general.id, name="Nueva")

    with pytest.raises(ValueError, match="no se puede eliminar"):
        service.delete_category(cat_general.id)


def test_kb_category_service_rename_to_general():
    mock_db = MagicMock()
    tenant_id = uuid.uuid4()
    service = KBCategoryService(mock_db, tenant_id)

    cat_other = KBCategory(id=uuid.uuid4(), tenant_id=tenant_id, name="Delivery", description="System")
    service.repo.find_by_id_and_tenant = MagicMock(return_value=cat_other)

    with pytest.raises(ValueError, match="No se puede renombrar una categoría de respuesta a 'General'"):
        service.update_category(cat_other.id, name="General")
