from django.conf.urls import url, include

from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    url(r'^register/$', views.RegisterFormView.as_view(), name='register'),
    url(r'^login/$', views.LoginFormView.as_view(), name='login'),
    url(r'^ajax/validate_username/$', views.validate_username, name='validate_username'),
    url(r'^ajax/get_recent_task/$', views.get_recent_task, name='get_recent_task'),
    url(r'^logout/$', views.logout_view, name='logout'),
    url(r'^profile/$', views.update_profile, name='profile'),
    url(r'^invite/$', views.user_invite, name='user_invite'),
    url(r'^search/$', views.search_result, name='search'),
    url(r'^$', views.task_list, name='task_list'),
    url(r'^task_finished/$', views.task_list_finished, name='task_list_finished'),
    url(r'^project_tasks_list/(?P<pk>[0-9]+)/', views.project_task_list, name='project_tasks_list'),
    url(r'^task/(?P<pk>[0-9]+)/$', views.task_detail, name='task_detail'),
    url(r'^task/(?P<pk>[0-9]+)/edit/$', views.task_edit, name='task_edit'),
    url(r'^task/(?P<pk>[0-9]+)/del$', views.task_del, name='task_del'),
    url(r'^project/(?P<pk>[0-9]+)/del$', views.project_del, name='project_del'),
    url(r'^(?P<pk>[0-9]+)/finish$', views.task_finish, name='task_finish'),
    url(r'^task/(?P<pk>[0-9]+)/not_remind$', views.task_do_not_remind, name='not_remind$'),
    url(r'^(?P<pk>[0-9]+)/restore', views.task_restore, name='task_restore'),
    url(r'^task/new/$', views.task_new, name='task_new'),
    url(r'^task/new/(?P<project>[0-9]+)/$', views.task_new, name='project_task_new'),
    url(r'^accounts/', include('allauth.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) \
  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
