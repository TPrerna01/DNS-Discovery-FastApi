import pytest
from pydantic import ValidationError

from app.domains.dto.domain_schemas import DomainCreateSchema


def test_domain_normalized_to_lowercase():
    d = DomainCreateSchema(domain="Example.COM")
    assert d.domain == "example.com"


def test_invalid_domain_without_dot_rejected():
    with pytest.raises(ValidationError):
        DomainCreateSchema(domain="notadomain")


def test_invalid_domain_with_leading_hyphen_rejected():
    with pytest.raises(ValidationError):
        DomainCreateSchema(domain="-example.com")
