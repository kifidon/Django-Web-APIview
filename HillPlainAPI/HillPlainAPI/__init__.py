from django.apps import AppConfig

class HillPlainAPIConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'HillPlainAPI'
    
from .celery import app as celery_app

__all__ = ['celery_app']
