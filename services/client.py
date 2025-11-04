from supabase import Client

def get_client(supabase: Client) -> tuple[str, str, str, int]:
    client_phone: str = input("Введите номер телефона клиента: ")
    client_exist: list= supabase.table("clients").select("*").eq("phone", client_phone).execute().data
    if client_exist:
        c_id: int = client_exist[0]["id"]
        phone: str = client_exist[0]["phone"]
        name: str = client_exist[0]["name"]
        address: str = client_exist[0]["address"]
        return name, phone, address, c_id
    return None