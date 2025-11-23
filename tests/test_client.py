import pytest

from src.database import client_manager, ClientExistsError, ClientNotExistsError

#get_all_clients
#get_client
#add_client
#delete_client

def test_get_all_clients():
    clients = client_manager.get_all_clients()
    assert len(clients) > 0
    assert isinstance(clients[0], tuple)

def test_get_existing_client():
    client = client_manager.get_client("+79993336545")
    assert client
    assert isinstance(client, tuple)

def test_get_non_existing_client():
    client = client_manager.get_client("+70000000000")
    assert not client

def test_get_client_wrong_length_phone():
    with pytest.raises(ValueError):
        client_manager.get_client("+7999643234")

def test_get_client_no_phone():
    with pytest.raises(ValueError):
        client_manager.get_client("")

def test_add_client():
    client_id = client_manager.add_client("name", "+79996432342")
    assert isinstance(client_id, int)
    client_manager.delete_client(client_id)

def test_add_client_with_address():
    client_id = client_manager.add_client("name", "+79996432342", "address")
    assert isinstance(client_id, int)
    client_manager.delete_client(client_id)

def test_add_client_no_phone():
    with pytest.raises(ValueError):
        client_manager.add_client("name", "")

def test_add_client_wrong_length_phone():
    with pytest.raises(ValueError):
        client_manager.add_client("name", "+7999643234")

def test_add_client_duplicate_phone():
    with pytest.raises(ClientExistsError):
        client_manager.add_client("name", "+79997654321")

def test_delete_existing_client():
    client_id = client_manager.add_client("name", "+79996432342")
    client_manager.delete_client(client_id)

def test_delete_non_existing_client():
    with pytest.raises(ClientNotExistsError):
        client_manager.delete_client(-1)