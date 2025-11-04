from supabase import Client

def get_service(supabase: Client) -> tuple[str, str, int | None, int]:
    #TODO: сделать поиск по части слова
    services: list = supabase.table("services").select("*").execute().data
    service_name: str = input("Введите название услуги: ")

    for service in services:
        s_id: int = service["id"]
        name: str = service["name"]
        description: str = service["description"]
        price: int = service["price"]

        if name.lower() == service_name.lower():
            return name, description, price, s_id
    return None