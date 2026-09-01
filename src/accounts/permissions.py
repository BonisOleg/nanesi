"""RBAC у сервісах (ecommerce_business_logic_skill, крок 4) — перевірка ВСЕРЕДИНІ
service-функції, не лише на view/admin рівні (щоб admin action теж не проходив
повз перевірку). Гранулярні чекбокси на менеджера (manager_permission) — Етап D,
якщо клієнт попросить обмежити конкретних менеджерів; зараз роль MANAGER = усі
операційні дії дозволені (немодерований мінімум, задокументований тут явно)."""
from src.accounts.models import User


def user_can_manage_orders(user) -> bool:
    if user is None or not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser or user.role == User.Role.ADMIN:
        return True
    return user.role == User.Role.MANAGER
