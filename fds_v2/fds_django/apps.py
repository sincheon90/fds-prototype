# fds_django/apps.py
from django.apps import AppConfig

class FdsDjangoConfig(AppConfig):
    name = "fds_django"

    def ready(self):
        try:
            from fds_core.rule_cache import load_rules_from_db
            load_rules_from_db()
        except Exception as e:
            print(f"[rules] skip preload: {e}")