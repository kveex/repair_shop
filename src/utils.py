import re

class PhoneValidationError(Exception):pass
class PhoneLengthError(PhoneValidationError):pass
class WrongPhoneCode(PhoneValidationError): pass

def format_phone_for_db(phone: str) -> str:
    cleaned = re.sub(r'[^\d+]', '', phone)

    if cleaned.startswith('8'):
        cleaned = '+7' + cleaned[1:]

    if not cleaned.startswith('+'):
        cleaned = '+7' + cleaned

    return cleaned

def validate_phone(phone: str) -> str:
    normalized = format_phone_for_db(phone)

    if not normalized.startswith('+7'):
        raise WrongPhoneCode("Номер должен начинаться с +7 или 8")

    if len(normalized) != 12:
        raise PhoneLengthError(f"Номер должен содержать 10 цифр, после +7. Получено: {len(normalized) - 2}")

    if not normalized[2:].isdigit():
        raise PhoneValidationError("Номер содержит недопустимые символы")

    return normalized


def format_phone_for_display(phone: str) -> str:
    normalized = format_phone_for_db(phone)

    if len(normalized) < 12:
        return normalized

    return f"{normalized[:2]} ({normalized[2:5]}) {normalized[5:8]}-{normalized[8:10]}-{normalized[10:]}"