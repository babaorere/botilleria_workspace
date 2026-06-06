import uuid
import pytest
from unittest.mock import MagicMock
from services.spell_corrector import BotilleriaSpellCorrector
from services.category_service import CategoryService
from models.category import Category


def test_spell_corrector_exact_matches():
    # Test standard categories
    assert BotilleriaSpellCorrector.correct("Cervezas") == "Cervezas"
    assert BotilleriaSpellCorrector.correct("cervezas") == "Cervezas"
    assert BotilleriaSpellCorrector.correct("Vinos") == "Vinos"
    assert BotilleriaSpellCorrector.correct("vinos") == "Vinos"


def test_spell_corrector_typo_matches():
    # Test common typos
    assert BotilleriaSpellCorrector.correct("serbesas") == "Cervezas"
    assert BotilleriaSpellCorrector.correct("binos") == "Vinos"
    assert BotilleriaSpellCorrector.correct("chela") == "Cervezas"
    assert BotilleriaSpellCorrector.correct("piscos") == "Destilados"
    assert BotilleriaSpellCorrector.correct("esnaks") == "Snacks"
    assert BotilleriaSpellCorrector.correct("likor") == "Licores"


def test_spell_corrector_unmatched():
    # Unmatched inputs should be capitalized/cleaned
    assert BotilleriaSpellCorrector.correct("otra cosa") == "Otra Cosa"
    assert BotilleriaSpellCorrector.correct("  pisco sour  ") == "Pisco Sour"


def test_category_service_create():
    mock_db = MagicMock()
    tenant_id = uuid.uuid4()
    
    # Mocking the repository methods inside CategoryService
    # We will mock the save method of CategoryRepository to return a category object
    service = CategoryService(mock_db, tenant_id)
    
    # Mock repo.find_by_name_and_tenant to return None (category doesn't exist yet)
    service.repo.find_by_name_and_tenant = MagicMock(return_value=None)
    service.repo.save = MagicMock(side_effect=lambda x: x)
    
    new_cat = service.create_category("serbesas", "Mis cervezas ricas")
    
    assert new_cat.name == "Cervezas" # corrected
    assert new_cat.description == "Mis cervezas ricas"
    assert new_cat.tenant_id == tenant_id
    service.repo.save.assert_called_once()


def test_category_service_protect_general():
    mock_db = MagicMock()
    tenant_id = uuid.uuid4()
    service = CategoryService(mock_db, tenant_id)

    # Mock finding a category with name "General"
    cat_general = Category(id=uuid.uuid4(), tenant_id=tenant_id, name="General", description="System")
    service.repo.find_by_id_and_tenant = MagicMock(return_value=cat_general)

    with pytest.raises(ValueError, match="no se puede editar"):
        service.update_category(cat_general.id, name="Nueva")

    with pytest.raises(ValueError, match="no se puede eliminar"):
        service.delete_category(cat_general.id)


def test_category_service_rename_to_general():
    mock_db = MagicMock()
    tenant_id = uuid.uuid4()
    service = CategoryService(mock_db, tenant_id)

    # Mock finding a non-General category
    cat_other = Category(id=uuid.uuid4(), tenant_id=tenant_id, name="Vinos", description="System")
    service.repo.find_by_id_and_tenant = MagicMock(return_value=cat_other)

    with pytest.raises(ValueError, match="No se puede renombrar una categoría a 'General'"):
        service.update_category(cat_other.id, name="General")
