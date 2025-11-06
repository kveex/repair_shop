from db import supabase
from services.service import *
import pytest

#add_service
#delete_service
#get_all_services
#!get_service_by_id
#!get_service_by_name

id = 0
name = ""

def test_add_service():
    global id
    id = add_service(supabase, "test_service", "test_description", 1000)
    assert id

def test_add_service_no_name():
    with pytest.raises(ValueError):
        assert add_service(supabase, "", "test_description", None)

def test_add_service_no_description():
    with pytest.raises(ValueError):
        assert add_service(supabase, "test_service", "", "")

def test_get_service_by_id():
    global name
    service = get_service_by_id(supabase, id)
    assert service
    name = service[0]

def test_get_service_by_id_nonexistent():
    with pytest.raises(ServiceNotExists):
        assert get_service_by_id(supabase, -1)

def test_get_service_by_id_no_id():
    with pytest.raises(ValueError):
        assert get_service_by_id(supabase, None)
    
def test_get_service_by_name():
    assert get_service_by_name(supabase, name)

def test_get_service_by_name_nonexistent():
    with pytest.raises(ServiceNotExists):
        assert get_service_by_name(supabase, "test")

def test_get_service_by_name_no_name():
    with pytest.raises(ValueError):
        assert get_service_by_name(supabase, None)
    
def test_get_all_services():
    assert get_all_services(supabase)

def test_delete_service():
    assert delete_service(supabase, id)

def test_delete_service_no_id():
    with pytest.raises(ValueError):
        assert delete_service(supabase, None)

def test_delete_service_nonexistent():
    with pytest.raises(ServiceNotExists):
        assert delete_service(supabase, -1)