import random

from allauth.socialaccount.models import SocialAccount
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType

from django.db.models import Q, Count, Sum
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
import datetime

from django.template.defaulttags import register
from django.template.loader import render_to_string
from django.templatetags.static import static

from .forms import TaskForm, TaskEditForm, UserProfileForm, UserForm, ProjectForm, SearchForm, InviteUserForm, \
    ProjectFormRename, ProjectInviteUser, CommentAddForm, MyUserCreationForm, KanbanColumnForm, NoteForm
from django.contrib.auth.forms import AuthenticationForm
from .models import Task, Project, User, InviteUser, PartnerGroup, TasksTimeTracker, CommentsTask, RegistrationTable, \
    ViewsEventsTable, QueueTask, QueuePushNotify, KanbanStatus, Notes
from django.contrib.auth import logout, login

from django.views.generic.edit import FormView
from qsstats import QuerySetStats

from django.utils.timezone import now, pytz


def generate_color():
    r = lambda: random.randint(0, 255)
    return '#%02X%02X%02X' % (r(), r(), r())


def local_time(dt, tz):
    if dt.tzinfo is None:
        dt = tz.localize(dt)
    return dt.astimezone(tz)


def get_tasks_with_filter(filter_method, project, user):
    global tasks, tasks_finish
    currentdate = datetime.datetime.today()
    start_day = currentdate.combine(currentdate, currentdate.min.time())
    end_day = currentdate.combine(currentdate, currentdate.max.time())
    yesterday = currentdate - datetime.timedelta(days=1)
    first_day = datetime.date(1001, 1, 1)

    if filter_method == 'projects':
        if project.author == user:
            tasks = Task.objects.filter(active=True).filter(project=project).order_by('date')

            tasks_finish = Task.objects.filter(active=False).filter(finished=True).filter(project=project.pk) \
                .filter(date_finish__range=(start_day, end_day)).order_by(
                'date_finish')
        else:
            users_in_project = PartnerGroup.objects.filter(project=project)

            all_users_in_project = User.objects.filter(
                Q(pk__in=[user.partner_id for user in users_in_project]) | Q(pk=project.author.pk)).values_list('id',
                                                                                                                flat=True)

            tasks = Task.objects.filter(active=True).filter(
                Q(author__in=all_users_in_project) | Q(performer__id__in=all_users_in_project)). \
                filter(project=project).order_by('date')

            tasks_finish = Task.objects.filter(active=False).filter(finished=True). \
                filter(Q(author=user) | Q(performer=user)).filter(project=project.pk) \
                .filter(date_finish__range=(start_day, end_day)).order_by(
                'date_finish')

    elif filter_method == 'today':
        tasks = Task.objects.filter(active=True).filter(Q(author=user) | Q(performer=user)) \
            .filter(date_time__range=(start_day, end_day)) \
            .order_by('date', 'priority', 'time')
        tasks_finish = Task.objects.filter(active=False).filter(finished=True) \
            .filter(Q(author=user) | Q(performer=user)) \
            .filter(date_finish__range=(start_day, end_day)).order_by(
            'date_finish')
    elif filter_method == 'overdue':
        tasks = Task.objects.filter(active=True).filter(Q(author=user) | Q(performer=user)) \
            .filter(planed_date_finish__range=(first_day, yesterday)) \
            .order_by('date', 'priority', 'time')
        tasks_finish = Task.objects.filter(active=False).filter(finished=True) \
            .filter(Q(author=user) | Q(performer=user)). \
            filter(project=None).filter(date_finish__range=(start_day, end_day)).order_by(
            'date_finish')
    elif filter_method == 'tasks':
        tasks = Task.objects.filter(active=True).filter(Q(author=user) | Q(performer=user)) \
            .filter(project=None). \
            order_by('date', 'priority', 'time')
        tasks_finish = Task.objects.filter(active=False).filter(finished=True) \
            .filter(Q(author=user) | Q(performer=user)).filter(date_finish__range=(start_day, end_day)).order_by(
            'date_finish')

    return tasks, tasks_finish


def register_event(event_object, user, project, event_desc):
    local_timez = pytz.timezone(user.profile.timezone)
    dt = datetime.datetime.now().astimezone(local_timez)

    users_in_project = PartnerGroup.objects.filter(project=project)

    content_type = ContentType.objects.get_for_model(event_object)
    model_class = content_type.model_class()

    if project is not None and model_class == Project:
        all_users = User.objects.filter(
            Q(pk__in=[user.partner_id for user in users_in_project]) | Q(pk=project.author.pk))
    elif project is not None and model_class == Task:
        all_users = list()
        all_users.append(event_object.performer)
        if event_object.performer != event_object.author:
            all_users.append(event_object.author)
    else:
        all_users = list()
        if model_class == InviteUser:
            all_users.append(event_object.user_invite)
            all_users.append(event_object.user_sender)

    event = RegistrationTable(author=user, project=project)
    event.content_type = content_type
    event.object_id = event_object.pk
    event.date = dt
    event.date_time = dt
    event.event = event_desc
    event.save()

    for user_proj in all_users:
        sees = ViewsEventsTable()
        sees.user = user_proj
        sees.event = event
        sees.sees = False
        sees.save()


def get_event(user, request):
    projects = list(
        PartnerGroup.objects.filter(partner=user).values_list('project', flat=True))
    project_owner = list(Project.objects.filter(author=user).values_list('pk', flat=True))
    projects.extend(project_owner)
    events = ViewsEventsTable.objects.filter(sees=False).filter(user=user).filter(Q(
        event__project_id__in=projects) | Q(event__project=None)).order_by('id').reverse()[:10]
    count_notify = events.count()
    if not count_notify:
        events = ViewsEventsTable.objects.filter(sees=True).filter(user=user).filter(Q(
            event__project_id__in=projects) | Q(event__project=None)).order_by('id').reverse()[:10]
        count_notify = 0

    tasks = list()
    for event in events:
        model = event.event.content_type.model_class()
        event_obj = get_object_or_404(ViewsEventsTable, pk=event.pk)
        event_obj.sees = True
        event_obj.save()
        if model == Task:
            try:
                object_model = get_object_or_404(model, pk=event.event.object_id)
            except:
                continue
            if 'прокомментировал' in event.event.event:
                ico = 'fa fa-comment fa-fw'
            elif 'создал' in event.event.event or 'изменил' in event.event.event:
                ico = 'fa fa-tasks fa-fw'
            else:
                ico = 'fa fa-tasks fa-fw'
            tasks.append({'msg': event.event.author.username + ' ' + event.event.event + object_model.title,
                          'url': '/task/det/' + str(object_model.pk) + '/',
                          'time': event.event.date_time.strftime('%H:%M'),
                          'ico': ico})
        elif model == PartnerGroup:
            try:
                object_model = get_object_or_404(PartnerGroup, pk=event.event.object_id)
            except:
                continue
            ico = 'fa fa-user fa-fw'
            tasks.append({'msg': event.event.author.username + ' ' + event.event.event + object_model.partner.username,
                          'url': '',
                          'time': event.event.date_time.strftime('%H:%M'),
                          'ico': ico})
        elif model == InviteUser:
            try:
                object_model = get_object_or_404(InviteUser, pk=event.event.object_id)
            except:
                continue
            ico = 'fa fa-user fa-fw'
            tasks.append(
                {'msg': object_model.user_sender.username + ' ' + event.event.event + object_model.user_invite.username,
                 'url': '/invite/',
                 'time': event.event.date_time.strftime('%H:%M'),
                 'ico': ico})

    notify_tasks = render_to_string('JtdiTASKS/menu/notify_menu.html',
                                    {'tasks': tasks},
                                    request=request
                                    )

    return notify_tasks, str(count_notify)


