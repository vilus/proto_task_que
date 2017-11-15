from django.conf.urls import url
from tasks.views import create_and_kick_task, get_task_detail, task_started, task_finished, run_next


urlpatterns = [
    # url(r'^tasks/$', task_list, name='task_list'),  # TODO
    url(r'^tasks/add/$', create_and_kick_task, name='task_add'),
    url(r'^tasks/(?P<pk>\d+)/$', get_task_detail, name='task_detail'),
    url(r'^tasks/(?P<pk>\d+)/started/$', task_started, name='task_started'),
    url(r'^tasks/(?P<pk>\d+)/finished/$', task_finished, name='task_finished'),

    url(r'^scheds/(?P<pk>\d+)/run_next/$', run_next, name='sched_run_next'),
]
