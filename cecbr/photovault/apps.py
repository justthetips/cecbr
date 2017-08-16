from django.apps import AppConfig


class PhotoVaultConfig(AppConfig):
    name = 'cecbr.photovault'
    verbose_name = "Vault"

    def ready(self):
        """Override this to put in:
            Users system checks
            Users signal registration
        """
        pass
