from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest

from src.database.services.order import (Order, OrderManager, Client,
                                         ClientManager, Service, ClientNotExistsError,
                                         ServiceNotExistsError, Worker)
from tests.conftest import chain_factory

class TestMakeOrderNewClient:
    def test_make_order_new_client_success(self, chain_factory):
        client_obj = Client(name="Bob", phone="+79993456789", address="Home", id=12)
        client_manager = MagicMock()
        client_manager.add_client.return_value = client_obj

        om = object.__new__(OrderManager)
        om.client_manager = client_manager
        om.make_order = MagicMock(return_value=True)
        om.supabase = MagicMock()

        service = Service(name="Test", description="Test", price=100, id=12)

        client_returned, ok = om.make_order_new_client(
            client_name=client_obj.name,
            client_phone=client_obj.phone,
            client_address=client_obj.address,
            service=service,
            trouble_description="Meh"
        )

        assert ok is True
        assert client_returned == client_obj

        om.supabase.table.assert_not_called()

    def test_make_order_new_client_order_failed_deletes_client(self, chain_factory):
        client_obj = Client(name="Bob", phone="+79993456789", address="Home", id=12)
        client_manager = MagicMock()
        client_manager.add_client.return_value = client_obj

        om = object.__new__(OrderManager)
        om.client_manager = client_manager
        om.make_order = MagicMock(return_value=False)

        # Подготовим supabase mock, который вернёт chain для delete().eq().execute()
        supabase = MagicMock()
        supabase.table.return_value = chain_factory([])  # ответ delete.execute() — не важен
        om.supabase = supabase

        service = Service(name="Test", description="Test", price=100, id=12)

        client_returned, ok = om.make_order_new_client(
            client_name=client_obj.name,
            client_phone=client_obj.phone,
            client_address=client_obj.address,
            service=service,
            trouble_description="Meh"
        )

        assert ok is False
        assert client_returned is None

        # Проверяем что удаление вызвано корректно по id клиента
        supabase.table.assert_called_once_with("clients")
        supabase.table().delete.assert_called_once()
        supabase.table().delete().eq.assert_called_once_with("id", client_obj.id)
        supabase.table().delete().execute.assert_called_once()

    def test_make_order_new_client_add_client_raises_returns_none_false(self):
        client_manager = MagicMock()
        client_manager.add_client.side_effect = Exception("db error")

        om = object.__new__(OrderManager)
        om.client_manager = client_manager
        om.make_order = MagicMock()  # не должен вызываться
        om.supabase = MagicMock()

        service = Service(name="Test", description="Test", price=100, id=12)

        client_returned, ok = om.make_order_new_client(
            client_name="X", client_phone="Y", client_address="Z",
            service=service, trouble_description="T"
        )

        assert client_returned is None
        assert ok is False
        om.supabase.table.assert_not_called()