def get_push_event(request):
    if not request.user.is_authenticated():
        return JsonResponse({})

    data = dict()
    currentdate = datetime.datetime.today()
    start_day = currentdate.combine(currentdate, currentdate.min.time())
    local_timez = pytz.timezone(request.user.profile.timezone)
    dt = datetime.datetime.now().astimezone(local_timez)

    tasks_today = QueueTask.objects.filter(reminded=False).filter(user=request.user) \
        .filter(date_time__range=(start_day, dt.replace(tzinfo=pytz.timezone('UTC')))) \
        .order_by('date_time').reverse()
    count = 0
    for task_actual in tasks_today:
        data[str(count)] = {'title': task_actual.task.title,
                            'url': '/task/det/' + str(task_actual.task.pk) + '/',
                            'body': task_actual.task.description}
        count += 1
        reminder = get_object_or_404(QueueTask, pk=task_actual.pk)
        reminder.reminded = True
        reminder.save()

    other_notify = QueuePushNotify.objects.filter(reminded=False).filter(user=request.user) \
        .filter(date_time__range=(start_day, dt.replace(tzinfo=pytz.timezone('UTC')))) \
        .order_by('date_time').reverse()
    for noti in other_notify:
        data[str(count)] = {'title': request.user.username,
                            'url': noti.url,
                            'body': noti.event}
        count += 1
        reminder = get_object_or_404(QueuePushNotify, pk=noti.pk)
        reminder.reminded = True
        reminder.save()

    return JsonResponse(data)


# KANBAN +


def create_first_canban_status(user, project, title):
    kanban_first_column = KanbanStatus()
    kanban_first_column.project = project
    kanban_first_column.author = user
    kanban_first_column.color = generate_color()
    kanban_first_column.title = title
    kanban_first_column.save()

    return kanban_first_column


def get_kanban(request, pk):
    if not request.user.is_authenticated():
        return JsonResponse({})

    data = dict()
    kanban = dict()

    project = Project.objects.filter(pk=pk)[0]
    kanban_status = KanbanStatus.objects.filter(project=project)
    if not kanban_status.__len__():
        kanban_column = create_first_canban_status(request.user, project, 'Запрос')
        kanban_status = list()
        kanban_status.append(kanban_column)
    tasks, tasks_finish = get_tasks_with_filter('projects', project, request.user)
    for status in kanban_status:
        kanban[status] = []
        for task in tasks:
            if task.kanban_status == status:
                kanban[status].append(task)
            elif task.kanban_status is None and status.title == 'Запрос':
                kanban[status].append(task)

    data['kanban'] = render_to_string('JtdiTASKS/ajax_views/kanban.html',
                                      {'kanban': kanban},
                                      request=request
                                      )

    return JsonResponse(data)


def add_kanban_column(request, pk):
    if not request.user.is_authenticated():
        return JsonResponse({})

    data = dict()
    if request.method == 'POST':
        form = KanbanColumnForm(request.POST)
        if form.is_valid():
            project = Project.objects.filter(pk=pk)[0]
            kanban_column = create_first_canban_status(request.user, project, form.cleaned_data['title'])
            data['new_column'] = render_to_string('JtdiTASKS/ajax_views/kanban_column.html',
                                                  {'kanban_column': kanban_column},
                                                  request=request
                                                  )
            data['form_is_valid'] = True
    else:
        form = KanbanColumnForm()
        data['kanban_column_form'] = render_to_string('JtdiTASKS/ajax_views/new_kanban_column.html',
                                                      {'add_kanban_column_form': form,
                                                       'project': pk},
                                                      request=request
                                                      )

    return JsonResponse(data)


def change_kanban_status(request):
    if not request.user.is_authenticated():
        return JsonResponse({})

    data = dict()

    task_pk = request.POST['task_pk']
    status_kanban_pk = request.POST['status_kanban_pk']
    
    task = get_object_or_404(Task, pk=task_pk)
    status_kanban = get_object_or_404(KanbanStatus, pk=status_kanban_pk)
    
    task.kanban_status = status_kanban
    task.save()

    return JsonResponse(data)


def add_kanban_task(request, pk):
    if not request.user.is_authenticated():
        return JsonResponse({})

    data = dict()

    data['new_task'] = render_to_string('JtdiTASKS/ajax_views/kanban_task.html',
                                        request=request
                                        )

    return JsonResponse(data)


# KANBAN -


class RegisterFormView(FormView):
    form_class = MyUserCreationForm

    # Ссылка, на которую будет перенаправляться пользователь в случае успешной регистрации.
    # В данном случае указана ссылка на страницу входа для зарегистрированных пользователей.
    success_url = "/login/"

    # Шаблон, который будет использоваться при отображении представления.
    template_name = "JtdiTASKS/views/registration.html"

    def form_valid(self, form):
        # Создаём пользователя, если данные в форму были введены корректно.
        form.save()

        # Вызываем метод базового класса
        return super(RegisterFormView, self).form_valid(form)


class LoginFormView(FormView):
    form_class = AuthenticationForm

    # Аналогично регистрации, только используем шаблон аутентификации.
    template_name = "JtdiTASKS/views/login.html"

    # В случае успеха перенаправим на главную.
    success_url = "/"

    def form_valid(self, form):
        # Получаем объект пользователя на основе введённых в форму данных.
        self.user = form.get_user()

        # Выполняем аутентификацию пользователя.
        login(self.request, self.user)
        return super(LoginFormView, self).form_valid(form)


# NOTIFY +

def get_notifycation(request):
    if not request.user.is_authenticated():
        return JsonResponse({'msg': 'пользователь не авторизован'})

    data = dict()
    currentdate = datetime.datetime.today()
    start_day = currentdate.combine(currentdate, currentdate.min.time())
    end_day = currentdate.combine(currentdate, currentdate.max.time())
    first_day = currentdate
    first_day = first_day.combine(datetime.date(1001, 1, 1), currentdate.min.time())
    yesterday = currentdate - datetime.timedelta(days=1)

    tasks_today_notify = Task.objects.filter(active=True).filter(author=request.user) \
        .filter(date_time__range=(start_day, end_day)) \
        .order_by('date', 'priority', 'time').count()
    tasks_overdue_notify = Task.objects.filter(active=True).filter(author=request.user) \
        .filter(planed_date_finish__range=(first_day, yesterday)) \
        .order_by('date', 'priority', 'time').count()

    data['tasks_today_notify'] = tasks_today_notify
    data['tasks_overdue_notify'] = tasks_overdue_notify

    data['notify_tasks'], data['count_notify'] = get_event(request.user, request)

    return JsonResponse(data)


def get_notify_list(request):
    if not request.user.is_authenticated():
        return JsonResponse({'msg': 'пользователь не авторизован'})

    data = dict()
    data['notify_tasks'], data['count_notify'] = get_event(request.user, request)

    return JsonResponse(data)


