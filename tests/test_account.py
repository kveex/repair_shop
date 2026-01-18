from unittest.mock import MagicMock

import bcrypt
import pytest
from src.database.services.worker import (WorkerManager, Worker, WorkerNotExistsError,
                                          WrongCredentialsError, LoginMatchError)
from tests.conftest import chain_factory

@pytest.mark.asyncio
class TestLoginWorker:
    async def test_login_success(self, chain_factory):
        password = "pass123"
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        client = MagicMock()
        client.table.return_value = chain_factory(
            [{"name": "Bob", "role": "dev", "id": 43, "password": hashed_password}]
        )

        mgr = WorkerManager(client)
        account = await mgr.login_worker("Bob123", "pass123")

        assert account == Worker("Bob", "dev", 43)

    async def test_login_wrong_password(self, chain_factory):
        password = "pass456"
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        client = MagicMock()
        client.table.return_value = chain_factory(
            [{"name": "Bob", "role": "dev", "id": 42, "password": hashed_password}]
        )

        mgr = WorkerManager(client)
        with pytest.raises(WrongCredentialsError):
            await mgr.login_worker("Bob123", "pass123")

    async def test_login_wrong_login(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory([])

        mgr = WorkerManager(client)

        with pytest.raises(WrongCredentialsError):
            await mgr.login_worker("Bob123", "pass123")

@pytest.mark.asyncio
class TestRegisterWorker:
    async def test_register_success(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory(
            [{"name": "Bob", "role": "Не назначена", "id": 43}]
        )

        mgr = WorkerManager(client)
        account = await mgr.register_worker("Bob", "Bob123", "pass123")

        assert account == Worker("Bob", "Не назначена", 43)

    async def test_register_no_name(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory([])

        mgr = WorkerManager(client)
        with pytest.raises(ValueError):
            await mgr.register_worker("", "Bob123", "pass123")

    async def test_register_matching_login(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory(exc=Exception("unique"))

        mgr = WorkerManager(client)
        with pytest.raises(LoginMatchError):
            await mgr.register_worker("Bob", "Bob123", "pass123")

    async def test_register_unknown_error(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory(exc=Exception("some error"))

        mgr = WorkerManager(client)
        account = await mgr.register_worker("Bob", "Bob123", "pass123")
        assert account is None

@pytest.mark.asyncio
class TestChangeRole:
    async def test_change_role_success(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory(
            [{"name": "Bob", "role": "notDev", "id": 43}]
        )

        mgr = WorkerManager(client)
        assert mgr.change_role(43, "notDev")

    async def test_change_role_account_not_found(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory([])

        mgr = WorkerManager(client)
        with pytest.raises(WorkerNotExistsError):
            await mgr.change_role(43, "notDev")

    async def test_change_role_invalid_input(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory(exc=Exception("invalid input"))

        mgr = WorkerManager(client)
        with pytest.raises(ValueError):
            await mgr.change_role(43, "notDev")

@pytest.mark.asyncio
class TestGetAllWorkers:
    async def test_get_all_accounts_success(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory(
            [{"name": "Bob", "role": "dev", "id": 43}, {"name": "Peter", "role": "notDev", "id": 44}]
        )

        mgr = WorkerManager(client)
        accounts = await mgr.get_all_workers()
        assert accounts == [Worker("Bob", "dev", 43), Worker("Peter", "notDev", 44)]

    async def test_get_all_accounts_not_found(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory([])

        mgr = WorkerManager(client)
        with pytest.raises(WorkerNotExistsError):
            await mgr.get_all_workers()

@pytest.mark.asyncio
class TestGetWorker:
    async def test_get_worker_success(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory(
            [{"name": "Bob", "role": "dev", "id": 42}]
        )

        mgr = WorkerManager(client)
        account = await mgr.get_worker(42)

        assert account == Worker("Bob", "dev", 42)

    async def test_get_worker_not_found(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory([])
        mgr = WorkerManager(client)

        with pytest.raises(WorkerNotExistsError):
          await mgr.get_worker(42)

    async def test_get_worker_invalid_input(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory(exc=Exception("invalid input"))
        mgr = WorkerManager(client)

        with pytest.raises(ValueError):
            await mgr.get_worker(1)

    async def test_get_worker_unknown_error(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory(exc=Exception("some error"))
        mgr = WorkerManager(client)

        account = await mgr.get_worker(42)
        assert account is None

@pytest.mark.asyncio
class TestDeleteWorker:
    async def test_delete_account_success(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory([{"id": 43}])

        mgr = WorkerManager(client)
        assert await mgr.delete_worker(43)

    async def test_delete_worker_not_found(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory([])

        mgr = WorkerManager(client)
        with pytest.raises(WorkerNotExistsError):
           await mgr.delete_worker(43)

    async def test_delete_worker_invalid_input(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory(exc=Exception("invalid input"))

        mgr = WorkerManager(client)
        with pytest.raises(ValueError):
            await mgr.delete_worker(43)