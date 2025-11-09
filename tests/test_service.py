from src.database.services.service import *
from src.database import service_manager
import pytest

#add_service
#delete_service
#get_all_services
#!get_service_by_id
#!get_service_by_name

s_id = 0
name = ""

def test_add_service():
    global s_id
    s_id = service_manager.add_service("test_service", "test_description", 1000)
    assert s_id

def test_add_service_no_name():
    with pytest.raises(ValueError):
        assert service_manager.add_service("", "test_description", None)

def test_add_service_no_description():
    with pytest.raises(ValueError):
        assert service_manager.add_service("test_service", "", None)

def test_get_service_by_id():
    global name
    service = service_manager.get_service_by_id(s_id)
    assert service
    name = service[0]

def test_get_service_by_id_nonexistent():
    with pytest.raises(ServiceNotExists):
        assert service_manager.get_service_by_id(-1)

def test_get_service_by_id_no_id():
    with pytest.raises(ValueError):
        assert service_manager.get_service_by_id(None)
    
def test_get_service_by_name():
    assert service_manager.get_service_by_name(name)

def test_get_service_by_name_nonexistent():
    with pytest.raises(ServiceNotExists):
        assert service_manager.get_service_by_name("test")

def test_get_service_by_name_no_name():
    with pytest.raises(ValueError):
        assert service_manager.get_service_by_name(None)
    
def test_get_all_services():
    assert service_manager.get_all_services()

def test_delete_service():
    assert service_manager.delete_service(s_id)

def test_delete_service_no_id():
    with pytest.raises(ValueError):
        assert service_manager.delete_service(None)

def test_delete_service_nonexistent():
    with pytest.raises(ServiceNotExists):
        assert service_manager.delete_service(-1)