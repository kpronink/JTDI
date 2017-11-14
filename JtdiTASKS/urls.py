from django.conf.urls import url, include
from django.conf.urls.static import static

from . import views
from django.conf import settings
from django.contrib.auth import views as auth_views

urlpatterns = [
                  url(r'^get_push_notify/$', views.get_push_event, name='get_push_notify'),
                  url(r'^get_notify/$', views.get_notifycation, name='get_notify'),
                  url(r'^task/create/$', views.task_create, name='task_create'),
                  url(r'^project/create/$', views.project_create, name='project_create'),
                  url(r'^task/det/(?P<pk>[0-9]+)/$', views.task_detail_ajax, name='task_det'),
                  url(r'^task/(?P<pk>\d+)/update/$', views.task_update, name='task_update'),
                  url(r'^register/$', views.RegisterFormView.as_view(), name='register'),
                  url(r'^login/$', views.LoginFormView.as_view(), name='login'),
                  url(r'^ajax/validate_username/$', views.validate_username, name='validate_username'),
                  url(r'^ajax/get_recent_task/$', views.get_recent_task, name='get_recent_task'),
                  url(r'^ajax/get_index_project/(?P<pk>[0-9]+)/$', views.get_index_project, name='get_index_project'),
                  url(r'^ajax/get_index_tasks/$', views.get_index_tasks, name='get_index_tasks'),
                  url(r'^ajax/get_index_task/(?P<pk>[0-9]+)/$', views.get_index_task, name='get_index_task'),
                  url(r'^ajax/get_data_gantt/(?P<pk>[0-9]+)/$', views.get_data_gantt, name='get_data_gantt'),
                  url(r'^ajax/get_performers/(?P<pk>[0-9]+)/$', views.get_performers, name='get_performers'),
                  url(r'^logout/$', views.logout_view, name='logout'),
                  url(r'^profile/$', views.update_profile, name='profile'),
                  url(r'^invite/$', views.user_invite, name='user_invite'),
                  url(r'^invited/(?P<pk>[0-9]+)/$', views.invited, name='invited'),
                  url(r'^invite_in_proj/(?P<pk>[0-9]+)/$', views.invite_user_in_project, name='invite_in_proj'),
                  url(r'^del_user/(?P<user>[0-9]+)/(?P<project>[0-9]+)/$', views.delete_user_in_project, name='del_user'),
                  url(r'^not_invited/(?P<pk>[0-9]+)/$', views.not_invited, name='not_invited'),
                  url(r'^search/$', views.search_result, name='search'),
                  url(r'^tasks$', views.task_list, name='task_list'),
                  url(r'^task_finished/$', views.task_list_finished, name='task_list_finished'),
                  url(r'^$', views.task_list_today, name='task_today'),
                  url(r'^task_overdue/$', views.task_list_overdue, name='task_overdue'),
                  url(r'^project_tasks_list/(?P<pk>[0-9]+)/', views.project_task_list, name='project_tasks_list'),
                  # url(r'^task/(?P<pk>[0-9]+)/$', views.task_detail, name='task_detail'),
                  url(r'^task/(?P<pk>[0-9]+)/edit/$', views.task_edit, name='task_edit'),
                  url(r'^task/(?P<pk>[0-9]+)/del$', views.task_del, name='task_del'),
                  url(r'^task/(?P<pk>[0-9]+)/transfer_date/(?P<days>[0-9]+)', views.task_transfer_date,
                      name='transfer_date'),
                  url(r'^project/(?P<pk>[0-9]+)/del$', views.project_del, name='project_del'),
                  url(r'^project/(?P<pk>[0-9]+)/rename$', views.project_rename, name='project_rename'),
                  url(r'^project_param/(?P<pk>[0-9]+)/$', views.project_param, name='project_param'),
                  url(r'^(?P<pk>[0-9]+)/finish$', views.task_finish, name='task_finish'),
                  url(r'^task/(?P<pk>[0-9]+)/start_stop$', views.task_start_stop, name='task_start_stop'),
                  url(r'^task/(?P<pk>[0-9]+)/not_remind$', views.task_do_not_remind, name='not_remind$'),
                  url(r'^(?P<pk>[0-9]+)/restore', views.task_restore, name='task_restore'),
                  # url(r'^task/new/$', views.task_new, name='task_new'),
                  url(r'^add_comment/(?P<pk>[0-9]+)/$', views.add_comment, name='add_comment'),
                  url(r'^get_comments/(?P<pk>[0-9]+)/$', views.get_comments, name='get_comments'),
                  # url(r'^task/new/(?P<project>[0-9]+)/$', views.task_new, name='project_task_new'),
                  url(r'^accounts/', include('allauth.urls')),
                  url(r'^password_reset/$',
                      auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'),
                      {'post_reset_redirect': 'password_reset/done/'}, name="password_reset"),
                  url(r'^password_reset/done/$',
                      auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
                      name="password_reset_done"),
                  url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
                      auth_views.PasswordResetConfirmView.as_view(
                          template_name='registration/password_reset_confirm.html'),
                      {'post_reset_redirect': 'reset/done/'}, name="password_reset_confirm"),
                  url(r'^reset/done/$',
                      auth_views.PasswordResetCompleteView.as_view(
                          template_name='registration/password_reset_complete.html')
                      , name="password_reset_complete", )

              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) \
              + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