def get_recent_task(request):
    if request.user.is_authenticated():
        today_min = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
        today_max = datetime.datetime.combine(datetime.date.today(), datetime.time.max)
        tasks_alert = Task.objects.filter(active=True).filter(author=request.user).filter(project=None).filter(
            remind=True) \
            .filter(time__range=(today_min, today_max)).order_by('date')
        data = {}
        for task in tasks_alert:
            data['/task/' + str(task.pk) + '/'] = task.title

    else:

        data = {

        }

    return JsonResponse(data)

# NOTIFY -


# DIAGRAMS +

def get_index_of_task(request, pk):
    local_timez = pytz.timezone(request.user.profile.timezone)

    currentdate = datetime.datetime.today()
    start_day = currentdate.combine(currentdate, currentdate.min.time())
    end_day = currentdate.combine(currentdate, currentdate.max.time())
    tasks = Task.objects.filter(pk=pk)
    tasks_time_tracking = TasksTimeTracker.objects.filter(task=tasks).filter(
        datetime__range=(start_day, end_day)).order_by('datetime')
    qsstats = QuerySetStats(tasks_time_tracking, date_field='datetime')
    # ...в день за указанный период
    values = qsstats.time_series(start_day, end_day, interval='hours')
    data = []

    for val in values:
        time_work = 0
        for traker in tasks_time_tracking:
            if traker.full_time is None:
                continue
            if traker.start.hour == val[0].hour or traker.finish.hour == val[0].hour:
                time_work = traker.full_time
        dt = val[0].astimezone(local_timez)
        data.append({'y': dt.strftime("%H:%M"),
                     'a': time_work})

    return data


def get_index_project(request, pk):
    tasks_total = 0
    tasks_finished = 0
    all_users_in_project = 0
    if request.user.is_authenticated():
        proj = get_object_or_404(Project, pk=pk)
        tasks_total = Task.objects.filter().filter(Q(author=request.user) | Q(performer=request.user)) \
            .filter(project=proj).order_by('date').count()
        tasks_finished = Task.objects.filter(finished=True).filter(author=request.user).filter(project=proj).order_by(
            'date').count()

        users_in_project = PartnerGroup.objects.filter(project=proj)
        all_users_in_project = User.objects.filter(
            Q(pk__in=[user.partner_id for user in users_in_project]) | Q(pk=proj.author.pk)).count()

    return JsonResponse(
        [{'label': 'Всего задач', 'value': tasks_total}, {'label': 'Задач завершено', 'value': tasks_finished},
         {'label': 'Участников проекта', 'value': all_users_in_project}], safe=False)


def get_index_tasks(request):
    if request.user.is_authenticated():
        today = datetime.date.today()
        week_end = today - datetime.timedelta(days=7)
        tasks_finish_base = Task.objects.filter(active=False).filter(finished=True).filter(author=request.user).filter(
            date_finish__range=(week_end, today)).order_by(
            'date_finish')
        tasks_create = Task.objects.filter(author=request.user).filter(
            date__range=(week_end, today)).order_by(
            'date')
        qsstats = QuerySetStats(tasks_finish_base, date_field='date_finish', aggregate=Count('id'))
        qsstats2 = QuerySetStats(tasks_create, date_field='date', aggregate=Count('id'))

        # ...в день за указанный период
        data = []
        values = qsstats.time_series(week_end, today, interval='days')
        values2 = qsstats2.time_series(week_end, today, interval='days')
        count = 0
        for val in values:
            data.append({'y': str(val[0].day) + '.' + str(val[0].month),
                         'b': values2[count][1],
                         'a': val[1]})
            count += 1
    return JsonResponse(data, safe=False)


def get_index_task(request, pk):
    if request.user.is_authenticated():
        data = get_index_of_task(request, pk)

    return JsonResponse(data, safe=False)


def get_data_gantt(request, pk):
    if request.user.is_authenticated():
        proj = get_object_or_404(Project, pk=pk)

        tasks = Task.objects.filter(project=proj).filter(finished=False).order_by('date_finish') \
            .order_by('performer').order_by('date')

        # ...в день за указанный период
        data = []
        count = 0

        for val in tasks:
            if val.planed_date_finish is None:
                plane_date_finish = val.date + datetime.timedelta(days=3)
            else:
                plane_date_finish = val.planed_date_finish

            if val.date_finish is None:
                date_finish = datetime.date.today()
            else:
                date_finish = val.date_finish

            data.append({'id': count + 1, 'name': val.title[:15], 'series': []})
            data[count]['series'] = (
                {'name': 'Планируемая', 'start': val.date, 'end': plane_date_finish, 'color': "#e96562",
                 'url': redirect('task_edit', pk=val.pk).url},
                {'name': 'Актуальная', 'start': val.date, 'end': date_finish, 'color': "#414e63",
                 'url': redirect('task_edit', pk=val.pk).url})
            count += 1
        return JsonResponse(data, safe=False)

# DIAGRAMS -


def get_performers(request, pk):
    data = []
    # invited_users = InviteUser \
    #     .objects.filter(Q(user_sender__username__exact=request.user.username)
    #                     | Q(user_invite__username__exact=request.user.username)) \
    #     .filter(not_invited=False).filter(invited=True)
    project = get_object_or_404(Project, pk=pk)
    users_in_project = PartnerGroup.objects.filter(project=project) \
        # .filter(partner_id__in=[user.user_invite.pk for user in invited_users])
    performers = User.objects.filter(
        Q(pk__in=[user.partner_id for user in users_in_project]) | Q(pk=project.author.pk))

    data.append({'': '---------'})
    for performer in performers:
        data.append([str(performer.pk), str(performer.username)])

    return JsonResponse(data, safe=False)


def validate_username(request):
    username = request.GET.get('username', None)
    data = {
        'is_taken': User.objects.filter(username__iexact=username).exists()
    }
    if not data['is_taken']:
        data['error_message'] = 'Пользователя с таким именем не существует'
    return JsonResponse(data)


# VIEWS +

def logout_view(request):
    logout(request)
    return redirect('login')


def update_profile(request):
    soc_acc = SocialAccount.objects.filter(user=request.user)
    task_with_full_time = []
    tasks = Task.objects.filter(performer=request.user)
    for task in tasks:
        full_time = TasksTimeTracker.objects.filter(task__id=task.id).aggregate(Sum('full_time'))
        task_with_full_time.append([task, full_time])
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Ваш профиль успешно обновлен!')
            return redirect('profile')
        else:
            messages.error(request, 'Пожалуйста исправьте ошибки.')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=request.user.profile)
    return render(request, 'JtdiTASKS/views/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'accounts': soc_acc,
        'task_time': task_with_full_time,
    })


def task_list(request):
    if not request.user.is_authenticated():
        return redirect('login')

    currentdate = datetime.datetime.today()
    start_day = currentdate.combine(currentdate, currentdate.min.time())
    end_day = currentdate.combine(currentdate, currentdate.max.time())

    tasks = Task.objects.filter(active=True).filter(Q(author=request.user) | Q(performer=request.user)) \
        .filter(project=None). \
        order_by('date', 'priority', 'time')
    tasks_finish = Task.objects.filter(active=False).filter(finished=True) \
        .filter(Q(author=request.user) | Q(performer=request.user)).order_by(
        'date_finish')
    tasks_finished_today = Task.objects.filter(active=False).filter(finished=True) \
        .filter(Q(author=request.user) | Q(performer=request.user)) \
        .filter(date_finish__range=(start_day, end_day)).order_by(
        'date_finish')

    return render(request, 'JtdiTASKS/views/index.html', {'tasks': tasks,
                                                          'tasks_finish': tasks_finish,
                                                          'tasks_finished_today': tasks_finished_today})


