# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from tasks.models import Task, TaskRunner, Scheduler

admin.site.register(Task)
admin.site.register(TaskRunner)
admin.site.register(Scheduler)
