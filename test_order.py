from services.order import *
from services.service import ServiceNotExists
from services.client import delete_client
from db import supabase
import pytest

#make_order
#make_order_new_client
#get_all_orders
#get_order

def test_make_order_existing_client():
    assert make_order(supabase, "+79997654321", "Замена", "Тестовый заказ")
    supabase.table("orders").delete().eq("trouble_description", "Тестовый заказ").execute()

def test_make_order_existing_client_wrong_phone():
    with pytest.raises(ValueError):
        make_order(supabase, "+79999999999", "Замена", "Тестовый заказ")

def test_make_order_existing_client_no_phone():
    with pytest.raises(ValueError):
        make_order(supabase, "", "Замена", "Тестовый заказ")

def test_make_order_existing_client_no_service():
    with pytest.raises(ValueError):
        make_order(supabase, "+79997654321", "", "Тестовый заказ")

def test_make_order_existing_client_wrong_service():
    with pytest.raises(ServiceNotExists):
        make_order(supabase, "+79997654321", "арывлаорфл", "Тестовый заказ")
    
def test_make_order_new_client():
    order = make_order_new_client(supabase, "test_name", "+78005553535", "test_address", "Замена", "Тестовый заказ")
    assert order[1]
    delete_client(supabase, order[0])

def test_make_order_new_client_no_phone():
    with pytest.raises(ValueError):
        make_order_new_client(supabase, "test_name", "", "test_address", "Замена", "Тестовый заказ")

def test_make_order_new_client_no_name():
    with pytest.raises(ValueError):
        make_order_new_client(supabase, "", "+78005553536", "test_address", "Замена", "Тестовый заказ")

# passes but does not delete client
# def test_make_order_new_client_no_service():
#     with pytest.raises(ValueError):
#         make_order_new_client(supabase, "test_name", "+78005553536", "test_address15", "", "Тестовый заказ")
        
def test_get_all_orders():
    assert get_all_orders(supabase)

def test_get_order():
    order = get_order(supabase, "+79993336545")
    assert order
    assert isinstance(order, list)
    assert isinstance(order[0], tuple)

def test_get_order_no_phone():
    with pytest.raises(ValueError):
        get_order(supabase, "")