def task_list_today(request):
    if not request.user.is_authenticated():
        return redirect('login')

    currentdate = datetime.datetime.today()
    start_day = currentdate.combine(currentdate, currentdate.min.time())
    end_day = currentdate.combine(currentdate, currentdate.max.time())

    tasks = Task.objects.filter(active=True).filter(Q(author=request.user) | Q(performer=request.user)) \
        .filter(date_time__range=(start_day, end_day)) \
        .order_by('date', 'priority', 'time')
    tasks_finish = Task.objects.filter(active=False).filter(finished=True) \
        .filter(Q(author=request.user) | Q(performer=request.user)).order_by(
        'date_finish')
    tasks_finished_today = Task.objects.filter(active=False).filter(finished=True) \
        .filter(Q(author=request.user) | Q(performer=request.user)) \
        .filter(date_finish__range=(start_day, end_day)).order_by(
        'date_finish')

    return render(request, 'JtdiTASKS/views/task_today.html', {'tasks': tasks,
                                                               'tasks_finish': tasks_finish,
                                                               'tasks_finished_today': tasks_finished_today})


def task_list_overdue(request):
    if not request.user.is_authenticated():
        return redirect('login')

    currentdate = datetime.datetime.today()
    start_day = currentdate.combine(currentdate, currentdate.min.time())
    end_day = currentdate.combine(currentdate, currentdate.max.time())
    next_day = currentdate + datetime.timedelta(days=1)
    first_day = datetime.date(1001, 1, 1)
    yesterday = currentdate - datetime.timedelta(days=1)

    tasks = Task.objects.filter(active=True).filter(Q(author=request.user) | Q(performer=request.user)) \
        .filter(planed_date_finish__range=(first_day, yesterday)) \
        .order_by('date', 'priority', 'time')
    tasks_finish = Task.objects.filter(active=False).filter(finished=True) \
        .filter(Q(author=request.user) | Q(performer=request.user)). \
        filter(project=None).order_by(
        'date_finish')
    tasks_finished_today = Task.objects.filter(active=False).filter(finished=True) \
        .filter(Q(author=request.user) | Q(performer=request.user)). \
        filter(project=None).filter(date_finish__range=(start_day, end_day)).order_by(
        'date_finish')

    return render(request, 'JtdiTASKS/views/task_overdue.html', {'tasks': tasks,
                                                                 'tasks_finish': tasks_finish,
                                                                 'tasks_finished_today': tasks_finished_today})


def task_list_finished(request):
    if not request.user.is_authenticated():
        return redirect('login')

    tasks_finish = Task.objects.filter(active=False).filter(finished=True) \
        .filter(Q(author=request.user) | Q(performer=request.user)).order_by(
        'project').order_by('date_finish')

    return render(request, 'JtdiTASKS/views/finished_task.html', {'tasks': tasks_finish})


