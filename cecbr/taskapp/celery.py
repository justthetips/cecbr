
import os
from celery import Celery
from django.apps import apps, AppConfig
from django.conf import settings
from celery.utils.log import get_task_logger
from celery.schedules import crontab



if not settings.configured:
    # set the default Django settings module for the 'celery' program.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')  # pragma: no cover


app = Celery('cecbr')
logger = get_task_logger(__name__)



class CeleryConfig(AppConfig):
    name = 'cecbr.taskapp'
    verbose_name = 'Celery Config'

    def ready(self):
        # Using a string here means the worker will not have to
        # pickle the object when using Windows.
        app.config_from_object('django.conf:settings')
        installed_apps = [app_config.name for app_config in apps.get_app_configs()]
        app.autodiscover_tasks(lambda: installed_apps, force=True)

        if hasattr(settings, 'RAVEN_CONFIG'):
            # Celery signal registration
# Since raven is required in production only,
            # imports might (most surely will) be wiped out
            # during PyCharm code clean up started
            # in other environments.
            # @formatter:off
            from raven import Client as RavenClient
            from raven.contrib.celery import register_signal as raven_register_signal
            from raven.contrib.celery import register_logger_signal as raven_register_logger_signal
# @formatter:on

            raven_client = RavenClient(dsn=settings.RAVEN_CONFIG['DSN'])
            raven_register_logger_signal(raven_client)
            raven_register_signal(raven_client)




@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))  # pragma: no cover

@app.task(bind=True)
def update_albums(self):
    from cecbr.photos.models import CECBRProfile, Season
    seasons = Season.objects.all()
    profile = CECBRProfile.objects.get(user_id=1)
    for season in seasons:
        logger.info("Updating albums in {}".format(season.season_name))
        season.process_season(profile=profile)

@app.task(bind=True)
def process_albums(self):
    from cecbr.photos.models import CECBRProfile, Album
    from cecbr.photos.utils.parsers import get_logged_on_page
    albums = Album.objects.filter(processed=False)
    profile = CECBRProfile.objects.get(user_id=1)
    page = get_logged_on_page(profile.cecbr_uname, profile.get_pwd())
    for album in albums:
        logger.info("Processing Album {}".format(album.album_name))
        album.process_album(profile, page)
    page.close()




