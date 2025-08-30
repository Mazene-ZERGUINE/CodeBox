"""
initializes the Celery application for the Django project.

It ensures the Celery app is correctly integrated with Django's settings
and task modules.
"""
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'codeBox.settings')

app = Celery('codeBox_celery', include=['codeBox.tasks'])
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