def project_task_list(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    project = Project.objects.filter(pk=pk)[0]

    tasks, tasks_finish = get_tasks_with_filter('projects', project, request.user)

    users_in_project = PartnerGroup.objects.filter(project=project)

    all_users_in_project = User.objects.filter(
        Q(pk__in=[user.partner_id for user in users_in_project]) | Q(pk=project.author.pk))

    all_users_task_count = []
    for user_in_proj in all_users_in_project:
        all_users_task_count.append({'user': user_in_proj
                                        , 'task_count': Task.objects.filter(project=project)
                                    .filter(Q(author=user_in_proj) | Q(performer=user_in_proj))
                                    .filter(active=True).filter(finished=False).count()})

    return render(request, 'JtdiTASKS/views/project_task_list.html', {'tasks': tasks,
                                                                      'tasks_finish': tasks_finish,
                                                                      'project': pk,
                                                                      'project_object': project,
                                                                      'users_in_project': all_users_task_count})


def search_result(request):
    if not request.user.is_authenticated():
        return redirect('login')

    search_str = request.GET['search_field']
    search_str = search_str.replace('.', ' ')
    search_str_split = search_str.split(' ')
    search_result_data = []
    for item in search_str_split:
        search_result_data = Task.objects.filter(Q(title__contains=item) |
                                                 Q(description__contains=item)) \
            .filter(Q(author=request.user) | Q(performer=request.user)) \
            .order_by(
            '-date_finish')

    return render(request, 'JtdiTASKS/views/search.html', {'search_result_data': search_result_data})


def notes_list(request):
    if not request.user.is_authenticated():
        return redirect('login')

    notes = Notes.objects.filter(author=request.user).order_by('title')

    return render(request, 'JtdiTASKS/views/notes_list.html', {'notes': notes})

# VIEWS -


# TASKS +


def task_create(request):
    if not request.user.is_authenticated():
        return {'login':False}

    data = dict()

    user = get_object_or_404(User, pk=request.user.pk)

    if 'param' in request.POST:
        method = request.POST['param']
    elif 'param' in request.GET:
        method = request.GET['param']
    else:
        method = 'projects'

    if method == 'projects':
        if 'project_param' in request.POST:
            project_pk = int(request.POST['project_param'])
        elif 'project_param' in request.GET:
            project_pk = int(request.GET['project_param'])
    else:
        project_pk = None

    COLOR_CHOISE = {
        1: 'red',
        2: 'yellow',
        3: 'green',
        4: 'grey'}

    invited_users = InviteUser \
        .objects.filter(Q(user_sender__username__exact=user.username)
                        | Q(user_invite__username__exact=user.username)) \
        .filter(not_invited=False).filter(invited=True)

    users_in_project = PartnerGroup.objects.filter(project=project_pk)
    # .filter(partner_id__in=[user.user_invite.pk for user in invited_users])

    projects = list(
        PartnerGroup.objects.filter(partner=user).values_list('project', flat=True))
    project_owner = list(Project.objects.filter(author=user).values_list('pk', flat=True))
    projects.extend(project_owner)

    proj = None

    if project_pk is not None:
        proj = get_object_or_404(Project, pk=project_pk)
        all_users_in_project = User.objects.filter(
            Q(pk__in=[user.partner_id for user in users_in_project]) | Q(pk=proj.author.pk))
    else:
        users_in_project = PartnerGroup.objects.filter(partner_id__in=[user.user_invite.pk for user in invited_users])
        all_users_in_project = User.objects \
            .filter(Q(pk__in=[user.partner_id for user in users_in_project]) | Q(pk=user.pk))

    if request.method == 'POST':
        form = TaskForm(request.POST)
        form.fields['project_field'].queryset = Project.objects.filter(Q(author=user) | Q(pk__in=projects))
        form.fields['performer'].queryset = all_users_in_project
        if form.is_valid():
            task = Task()
            task.title = form.cleaned_data['title']
            task.description = form.cleaned_data['description']
            task.date = form.cleaned_data['date']
            task.time = datetime.datetime.combine(task.date, form.cleaned_data['time_field'])
            task.planed_date_finish = form.cleaned_data['date_planed']
            task.date_time = task.time
            task.author = request.user
            if proj is not None:
                task.project = proj
            else:
                task.project = form.cleaned_data['project_field']
            if form.cleaned_data['performer'] is not None:
                task.performer = form.cleaned_data['performer']
            else:
                task.performer = task.author
            task.active = True
            task.repeating = form.cleaned_data['repeating']
            task.remind = form.cleaned_data['remind']
            task.priority = form.cleaned_data['priority_field']
            task.color = COLOR_CHOISE[int(task.priority)]
            task.remind = False
            task.save(Task)

            if not task.remind:
                reminder = QueueTask(user=request.user, task=task, reminded=False, date_time=task.date_time)
                reminder.save()

            if task.project is not None:
                register_event(task, request.user, task.project, 'создал задачу:')

            tasks, tasks_finish = get_tasks_with_filter(method, task.project, user)
            data['form_is_valid'] = True
            data['html_active_tasks_list'] = render_to_string('JtdiTASKS/ajax_views/task_table_body.html', {
                'tasks': tasks
            })
        else:
            data['form_is_valid'] = False
    else:
        form = TaskForm(initial={'project_field': proj, 'performer': user})
        form.fields['project_field'].queryset = Project.objects.filter(Q(author=user) | Q(
            pk__in=PartnerGroup.objects.filter(partner=user).values_list('project', flat=True)))
        form.fields['performer'].queryset = all_users_in_project

    context = {'form': form}
    data['html_form'] = render_to_string('JtdiTASKS/ajax_views/task_create_ajax.html',
                                         context,
                                         request=request
                                         )
    return JsonResponse(data)


def task_detail_ajax(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    data = dict()

    task = get_object_or_404(Task, pk=pk)
    full_time = TasksTimeTracker.objects.filter(task__pk=pk).aggregate(Sum('full_time'))
    comment_form = CommentAddForm()

    context = {'task': task,
               'comment_form': comment_form,
               'full_time': full_time['full_time__sum']}
    data['html_form'] = render_to_string('JtdiTASKS/ajax_views/task_detail_ajax.html',
                                         context,
                                         request=request
                                         )
    return JsonResponse(data)


def task_update(request, pk):
    if not request.user.is_authenticated():
        return {'login':False}

    data = dict()

    if 'param' in request.POST:
        method = request.POST['param']
    elif 'param' in request.GET:
        method = request.GET['param']
    else:
        method = 'projects'

    project_pk = None
    task = get_object_or_404(Task, pk=pk)
    if task.author != request.user:
        return redirect('task_detail', pk=task.pk)
    if task.project is not None:
        project_pk = task.project.pk

    COLOR_CHOISE = {
        1: 'red',
        2: 'yellow',
        3: 'green',
        4: 'grey'}

    invited_users = InviteUser \
        .objects.filter(Q(user_sender__username__exact=request.user.username)
                        | Q(user_invite__username__exact=request.user.username)) \
        .filter(not_invited=False).filter(invited=True)

    users_in_project = PartnerGroup.objects.filter(project=project_pk)

    projects = list(
        PartnerGroup.objects.filter(partner=request.user).values_list('project', flat=True))
    project_owner = list(Project.objects.filter(author=request.user).values_list('pk', flat=True))
    projects.extend(project_owner)

    if project_pk is not None:
        proj = get_object_or_404(Project, pk=project_pk)
        all_users_in_project = User.objects.filter(
            Q(pk__in=[user.partner_id for user in users_in_project]) | Q(pk=proj.author.pk))
    else:
        users_in_project = PartnerGroup.objects.filter(partner_id__in=[user.user_invite.pk for user in invited_users])
        all_users_in_project = User.objects \
            .filter(Q(pk__in=[user.partner_id for user in users_in_project]) | Q(pk=request.user.pk))

    if request.method == "POST":
        if task.author == request.user:
            form = TaskEditForm(request.POST, instance=task)
            form.fields['project'].queryset = Project.objects.filter(Q(author=request.user) | Q(pk__in=projects))
            form.fields['performer'].queryset = all_users_in_project
            if form.is_valid():
                task = form.save(commit=False)
                task.author = request.user
                task.active = True
                if task.priority is not None:
                    task.color = COLOR_CHOISE[int(task.priority)]
                else:
                    task.color = COLOR_CHOISE[4]
                task.date_time = task.date_time.combine(task.date, task.time)
                task.save()
                if task.project is not None:
                    register_event(task, request.user, task.project, 'изменил задачу:')

                tasks, tasks_finish = get_tasks_with_filter(method, task.project, request.user)
                data['form_is_valid'] = True
                data['msg'] = 'Задача успешно обновлена'
                data['html_active_tasks_list'] = render_to_string('JtdiTASKS/ajax_views/task_table_body.html', {
                    'tasks': tasks
                })
                if not task.remind:
                    reminders = QueueTask.objects.filter(task=task).filter(user=request.user)
                    if reminders.count():
                        reminder = get_object_or_404(QueueTask, pk=reminders[0].pk)
                        reminder.reminded = False
                        reminder.date_time = task.date_time
                        reminder.save()
                    else:
                        reminder = QueueTask(user=request.user, task=task, reminded=False, date_time=task.date_time)
                        reminder.save()

    else:
        form = TaskEditForm(instance=task)
        form.fields['project'].queryset = Project.objects.filter(Q(author=request.user) | Q(
            pk__in=projects))
        form.fields['performer'].queryset = all_users_in_project
        data['msg'] = ''

    context = {'form': form,
               'task': task}
    data['html_form'] = render_to_string('JtdiTASKS/ajax_views/task_edit_ajax.html',
                                         context,
                                         request=request
                                         )
    return JsonResponse(data)

# TASKS -


# NOTES +

def note_create(request, pk):
    if not request.user.is_authenticated():
        return {'login': False}

    data = dict()

    user = get_object_or_404(User, pk=request.user.pk)
    note = None
    if pk != '0':
        note = get_object_or_404(Notes, pk=pk)

    if request.method == 'POST':
        if note is not None:
            form = NoteForm(request.POST, instance=note)
        else:
            form = NoteForm(request.POST)

        if form.is_valid():
            if note is not None:
                note = form.save(commit=False)
                note.save()
            else:
                note = Notes()
                note.title = form.cleaned_data['title']
                note.description = form.cleaned_data['description']
                note.author = user
                note.save(Notes)

            data['form_is_valid'] = True
            data['html_active_notes_list'] = render_to_string('JtdiTASKS/ajax_views/notes_table_body.html', {
                'notes': Notes.objects.filter(author=request.user).order_by('title')
            })
        else:
            data['form_is_valid'] = False
    else:
        if note is not None:
            form = NoteForm(instance=note)
        else:
            form = NoteForm()

    context = {'form': form,
               'pk': pk}
    data['html_form'] = render_to_string('JtdiTASKS/ajax_views/note_ajax.html',
                                         context,
                                         request=request
                                         )
    return JsonResponse(data)


def note_del(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    data = dict()

    note = get_object_or_404(Notes, pk=pk)
    if note.author == request.user:
        note.delete()

        data['form_is_valid'] = True
        data['html_active_notes_list'] = render_to_string('JtdiTASKS/ajax_views/notes_table_body.html', {
            'notes': Notes.objects.filter(author=request.user).order_by('title')})

    return JsonResponse(data)

# NOTES -


# def task_copy(request, pk):



# def task_edit(request, pk):
#     if not request.user.is_authenticated():
#         return redirect('login')
#
#     COLOR_CHOISE = {
#         1: 'red',
#         2: 'yellow',
#         3: 'green',
#         4: 'grey'}
#
#     invited_users = InviteUser \
#         .objects.filter(Q(user_sender__username__exact=request.user.username)
#                         | Q(user_invite__username__exact=request.user.username)) \
#         .filter(not_invited=False).filter(invited=True)
#
#     users_in_project = PartnerGroup.objects.filter(partner_id__in=[user.user_invite.pk for user in invited_users])
#     all_users_in_project = User.objects.filter(
#         Q(pk__in=[user.partner_id for user in users_in_project]) | Q(pk=request.user.pk))
#
#     task = get_object_or_404(Task, pk=pk)
#     if task.author != request.user:
#         return redirect('task_detail', pk=task.pk)
#
#     if request.method == "POST":
#         if task.author == request.user:
#             form = TaskEditForm(request.POST, instance=task)
#             form.fields['project'].queryset = Project.objects.filter(author=request.user)
#             form.fields['performer'].queryset = all_users_in_project
#             if form.is_valid():
#                 task = form.save(commit=False)
#                 task.author = request.user
#                 task.active = True
#                 if task.priority is not None:
#                     task.color = COLOR_CHOISE[int(task.priority)]
#                 else:
#                     task.color = COLOR_CHOISE[4]
#                 task.date_time = task.date_time.combine(task.date, task.time)
#                 task.save()
#                 return redirect('task_detail', pk=task.pk)
#     else:
#         form = TaskEditForm(instance=task)
#         form.fields['project'].queryset = Project.objects.filter(author=request.user)
#         form.fields['performer'].queryset = all_users_in_project
#
#     return render(request, 'JtdiTASKS/views/task_edit.html', {'form': form
#                                                               })



def task_del(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    data = dict()

    method = request.POST['param']

    task = get_object_or_404(Task, pk=pk)
    if task.author == request.user:
        task.delete()

        tasks, tasks_finish = get_tasks_with_filter(method, task.project, request.user)
        data['form_is_valid'] = True
        data['html_finished_tasks_list'] = render_to_string('JtdiTASKS/ajax_views/task_table_body_finished.html', {
            'tasks_finish': tasks_finish})
        data['html_active_tasks_list'] = render_to_string('JtdiTASKS/ajax_views/task_table_body.html', {
            'tasks': tasks})

    return JsonResponse(data)


def task_start_stop(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    local_timez = pytz.timezone(request.user.profile.timezone)
    dt = datetime.datetime.now().astimezone(local_timez)
    task = get_object_or_404(Task, pk=pk)
    if task.author == request.user or task.performer == request.user:
        time_tracker = TasksTimeTracker.objects.filter(task=task).order_by('-datetime')[:1]
        if time_tracker.count():
            if time_tracker[0].finish is None:
                time_tracker = get_object_or_404(TasksTimeTracker, pk=time_tracker[0].pk)
                time_tracker.finish = datetime.datetime.now().astimezone(local_timez)
                time_tracker.full_time = (time_tracker.finish - time_tracker.start).seconds / 60
            else:
                time_tracker = TasksTimeTracker()
                time_tracker.task = task
                time_tracker.datetime = dt
                time_tracker.start = dt
        else:
            time_tracker = TasksTimeTracker()
            time_tracker.task = task
            time_tracker.datetime = dt
            time_tracker.start = dt

        time_tracker.save()
        if task.status == "Wait":
            task.status = "Started"
            msg = 'Задача успешно запущена'
            if task.project is not None:
                register_event(task, request.user, task.project, 'начал выполнять задачу:')
        elif task.status == "Started":
            task.status = "Stoped"
            msg = 'Задача успешно приостановлена'
            if task.project is not None:
                register_event(task, request.user, task.project, 'приостановил выполнение задачи:')
        elif task.status == "Stoped":
            task.status = "Started"
            msg = 'Задача успешно запущена'
            if task.project is not None:
                register_event(task, request.user, task.project, 'начал выполнять задачу:')
        task.save()

    tasks_time_tracking = TasksTimeTracker.objects.filter(task=task).order_by('datetime').aggregate(Sum('full_time'))

    return JsonResponse({'status': task.status, 'full_time': tasks_time_tracking['full_time__sum'], 'msg': msg})


def task_finish(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    data = dict()

    method = request.POST['param']

    task = get_object_or_404(Task, pk=pk)
    if task.author == request.user or task.performer == request.user:
        task.finished = True
        task.active = False
        task.date_finish = datetime.datetime.today()
        task.date_time_finish = datetime.datetime.today()
        task.status = 'Finished'
        task.save()
        tasks, tasks_finish = get_tasks_with_filter(method, task.project, request.user)
        data['form_is_valid'] = True
        data['html_finished_tasks_list'] = render_to_string('JtdiTASKS/ajax_views/task_table_body_finished.html', {
            'tasks_finish': tasks_finish})
        data['html_active_tasks_list'] = render_to_string('JtdiTASKS/ajax_views/task_table_body.html', {
            'tasks': tasks})
        data['msg'] = 'Задача успешно завершена'
        if task.project is not None:
            register_event(task, request.user, task.project, 'завершил задачу:')

    return JsonResponse(data)


def task_do_not_remind(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    task = get_object_or_404(Task, pk=pk)
    task.remind = False
    task.save()
    if task.project is not None:
        project_pk = task.project.pk
        success_url = redirect('project_tasks_list', pk=project_pk)
    else:
        success_url = redirect('/')

    return success_url


def task_restore(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    data = dict()

    method = request.POST['param']

    task = get_object_or_404(Task, pk=pk)
    task.finished = False
    task.active = True
    task.status = 'Wait'
    task.save()
    if task.author == request.user or task.performer == request.user:
        tasks, tasks_finish = get_tasks_with_filter(method, task.project, request.user)
        data['form_is_valid'] = True
        data['html_finished_tasks_list'] = render_to_string('JtdiTASKS/ajax_views/task_table_body_finished.html', {
            'tasks_finish': tasks_finish})
        data['html_active_tasks_list'] = render_to_string('JtdiTASKS/ajax_views/task_table_body.html', {
            'tasks': tasks})
        data['msg'] = 'Задача успешно восстановлена'
        if task.project is not None:
            register_event(task, request.user, task.project, 'восстановил задачу:')

    return JsonResponse(data)


def task_transfer_date(request, pk, days):
    if not request.user.is_authenticated():
        return redirect('login')

    data = dict()

    method = request.POST['param']

    task = get_object_or_404(Task, pk=pk)
    task.date = task.date + datetime.timedelta(days=int(days))
    # Планируюмую дату заввершения переносим на тоже количество дней плюс неделя
    task.planed_date_finish = task.planed_date_finish + datetime.timedelta(days=(int(days)+7))
    task.save()
    if task.author == request.user or task.performer == request.user:
        tasks, tasks_finish = get_tasks_with_filter(method, task.project, request.user)
        data['form_is_valid'] = True
        data['html_finished_tasks_list'] = render_to_string('JtdiTASKS/ajax_views/task_table_body_finished.html', {
            'tasks_finish': tasks_finish})
        data['html_active_tasks_list'] = render_to_string('JtdiTASKS/ajax_views/task_table_body.html', {
            'tasks': tasks})
        data['msg'] = 'Задача успешно перенесена на ' + days + ' дней'

        if task.project is not None:
            register_event(task, request.user, task.project, 'перенес задачу на ' + days + ' дней:')

        full_time = TasksTimeTracker.objects.filter(task__pk=pk).aggregate(Sum('full_time'))
        comment_form = CommentAddForm()

        context = {'task': task,
                   'comment_form': comment_form,
                   'full_time': full_time['full_time__sum']}
        data['html_form'] = render_to_string('JtdiTASKS/ajax_views/task_detail_ajax.html',
                                             context,
                                             request=request
                                             )

    return JsonResponse(data)

# TASKS -


# PROJECTS +


def project_del(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    success_url = redirect('/')

    project = get_object_or_404(Project, pk=pk)
    if project.author == request.user:
        tasks = Task.objects.filter(active=True).filter(author=request.user). \
            filter(project=pk).order_by('date')
        for task in tasks:
            task_obj = get_object_or_404(Task, pk=task.pk)
            task_obj.delete()
        kanban_status = KanbanStatus.objects.filter(project__id=pk)
        for kanban_column in kanban_status:
            column_obj = get_object_or_404(KanbanStatus, pk=kanban_column)
            column_obj.delete()
        project.delete()

    return success_url


def project_rename(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    data = dict()

    project = get_object_or_404(Project, pk=pk)
    if project.author == request.user:
        if request.method == 'POST':
            project_rename_form = ProjectForm(request.POST)
            new_title = project_rename_form.data['rename_project-title']
            if new_title != '':
                project.title = new_title
                project.save()
                data['form_is_valid'] = True
                data['title'] = new_title

                register_event(project, request.user, project, 'переименовал проект:')

                context = {'projects': Project.objects.filter(author=request.user),
                           'project_form': ProjectForm(prefix='project')}
                data['project_list'] = render_to_string('JtdiTASKS/menu/project_list_menu.html',
                                                        context,
                                                        request=request
                                                        )

    return JsonResponse(data)


def project_create(request):
    if not request.user.is_authenticated():
        return redirect('login')

    data = dict()

    if request.method == 'POST':
        project_form = ProjectForm(request.POST, prefix='project')
        if project_form.is_valid():
            project = Project()
            project.title = project_form.cleaned_data['title']
            project.author = request.user
            color = generate_color()
            project.color_project = "color: " + color
            project.group = False
            project.save(Project)

            create_first_canban_status(request.user, project, 'Запрос')

            register_event(project, request.user, project, 'создал проект:')
            data['form_is_valid'] = True
            context = {'projects': Project.objects.filter(author=request.user),
                       'project_form': ProjectForm(prefix='project')}
            data['project_list'] = render_to_string('JtdiTASKS/menu/project_list_menu.html',
                                                    context,
                                                    request=request
                                                    )

    return JsonResponse(data)


def project_param(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    data = dict()

    invited_users = InviteUser.objects.filter(user_sender__username__exact=request.user.username) \
        .filter(not_invited=False).filter(invited=True)
    project_invite_form = ProjectInviteUser(prefix='invite_project')
    project_invite_form.fields['user_invite'].queryset = User.objects \
        .filter(pk__in=[user.user_invite.pk for user in invited_users])

    data['form_is_valid'] = True
    data['html_active_tasks_list'] = ''
    data['html_finished_tasks_list'] = ''
    data['project_param'] = render_to_string('JtdiTASKS/ajax_views/project_param.html', {
        'project_rename_form': ProjectFormRename(prefix='rename_project'),
        'project_invite_form': project_invite_form,
        'project': pk},
                                             request=request, )

    return JsonResponse(data)


# PROJECTS -


# USER INVITE +


def user_invite(request):
    if not request.user.is_authenticated():
        return redirect('login')

    my_invites = InviteUser.objects.filter(user_invite__username__exact=request.user.username).filter(not_invited=False)
    invites = InviteUser.objects.filter(user_sender__username__exact=request.user.username).filter(not_invited=False)
    local_timez = pytz.timezone(request.user.profile.timezone)
    dt = datetime.datetime.now().astimezone(local_timez)

    if request.method == "POST":
        form = InviteUserForm(request.POST)
        if form.is_valid():
            invite = InviteUser()
            exist = User.objects.filter(username__iexact=form.cleaned_data['username']).exists()
            if not exist:
                return redirect('/invite')
            invite_user = get_object_or_404(User, username=form.cleaned_data['username'])
            invite.user_invite = invite_user
            invite.user_sender = request.user
            invite.invited = False
            invite.save(InviteUser)

            register_event(invite, request.user, None, 'пригласил пользователя:')
            reminder = QueuePushNotify(user=invite.user_invite,
                                       event='Вас пригласил ' + request.user.username,
                                       url='/invite/',
                                       reminded=False,
                                       date_time=dt)
            reminder.save()

            return redirect('/invite')

    else:
        form = InviteUserForm()

    return render(request, 'JtdiTASKS/views/user_invite.html', {'invite_form': form,
                                                                'my_invites': my_invites,
                                                                'invites': invites,
                                                                })


def invited(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    local_timez = pytz.timezone(request.user.profile.timezone)
    dt = datetime.datetime.now().astimezone(local_timez)

    invite_user = get_object_or_404(InviteUser, pk=pk)
    invite_user.invited = True
    invite_user.not_invited = False

    invite_user.save()
    register_event(invite_user, request.user, None, 'принял приглашение:')
    success_url = redirect('user_invite')

    reminder = QueuePushNotify(user=invite_user.user_sender,
                               event=invite_user.user_invite.username + ' принял приглашение',
                               url='/invite/',
                               reminded=False,
                               date_time=dt)
    reminder.save()

    return success_url


def not_invited(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    local_timez = pytz.timezone(request.user.profile.timezone)
    dt = datetime.datetime.now().astimezone(local_timez)

    invite_user = get_object_or_404(InviteUser, pk=pk)
    invite_user.invited = False
    invite_user.not_invited = True

    invite_user.save()
    register_event(invite_user, request.user, None, 'отклонил приглашение:')
    success_url = redirect('user_invite')

    reminder = QueuePushNotify(user=invite_user.user_sender,
                               event=invite_user.user_invite.username + ' отклонил приглашение',
                               url='/invite/',
                               reminded=False,
                               date_time=dt)
    reminder.save()

    return success_url


def invite_user_in_project(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    data = dict()

    local_timez = pytz.timezone(request.user.profile.timezone)
    dt = datetime.datetime.now().astimezone(local_timez)

    if request.method == 'POST':
        project = get_object_or_404(Project, pk=pk)
        project_invite_form = ProjectInviteUser(request.POST)
        invited_users = InviteUser \
            .objects.filter(Q(user_sender__username__exact=request.user.username)
                            | Q(user_invite__username__exact=request.user.username)) \
            .filter(not_invited=False).filter(invited=True)
        project_invite_form.fields['user_invite'].queryset = User.objects.filter(
            pk__in=[user.user_invite.pk for user in invited_users])

        user_in_proj = get_object_or_404(User, pk=project_invite_form.data['invite_project-user_invite'])
        user_in_proj_pk = project_invite_form.data['invite_project-user_invite']
        exist = PartnerGroup.objects.filter(partner=user_in_proj_pk) \
            .filter(project=project).exists()
        if not exist:
            new_partner = PartnerGroup()
            new_partner.project = project
            new_partner.partner = user_in_proj
            new_partner.save()

            register_event(new_partner, request.user, project, 'добавлен в проект:')

            reminder = QueuePushNotify(user=new_partner.partner,
                                       event=request.user.username + ' добавил в проект:' + project.title,
                                       url='/project_tasks_list/' + str(project.pk) + '/',
                                       reminded=False,
                                       date_time=dt)
            reminder.save()

            data['html_new_user'] = render_to_string('JtdiTASKS/user_in_proj.html', {
                'task_count': Task.objects.filter(project=project)
                                                     .filter(Q(author=user_in_proj_pk) | Q(performer=user_in_proj_pk))
                                                     .filter(active=True).filter(finished=False).count(),
                'username': user_in_proj.username,
                'first_name': user_in_proj.first_name,
                'user_pk': user_in_proj.pk,
                'project_pk': pk,
            })

        data['form_is_valid'] = True

    return JsonResponse(data)


def delete_user_in_project(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    data = dict()

    if request.method == 'POST':
        project = get_object_or_404(Project, pk=pk)
        project_invite_form = ProjectInviteUser(request.POST)
        invited_users = InviteUser \
            .objects.filter(Q(user_sender__username__exact=request.user.username)
                            | Q(user_invite__username__exact=request.user.username)) \
            .filter(not_invited=False).filter(invited=True)
        project_invite_form.fields['user_invite'].queryset = User.objects.filter(
            pk__in=[user.user_invite.pk for user in invited_users])

        user_in_proj = get_object_or_404(User, pk=project_invite_form.data['invite_project-user_invite'])
        user_in_proj_pk = project_invite_form.data['invite_project-user_invite']
        partner = PartnerGroup.objects.filter(partner=user_in_proj_pk) \
            .filter(project=project).exists()
        if partner is not None:
            new_partner = get_object_or_404(PartnerGroup, pk=partner.pk)
            register_event(new_partner.partner, request.user, project, 'удален из проекта:')
            new_partner.delete()

            data['html_new_user'] = render_to_string('JtdiTASKS/user_in_proj.html', {
                'task_count': Task.objects.filter(project=project)
                                                     .filter(Q(author=user_in_proj_pk) | Q(performer=user_in_proj_pk))
                                                     .filter(active=True).filter(finished=False).count(),
                'username': user_in_proj.username,
                'first_name': user_in_proj.first_name,
            })

        data['form_is_valid'] = True

    return JsonResponse(data)


# USER INVITE -


# COMMENTS +


def add_comment(request, pk):
    local_timez = pytz.timezone(request.user.profile.timezone)
    dt = local_time(datetime.datetime.now(), local_timez)
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        post_text = request.POST.get('the_post')
        response_data = {}

        comment = CommentsTask()
        comment.task = task
        comment.date_time = datetime.datetime.now().astimezone(local_timez)
        comment.comment = post_text
        comment.commentator = request.user
        comment.save(CommentsTask)

        register_event(task, request.user, task.project, 'прокомментировал задачу:')

        response_data['result'] = 'Create post successful!'
        response_data['postpk'] = comment.pk
        response_data['text'] = comment.comment
        response_data['created'] = comment.date_time.strftime('%B %d, %Y %H:%M')
        response_data['author'] = comment.commentator.username
        if request.user.profile.avatar:
            response_data['avatar'] = request.user.profile.avatar.url
        else:
            response_data['avatar'] = static('img/avatar_2x.png')

        return JsonResponse(response_data)
    else:
        return JsonResponse({"nothing to see": "this isn't happening"})


def get_comments(request, pk):
    task = get_object_or_404(Task, pk=pk)
    comments = CommentsTask.objects.filter(task=task).order_by('date_time')
    data = []
    local_timez = pytz.timezone(request.user.profile.timezone)
    for comment in comments:
        response_data = {}
        response_data['postpk'] = comment.pk
        response_data['text'] = comment.comment
        response_data['created'] = comment.date_time.astimezone(local_timez).strftime('%B %d, %Y %H:%M')
        response_data['author'] = comment.commentator.username
        if request.user.profile.avatar:
            response_data['avatar'] = request.user.profile.avatar.url
        else:
            response_data['avatar'] = static('img/avatar_2x.png')
        data.append(response_data)

    return JsonResponse(data, safe=False)


# COMMENTS -


# Include tags


@register.inclusion_tag('JtdiTASKS/menu/menu.html')
def project_recent_list(request, user, project_pk):
    currentdate = datetime.datetime.today()
    start_day = currentdate.combine(currentdate, currentdate.min.time())
    end_day = currentdate.combine(currentdate, currentdate.max.time())
    first_day = currentdate
    first_day = first_day.combine(datetime.date(1001, 1, 1), currentdate.min.time())

    tasks_today_notify = Task.objects.filter(active=True).filter(author=user) \
        .filter(date_time__range=(start_day, end_day)) \
        .order_by('date', 'priority', 'time').count()
    tasks_overdue_notify = Task.objects.filter(active=True).filter(author=user) \
        .filter(date_time__range=(first_day, start_day)) \
        .order_by('date', 'priority', 'time').count()

    projects_group = PartnerGroup.objects \
        .filter(partner=user)

    if project_pk == '':
        project_pk = 0
    else:
        project_pk = int(project_pk)

    return {
        'projects': Project.objects.filter(author=user),
        'projects_group': projects_group,
        'project_form': ProjectForm(prefix='project'),
        'tasks_today_notify': tasks_today_notify,
        'tasks_overdue_notify': tasks_overdue_notify,
        'request': request,
        'project_pk': project_pk
    }


@register.inclusion_tag('JtdiTASKS/menu/profile_menu.html')
def profile_menu(user):
    today = datetime.date.today()
    week_end = today - datetime.timedelta(days=7)
    tasks_finish_base = Task.objects.filter(active=False).filter(finished=True).filter(author=user).filter(
        date_finish__range=(week_end, today)).order_by(
        'date_finish')
    qsstats = QuerySetStats(tasks_finish_base, date_field='date_finish', aggregate=Count('id'))
    qsstats.today = today
    # ...в день за указанный период
    values = qsstats.time_series(week_end, today, interval='days')
    my_invites = InviteUser.objects.filter(user_invite__username__exact=user.username).filter(not_invited=False) \
        .filter(invited=False).count()
    notify = 0 + my_invites
    return {'user': user,
            'values': values,
            'notify': notify,
            'my_invites': my_invites}


@register.inclusion_tag('JtdiTASKS/menu/task_menu.html')
def task_menu(request, task, user):
    return {'task': task}


@register.inclusion_tag('JtdiTASKS/menu/project_menu.html')
def project_menu(request, project, project_title):
    invited_users = InviteUser.objects.filter(user_sender__username__exact=request.user.username) \
        .filter(not_invited=False).filter(invited=True)
    project_invite_form = ProjectInviteUser(prefix='invite_project')
    project_invite_form.fields['user_invite'].queryset = User.objects \
        .filter(pk__in=[user.user_invite.pk for user in invited_users])
    return {'project': project,
            'project_title': project_title,
            'project_rename_form': ProjectFormRename(prefix='rename_project'),
            'project_invite_form': project_invite_form}


@register.inclusion_tag('JtdiTASKS/views/search_block.html')
def search_block(user):
    return {'user': user,
            'search_form': SearchForm()}

# TODO В модуле бутстрэп переписан темплейт с полями
