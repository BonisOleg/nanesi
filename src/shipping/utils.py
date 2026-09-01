"""Нормалізатори перед відправкою в API НП (novaposhta_skill, Фаза 3 pitfalls)."""
import re


def normalize_phone(raw: str) -> str:
    """→ '380XXXXXXXXX' без '+' і пробілів (спільний формат з TurboSMS/НП)."""
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("0") and len(digits) == 10:
        digits = "38" + digits
    if digits.startswith("380"):
        return digits
    if len(digits) == 9:
        return "380" + digits
    return digits


def split_full_name(full_name: str) -> tuple[str, str]:
    """'Іванов Іван' → ('Іван', 'Іванов'). Без прізвища — вважаємо все ім'ям."""
    parts = (full_name or "").strip().split()
    if len(parts) >= 2:
        last_name, first_name = parts[0], " ".join(parts[1:])
        return first_name, last_name
    return (parts[0] if parts else "Клієнт"), ""
