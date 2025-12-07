# tests/conftest.py
from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest

def make_chain(data=None, exc: Exception | None = None):
    """Mock цепочки .table(...).select(...).eq(...).insert(...).execute()"""
    chain = MagicMock()
    # методы fluent API, которые часто используются — все возвращают тот же chain
    for method in ("select", "eq", "limit", "insert", "update", "delete", "order", "returning"):
        getattr(chain, method).return_value = chain

    if exc:
        chain.execute.side_effect = exc
    else:
        chain.execute.return_value = SimpleNamespace(data=data)

    return chain

@pytest.fixture
def chain_factory():
    """В тестах: client.table.return_value = chain_factory([...])"""
    return make_chain
