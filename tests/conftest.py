from types import SimpleNamespace
from unittest.mock import MagicMock, AsyncMock
import pytest

def make_chain(data=None, exc: Exception | None = None):
    """Mock цепочки .table(...).select(...).eq(...).insert(...).execute()

    execute() — AsyncMock, чтобы его можно было await'ить в async-тестах.
    """
    chain = MagicMock()
    # методы fluent API — возвращают тот же chain
    for method in ("select", "eq", "limit", "insert", "update", "delete", "order", "returning"):
        getattr(chain, method).return_value = chain

    # Сделать execute awaitable
    if exc:
        chain.execute = AsyncMock(side_effect=exc)
    else:
        chain.execute = AsyncMock(return_value=SimpleNamespace(data=data))

    return chain

@pytest.fixture
def chain_factory():
    """В тестах: client.table.return_value = chain_factory([...])"""
    return make_chain
