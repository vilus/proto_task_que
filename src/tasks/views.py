# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from tasks.models import TaskRunner, Task, Scheduler


@csrf_exempt
@require_POST
def create_and_kick_task(request):
    task_runner = TaskRunner.objects.create(node=request.get_host())
    task_runner.sched.run_next()  # It is bad :( need use external periodical kicker
    return JsonResponse({'task_id': task_runner.task.id})


@csrf_exempt
@require_POST
def get_task_detail(_, pk):
    task = get_object_or_404(Task, pk=pk)
    return JsonResponse({'status': task.STATUS_CHOICES.get(task.status, 'unknown status'),
                         'create_time': task.create_time,
                         'start_time': task.start_time,
                         'time_to_execute': str(task.exec_time)})


@csrf_exempt
@require_POST
def task_started(request, pk):
    task_runner = get_object_or_404(TaskRunner, task__id=pk)
    # NOTE: checks for already started, ...
    try:  # NOTE: improve (check json schema)
        info = json.loads(request.body.decode('utf-8'))  # TODO: clean
    except ValueError:
        return HttpResponseBadRequest()

    task_runner.started(info)
    return JsonResponse({})


@csrf_exempt
@require_POST
def task_finished(request, pk):
    task_runner = get_object_or_404(TaskRunner, task__id=pk)
    # NOTE: checks for already finished ...
    try:  # NOTE: improve (check json schema)
        info = json.loads(request.body.decode('utf-8'))  # TODO: clean
    except ValueError:
        return HttpResponseBadRequest()

    task_runner.finished(info)
    return JsonResponse({})


@csrf_exempt
@require_POST
def run_next(_, pk):
    sched = get_object_or_404(Scheduler, pk=pk)
    sched.run_next()
    return JsonResponse({})
