import pytest
from db import supabase
from services.client import *

#get_all_clients
#get_client
#add_client
#delete_client

def test_get_all_clients():
    clients = get_all_clients(supabase)
    assert len(clients) > 0
    assert isinstance(clients[0], tuple)

def test_get_existing_client():
    client = get_client(supabase, "+79993336545")
    assert client
    assert isinstance(client, tuple)

def test_get_non_existing_client():
    client = get_client(supabase, "+70000000000")
    assert not client

def test_get_client_wrong_length_phone():
    with pytest.raises(ValueError):
        get_client(supabase, "+7999643234")

def test_get_client_no_phone():
    with pytest.raises(ValueError):
        get_client(supabase, "")

def test_add_client():
    client_id = add_client(supabase, "name", "+79996432342")
    assert isinstance(client_id, int)
    delete_client(supabase, client_id)

def test_add_client_with_address():
    client_id = add_client(supabase, "name", "+79996432342", "address")
    assert isinstance(client_id, int)
    delete_client(supabase, client_id)

def test_add_client_no_phone():
    with pytest.raises(ValueError):
        add_client(supabase, "name", "")

def test_add_client_wrong_length_phone():
    with pytest.raises(ValueError):
        add_client(supabase, "name", "+7999643234")

def test_add_client_duplicate_phone():
    with pytest.raises(ClientExistsError):
        add_client(supabase, "name", "+79997654321")

def test_delete_existing_client():
    client_id = add_client(supabase, "name", "+79996432342")
    delete_client(supabase, client_id)

def test_delete_non_existing_client():
    with pytest.raises(ClientNotExistsError):
        delete_client(supabase, 0)