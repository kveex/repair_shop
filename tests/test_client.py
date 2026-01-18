from unittest.mock import MagicMock

import pytest
from src.database.services.client import (Client, ClientManager,
                                           ClientNotExistsError, ClientExistsError)
from tests.conftest import chain_factory

@pytest.mark.asyncio
class TestAddClient:
    async def test_add_client_success(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory(
            [{"id": 12, "name": "Bob", "phone": "+79993456789", "address": "Home"}]
        )

        cm = ClientManager(client)
        result = await cm.add_client("Bob", "+79993456789", "Home")

        assert result == Client(name="Bob", phone="+79993456789", address="Home", id=12)

    async def test_add_client_short_phone(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory(
            [{"id": 12, "name": "Bob", "phone": "+79993456789", "address": "Home"}]
        )

        cm = ClientManager(client)
        with pytest.raises(ValueError):
           await cm.add_client("Bob", "+7999345", "Home")

    async def test_add_client_long_phone(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory(
            [{"id": 12, "name": "Bob", "phone": "+79993456789", "address": "Home"}]
        )

        cm = ClientManager(client)
        with pytest.raises(ValueError):
            await cm.add_client("Bob", "+7999345678954334", "Home")

    async def test_add_client_empty_phone(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory(
            [{"id": 12, "name": "Bob", "phone": "+79993456789", "address": "Home"}]
        )

        cm = ClientManager(client)
        with pytest.raises(ValueError):
            await cm.add_client("Bob", "", "Home")

    async def test_add_client_empty_name(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory(
            [{"id": 12, "name": "Bob", "phone": "+79993456789", "address": "Home"}]
        )

        cm = ClientManager(client)
        with pytest.raises(ValueError):
            await cm.add_client("", "+79993456789", "Home")


    async def test_add_client_already_existing_client(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory(exc=Exception("unique"))

        cm = ClientManager(client)
        with pytest.raises(ClientExistsError):
            await cm.add_client("Bob", "+79993456789", "Home")

    async def test_add_client_some_error(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory(exc=Exception("some error"))

        cm = ClientManager(client)
        with pytest.raises(ValueError):
           await cm.add_client("Bob", "+79993456789", "Home")

@pytest.mark.asyncio
class TestDeleteClient:
    async def test_delete_client_success(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory(
            [{"id": 12, "name": "Bob", "phone": "+79993456789", "address": "Home"}]
        )

        cm = ClientManager(client)
        assert await cm.delete_client(12)

    async def test_delete_client_not_exists(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory([])

        cm = ClientManager(client)
        with pytest.raises(ClientNotExistsError):
            await cm.delete_client(12)

    async def test_delete_client_invalid_input(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory(exc=Exception("invalid input"))

        cm = ClientManager(client)
        with pytest.raises(ValueError):
            await cm.delete_client(12)

    async def test_delete_client_some_error(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory(exc=Exception("some error"))

        cm = ClientManager(client)
        assert not await cm.delete_client(12)

@pytest.mark.asyncio
class TestGetClient:
    async def test_get_client_success(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory(
            [{"id": 12, "name": "Bob", "phone": "+79993456789", "address": "Home"}]
        )

        cm = ClientManager(client)
        result = await cm.get_client("+79993456789")

        assert result == Client(name="Bob", phone="+79993456789", address="Home", id=12)

    async def test_get_client_short_phone(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory(
            [{"id": 12, "name": "Bob", "phone": "+79993456789", "address": "Home"}]
        )

        cm = ClientManager(client)
        with pytest.raises(ValueError):
            await cm.get_client("+7999345")

    async def test_get_client_long_phone(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory(
            [{"id": 12, "name": "Bob", "phone": "+79993456789", "address": "Home"}]
        )

        cm = ClientManager(client)
        with pytest.raises(ValueError):
            await cm.get_client("+79993456789734824")

    async def test_get_client_empty_phone(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory(
            [{"id": 12, "name": "Bob", "phone": "+79993456789", "address": "Home"}]
        )

        cm = ClientManager(client)
        with pytest.raises(ValueError):
            await cm.get_client("")

    async def test_get_client_not_exists(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory([])

        cm = ClientManager(client)
        with pytest.raises(ClientNotExistsError):
            await cm.get_client("+79993456789")

@pytest.mark.asyncio
class TestGetAllClients:
    async def test_get_all_clients_success(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory([
            {"id": 12, "name": "Bob", "phone": "+79993456789", "address": "Home"},
            {"id": 13, "name": "Phill", "phone": "+71119876543", "address": "NotHome"},
        ])

        cm = ClientManager(client)
        result = await cm.get_all_clients()

        assert result == [
            Client(name="Bob", phone="+79993456789", address="Home", id=12),
            Client(name="Phill", phone="+71119876543", address="NotHome", id=13)
        ]

    async def test_get_all_clients_no_clients(self, chain_factory):
        client = MagicMock()
        client.table.return_value = chain_factory([])

        cm = ClientManager(client)
        with pytest.raises(ClientNotExistsError):
            await cm.get_all_clients()