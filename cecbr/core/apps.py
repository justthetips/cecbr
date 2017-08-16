from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'cecbr.core'
    verbose_name = "Core"

    def ready(self):
        """Override this to put in:
            Users system checks
            Users signal registration
        """
        pass
