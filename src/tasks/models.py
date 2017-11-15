# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import requests
from subprocess import Popen
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone
from django.conf import settings


class Task(models.Model):
    STATUS_QUEUE = 2
    STATUS_RUNNING = 4
    STATUS_DONE = 8
    STATUS_CHOICES = {
        STATUS_QUEUE: 'In Queue',
        STATUS_RUNNING: 'Run',
        STATUS_DONE: 'Completed',
    }

    create_time = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField(null=True)  # NOTE: it's finish time
    exec_time = models.CharField(max_length=256, null=True)  # models.DurationField(null=True)
    status = models.SmallIntegerField(choices=STATUS_CHOICES.items(), default=STATUS_QUEUE)

    def __str__(self):
        return 'task:{0}, status:{1}'.format(self.id, self.STATUS_CHOICES[self.status])

    def started(self):
        self.start_time = timezone.now()  # NOTE: it's workaround for compliance with requirements
        self.status = self.STATUS_RUNNING
        self.save(update_fields=['start_time', 'status'])

    def finished(self):
        dt_now = timezone.now()
        self.exec_time = str(dt_now - self.start_time)
        self.start_time = dt_now
        self.status = self.STATUS_DONE
        self.save(update_fields=['exec_time', 'start_time', 'status'])


# TODO: add TaskChangeStatusLog model (as example for testing)


class Scheduler(models.Model):
    DEFAULT_NAME = 'default'
    name = models.CharField(max_length=256, default=DEFAULT_NAME)
    max_running_task = models.SmallIntegerField(default=2)  # TODO: get from settings, from ENV
    count_running_task = models.SmallIntegerField(default=0)

    def __str__(self):
        return 'scheduler: {0}, count_running: {1}'.format(self.name, self.count_running_task)

    def run_next(self):
        with transaction.atomic():
            sched = Scheduler.objects.select_for_update().get(pk=self.id)
            waiting_task = TaskRunner.objects.filter(sched=self, was_run=False, done=False)

            if not len(waiting_task):
                return
            if sched.count_running_task >= sched.max_running_task:
                return

            count_task_to_run = sched.max_running_task - sched.count_running_task
            tasks_to_run = waiting_task[:count_task_to_run]
            sched.count_running_task += len(tasks_to_run)
            for t in tasks_to_run:
                t.was_run = True
                t.save(update_fields=['was_run'])
            sched.save(update_fields=['count_running_task'])
        [task.run() for task in tasks_to_run]

    def task_finished(self):
        with transaction.atomic():
            sched = Scheduler.objects.select_for_update().get(pk=self.id)
            sched.count_running_task -= 1
            sched.save(update_fields=['count_running_task'])


class TaskRunnerManager(models.Manager):
    def create(self, *args, **kwargs):
        if 'sched_id' not in kwargs:
            sched, _ = Scheduler.objects.get_or_create(name=Scheduler.DEFAULT_NAME)
            kwargs['sched_id'] = sched.id
        if 'task_id' not in kwargs:
            task = Task.objects.create()
            kwargs['task_id'] = task.id
        return super(TaskRunnerManager, self).create(*args, **kwargs)


class TaskRunner(models.Model):
    task = models.OneToOneField(Task)
    sched = models.ForeignKey(Scheduler)
    cmdline = models.CharField(max_length=256, default='python {0}/test.py')
    pid = models.SmallIntegerField(null=True)
    ret_code = models.SmallIntegerField(null=True)
    run_timeout = models.SmallIntegerField(default=3600)
    done = models.BooleanField(default=False)
    was_run = models.BooleanField(default=False)
    node = models.CharField(max_length=256)  # NOTE: from 'request.get_host()'
    upstream = models.CharField(max_length=256, null=True)  # TODO: get valid value
    objects = TaskRunnerManager()

    def __str__(self):
        return 'node:{0}, task_id: {1}, done: {2}, ret_code: {3}'.format(self.node, self.task.id,
                                                                         self.done, self.ret_code)

    def run(self):
        started_url = 'http://' + self.node + reverse('task_started', kwargs={'pk': self.task.id})
        finished_url = 'http://' + self.node + reverse('task_finished', kwargs={'pk': self.task.id})

        launch_cmdline = ['python', '{0}/launcher.py'.format(settings.BASE_DIR),
                          '-c', self.cmdline.format(settings.BASE_DIR), '-s', started_url, '-f', finished_url]

        Popen(launch_cmdline)
        self.task.started()

    def started(self, info):
        self.pid = info.get('pid', -1)
        self.save(update_fields=['pid'])

    def finished(self, info):
        self.done = True
        self.ret_code = info.get('ret_code', -1)
        self.save(update_fields=['done', 'ret_code'])
        self.task.finished()
        # NOTE: improve, move to Scheduler and call from external kicker
        self.sched.task_finished()
        self.send_notify_run_next()

    def send_notify_run_next(self):
        """
        profit if exists load balancing
        """
        front = self.upstream or self.node
        front_url = 'http://' + front + reverse('sched_run_next', kwargs={'pk': self.sched.id})
        requests.post(front_url, timeout=60)


# TODO: add watchdog for checks
