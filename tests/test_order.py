import pytest
from src.database import _supabase, order_manager, client_manager
from src.database.services.service import ServiceNotExists


#make_order
#make_order_new_client
#get_all_orders
#get_order

def test_make_order_existing_client():
    assert order_manager.make_order("+79997654321", "Замена", "Тестовый заказ")
    _supabase.table("orders").delete().eq("trouble_description", "Тестовый заказ").execute()

def test_make_order_existing_client_wrong_phone():
    with pytest.raises(ValueError):
        order_manager.make_order("+79999999999", "Замена", "Тестовый заказ")

def test_make_order_existing_client_no_phone():
    with pytest.raises(ValueError):
        order_manager.make_order("", "Замена", "Тестовый заказ")

def test_make_order_existing_client_no_service():
    with pytest.raises(ValueError):
        order_manager.make_order("+79997654321", "", "Тестовый заказ")

def test_make_order_existing_client_wrong_service():
    with pytest.raises(ServiceNotExists):
        order_manager.make_order("+79997654321", "арывлаорфл", "Тестовый заказ")
    
def test_make_order_new_client():
    order = order_manager.make_order_new_client("test_name", "+78005553535", "test_address", "Замена", "Тестовый заказ")
    assert order[1]
    client_manager.delete_client(order[0])

def test_make_order_new_client_no_phone():
    with pytest.raises(ValueError):
        order_manager.make_order_new_client("test_name", "", "test_address", "Замена", "Тестовый заказ")

def test_make_order_new_client_no_name():
    with pytest.raises(ValueError):
        order_manager.make_order_new_client("", "+78005553536", "test_address", "Замена", "Тестовый заказ")

def test_make_order_new_client_no_service():
    with pytest.raises(ValueError):
        order_manager.make_order_new_client("test_name", "+78005553536", "test_address15", "", "Тестовый заказ")
        # supabase.table("clients").delete().eq("phone", "+78005553536")
        
def test_get_all_orders():
    assert order_manager.get_all_orders()

def test_get_order():
    order = order_manager.get_order("+79993336545")
    assert order
    assert isinstance(order, list)
    assert isinstance(order[0], tuple)

def test_get_order_no_phone():
    with pytest.raises(ValueError):
        order_manager.get_order("")