from django.apps import AppConfig


class PluginApp(AppConfig):
    name = 'pretix_pizzabot'
    verbose_name = 'Pizza group orders for pretix'

    class PretixPluginMeta:
        name = 'Pizza group orders for pretix'
        author = 'Raphael Michel'
        description = 'Pizza group orders for pretix'
        visible = True
        version = '1.0.0'

    def ready(self):
        from . import signals  # NOQA


default_app_config = 'pretix_pizzabot.PluginApp'
