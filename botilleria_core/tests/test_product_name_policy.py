import uuid
import pytest
from services.product_service import (
    get_levenshtein_distance,
    parse_presentation,
    check_product_name_policy,
)
from models.product import Product


def test_get_levenshtein_distance():
    assert get_levenshtein_distance("cristal", "cristal") == 0
    assert get_levenshtein_distance("cristal", "cristal1") == 1
    assert get_levenshtein_distance("cristal", "cristall") == 1
    assert get_levenshtein_distance("cristal", "cristal_") == 1
    assert get_levenshtein_distance("cristal", "pisco") == 5


def test_parse_presentation():
    assert parse_presentation("Cristal 500cc") == "500cc"
    assert (
        parse_presentation("Cristal 1.2L Botella Retornable")
        == "1.2l botella retornable"
    )
    assert parse_presentation("Pisco Mistral 35º 750ml") == "750ml"
    assert parse_presentation("Corona Lata") == "lata"
    assert parse_presentation("Escudo") is None


def test_check_product_name_policy_exact_duplicate():
    tenant_id = uuid.uuid4()
    p1 = Product(id=uuid.uuid4(), tenant_id=tenant_id, name="Cerveza Cristal")
    existing = [p1]

    with pytest.raises(ValueError, match="Ya existe un producto con el nombre exacto"):
        check_product_name_policy("Cerveza Cristal", existing)

    with pytest.raises(ValueError, match="Ya existe un producto con el nombre exacto"):
        check_product_name_policy("  cerveza cristal  ", existing)


def test_check_product_name_policy_similar_without_presentation():
    tenant_id = uuid.uuid4()
    # If one of them has no presentation, they are considered ambiguous
    p1 = Product(id=uuid.uuid4(), tenant_id=tenant_id, name="Cerveza Cristal")
    existing = [p1]

    with pytest.raises(ValueError, match="es ambiguo con el producto existente"):
        check_product_name_policy("Cerveza Cristal 500cc", existing)

    with pytest.raises(ValueError, match="es ambiguo con el producto existente"):
        check_product_name_policy("Cerveza Cristal Lata", existing)


def test_check_product_name_policy_different_presentations_allowed():
    tenant_id = uuid.uuid4()
    # If both specify different presentations, they are allowed
    p1 = Product(id=uuid.uuid4(), tenant_id=tenant_id, name="Cerveza Cristal 500cc")
    existing = [p1]

    # Different presentation should pass successfully (no exception)
    check_product_name_policy("Cerveza Cristal 1L", existing)
    check_product_name_policy("Cerveza Cristal Lata", existing)


def test_check_product_name_policy_same_presentation_blocked():
    tenant_id = uuid.uuid4()
    p1 = Product(id=uuid.uuid4(), tenant_id=tenant_id, name="Cerveza Cristal 500cc")
    existing = [p1]

    # Exact duplicates are blocked by Rule 1
    with pytest.raises(ValueError, match="Ya existe un producto con el nombre exacto"):
        check_product_name_policy("Cerveza Cristal 500cc", existing)

    # Different string representation but same base name and same presentation are blocked by Rule 2
    with pytest.raises(ValueError, match="tiene el mismo formato/presentación"):
        check_product_name_policy("Cerveza Cristal - 500cc", existing)


def test_tenant_slug_policy():
    from unittest.mock import MagicMock
    from services.tenant_service import TenantService
    from models.tenant import Tenant

    mock_db = MagicMock()
    service = TenantService(mock_db)

    # Setup some existing tenants
    t1_id = uuid.uuid4()
    t2_id = uuid.uuid4()
    t1 = Tenant(id=t1_id, slug="cristal", name="Cristal Store")
    t2 = Tenant(id=t2_id, slug="escudo", name="Escudo Store")

    # Mock tenant repository methods
    service.tenant_repo.find_by_slug = MagicMock(
        side_effect=lambda s: t1 if s == "cristal" else (t2 if s == "escudo" else None)
    )
    service.tenant_repo.find_all = MagicMock(return_value=[t1, t2])

    # Exact duplicate slug should raise ValueError
    with pytest.raises(ValueError, match="Ya existe un tenant con el slug"):
        service.validate_slug("cristal")

    with pytest.raises(ValueError, match="Ya existe un tenant con el slug"):
        service.validate_slug("  CRISTAL  ")

    # Extremely similar slug (Levenshtein distance <= 1) should raise ValueError
    with pytest.raises(ValueError, match="es extremadamente similar al slug existente"):
        service.validate_slug("cristal1")

    with pytest.raises(ValueError, match="es extremadamente similar al slug existente"):
        service.validate_slug("cristal_")

    # Different slug should pass
    assert service.validate_slug("corona") == "corona"

    # Self slug on update (excluding own id) should pass
    assert service.validate_slug("cristal", exclude_id=t1_id) == "cristal"
