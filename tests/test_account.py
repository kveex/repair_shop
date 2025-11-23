from src.database import account_manager, LoginMatchError, AccountNotExistsError
from pytest import raises

#login_account
#register_account
#change_role
#get_all_accounts
#delete_account

account_id = 0

def test_login_existing_account():
    assert account_manager.login_account("manager1", "pass123")

def test_login_nonexistent_account():
    assert not account_manager.login_account("nonexistent", "password")

def test_login_account_no_password():
    assert not account_manager.login_account("admin", "")

def test_login_account_no_login():
    assert not account_manager.login_account("", "password")

def test_register_account():
    global account_id
    account_id = account_manager.register_account("test_name", "test_login", "test_password")
    assert account_id

def test_register_account_empty_fields():
    with raises(ValueError):
        account_manager.register_account("", "", "")

def test_register_account_matching_login():
    with raises(LoginMatchError):
        account_manager.register_account("test_name", "manager1", "test_password")

def test_change_role():
    assert account_manager.change_role(account_id, "Менеджер")

def test_get_account():
    account = account_manager.get_account(account_id)
    assert account
    assert isinstance(account, tuple)
    assert isinstance(account[0], str)
    assert isinstance(account[1], str)
    assert isinstance(account[2], int)

def test_get_account_nonexistent():
    with raises(AccountNotExistsError):
        account_manager.get_account(0)

def test_get_account_no_id():
    with raises(ValueError):
        account_manager.get_account(None)

def test_delete_account():
    assert account_manager.delete_account(account_id)

def test_delete_account_nonexistent():
    with raises(AccountNotExistsError):
        account_manager.delete_account(account_id)

def test_delete_account_no_id():
    with raises(ValueError):
        account_manager.delete_account(None)

def test_get_all_accounts():
    accounts = account_manager.get_all_accounts()
    assert len(accounts) > 0
    assert isinstance(accounts, list)
    assert isinstance(accounts[0], tuple)