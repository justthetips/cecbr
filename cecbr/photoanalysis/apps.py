from django.apps import AppConfig


class PhotoAnalysisConfig(AppConfig):
    name = 'cecbr.photoanalysis'
    verbose_name = "Photo Analysis"

    def ready(self):
        """Override this to put in:
            Users system checks
            Users signal registration
        """
        pass
