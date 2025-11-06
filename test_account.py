from services.account import *
from db import supabase
import pytest

#login_account
#register_account
#get_all_accounts
#delete_account

account_id = 0
def test_login_existing_account():
    assert login_account(supabase, "manager1", "pass123")

def test_login_nonexistent_account():
    assert not login_account(supabase, "nonexistent", "password")

def test_login_account_no_password():
    assert not login_account(supabase, "admin", "")

def test_login_account_no_login():
    assert not login_account(supabase, "", "password")

def test_register_account():
    global account_id
    account_id = register_account(supabase, "test_name", "test_role", "test_login", "test_password")
    assert account_id

def test_register_account_empty_fields():
    with pytest.raises(ValueError):
        register_account(supabase, "", "", "", "")

def test_refister_account_matching_login():
    with pytest.raises(LoginMatchError):
        register_account(supabase, "test_name", "test_role", "manager1", "test_password")

def test_get_account():
    account = get_account(supabase, account_id)
    assert account
    assert isinstance(account, tuple)
    assert isinstance(account[0], str)
    assert isinstance(account[1], str)
    assert isinstance(account[2], int)

def test_get_account_nonexistent():
    with pytest.raises(AccountNotExistsError):
        get_account(supabase, 0)

def test_get_account_no_id():
    with pytest.raises(ValueError):
        get_account(supabase, None)

def test_delete_account():
    assert delete_account(supabase, account_id)

def test_delete_account_nonexistent():
    with pytest.raises(AccountNotExistsError):
        delete_account(supabase, account_id)

def test_delete_account_no_id():
    with pytest.raises(ValueError):
        delete_account(supabase, None)

def test_get_all_accounts():
    accounts = get_all_accounts(supabase)
    assert len(accounts) > 0
    assert isinstance(accounts, list)
    assert isinstance(accounts[0], tuple)