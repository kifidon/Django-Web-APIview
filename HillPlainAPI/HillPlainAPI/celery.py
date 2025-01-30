import os
from celery import Celery
# import BackgroundTasks.tasks
# from HillPlainAPI import settings
from celery.schedules import crontab
# import BackgroundTasks

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HillPlainAPI.settings')

app = Celery('HillPlainAPI')

# Using a string here means the worker doesn't 
# have to serialize the configuration object to 
# child processes. - namespace='CELERY' means all 
# celery-related configuration keys should 
# have a `CELERY_` prefix.
app.config_from_object('django.conf:settings',
                       namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.update(
    broker_connection_retry_on_startup=True,  # Enable retry on startup
)

app.conf.beat_schedule = {
    # 'UserEvent': {
    #     'task': 'BackgroundTasks.tasks.UserEvent',
    #     'schedule': crontab(minute=0, hour=0, day_of_week='sun'),  # Runs at 9:00 AM every Monday
    #     'args': ['Hill Plain'],
    # },
    'ClientEvent': {
        'task': 'BackgroundTasks.tasks.ClientEvent',
        'schedule': crontab(minute=0, hour=1, day_of_week='sun'),  # Runs at 9:00 AM every Tuesday
        'args': ['Hill Plain'],
    },
    # For debugging
    # 'ClientEvent': {
    #     'task': 'BackgroundTasks.tasks.ClientEvent',
    #     'schedule': crontab(minute='*'),  # Runs once per minute
    #     'args': ['Hill Plain'],
    # },
    'ProjectEvent': {
        'task': 'BackgroundTasks.tasks.ProjectEvent',
        'schedule': crontab(minute=0, hour=2, day_of_week='sun'),  # Runs at 9:00 AM every Wednesday
        'args': ['Hill Plain'],
    },
    'PolicyEvent': {
        'task': 'BackgroundTasks.tasks.PolicyEvent',
        'schedule': crontab(minute=0, hour=3, day_of_week='sun'),  # Runs at 9:00 AM every Thursday
        'args': ['Hill Plain'],
    },
    'TimesheetEvent': {
        'task': 'BackgroundTasks.tasks.TimesheetEvent',
        'schedule': crontab(minute=0, hour=4),  # Runs at 9:00 AM every Friday
        'args': ['Hill Plain'],
    },
    'TimeOffEvent': {
        'task': 'BackgroundTasks.tasks.TimeOffEvent',
        'schedule': crontab(minute=0, hour=5, day_of_week='sun'),  # Runs at 9:00 AM every Saturday
        'args': ['Hill Plain'],
    },
    'HolidayEvent': {
        'task': 'BackgroundTasks.tasks.HolidayEvent',
        'schedule': crontab(month_of_year='1,4,7,10', day_of_week='sun', hour=9, minute=0),  # Runs at 9:00 AM every Sunday in January, April, July, and October
        'args': ['Hill Plain'],
    },
    'CalendarEvent': {
        'task': 'BackgroundTasks.tasks.CalendarEvent',
        'schedule': crontab(minute=0, hour=7, day_of_month='1', month_of_year='1'),  # Runs on the first Monday in January
    },
    'BankedHrs_at_6am': {
        'task': 'BackgroundTasks.tasks.BankedHrsTask',
        'schedule': crontab(minute=0, hour=6),  # Runs at 6:00 AM daily
        'args': [],  # Add arguments if required
    },
    'UpdateSalaryVacation_at_6am': {
        'task': 'BackgroundTasks.tasks.SalaryVacationTask',
        'schedule': crontab(minute=5, hour=6),  # Runs at 6:00 AM daily
        'args': [],  # Add arguments if required
    }

}
