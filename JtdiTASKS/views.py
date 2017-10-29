
import random

from allauth.socialaccount.models import SocialAccount
from django.contrib import messages

from django.db.models import Q, Count, Sum
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
import datetime

from django.template.defaulttags import register
from django.templatetags.static import static

from .forms import TaskForm, TaskEditForm, UserProfileForm, UserForm, ProjectForm, SearchForm, InviteUserForm, \
    ProjectFormRename, ProjectInviteUser, CommentAddForm, MyUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from .models import Task, Project, User, InviteUser, PartnerGroup, TasksTimeTracker, CommentsTask
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


class RegisterFormView(FormView):
    form_class = MyUserCreationForm

    # Ссылка, на которую будет перенаправляться пользователь в случае успешной регистрации.
    # В данном случае указана ссылка на страницу входа для зарегистрированных пользователей.
    success_url = "/login/"

    # Шаблон, который будет использоваться при отображении представления.
    template_name = "JtdiTASKS/registration.html"

    def form_valid(self, form):
        # Создаём пользователя, если данные в форму были введены корректно.
        form.save()

        # Вызываем метод базового класса
        return super(RegisterFormView, self).form_valid(form)


class LoginFormView(FormView):
    form_class = AuthenticationForm

    # Аналогично регистрации, только используем шаблон аутентификации.
    template_name = "JtdiTASKS/login.html"

    # В случае успеха перенаправим на главную.
    success_url = "/"

    def form_valid(self, form):
        # Получаем объект пользователя на основе введённых в форму данных.
        self.user = form.get_user()

        # Выполняем аутентификацию пользователя.
        login(self.request, self.user)
        return super(LoginFormView, self).form_valid(form)
    

def validate_username(request):
    username = request.GET.get('username', None)
    data = {
        'is_taken': User.objects.filter(username__iexact=username).exists()
    }
    if not data['is_taken']:
        data['error_message'] = 'Пользователя с таким именем не существует'
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


def get_index_project(request, pk):
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


def logout_view(request):
    logout(request)
    return redirect('login')


def update_profile(request):
    soc_acc = SocialAccount.objects.filter(user=request.user)
    task_with_full_time =[]
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
    return render(request, 'JtdiTASKS/profile.html', {
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
        .filter(Q(author=request.user) | Q(performer=request.user)). \
        filter(project=None).order_by(
        'date_finish')
    tasks_finished_today = Task.objects.filter(active=False).filter(finished=True) \
        .filter(Q(author=request.user) | Q(performer=request.user)). \
        filter(project=None).filter(date_finish__range=(start_day, end_day)).order_by(
        'date_finish')

    return render(request, 'JtdiTASKS/index.html', {'tasks': tasks,
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
        .filter(Q(author=request.user) | Q(performer=request.user)).filter(project=None) \
        .filter(date_finish__range=(start_day, end_day)).order_by(
        'date_finish')

    return render(request, 'JtdiTASKS/task_today.html', {'tasks': tasks,
                                                         'tasks_finish': tasks_finish,
                                                         'tasks_finished_today': tasks_finished_today})


def task_list_overdue(request):
    if not request.user.is_authenticated():
        return redirect('login')

    currentdate = datetime.datetime.today()
    start_day = currentdate.combine(currentdate, currentdate.min.time())
    end_day = currentdate.combine(currentdate, currentdate.max.time())
    first_day = datetime.date(1001, 1, 1)

    tasks = Task.objects.filter(active=True).filter(Q(author=request.user) | Q(performer=request.user)) \
        .filter(date_time__range=(first_day, start_day)) \
        .order_by('date', 'priority', 'time')
    tasks_finish = Task.objects.filter(active=False).filter(finished=True) \
        .filter(Q(author=request.user) | Q(performer=request.user)). \
        filter(project=None).order_by(
        'date_finish')
    tasks_finished_today = Task.objects.filter(active=False).filter(finished=True) \
        .filter(Q(author=request.user) | Q(performer=request.user)). \
        filter(project=None).filter(date_finish__range=(start_day, end_day)).order_by(
        'date_finish')

    return render(request, 'JtdiTASKS/task_overdue.html', {'tasks': tasks,
                                                           'tasks_finish': tasks_finish,
                                                           'tasks_finished_today': tasks_finished_today})


def task_list_finished(request):
    if not request.user.is_authenticated():
        return redirect('login')

    tasks_finish = Task.objects.filter(active=False).filter(finished=True) \
        .filter(Q(author=request.user) | Q(performer=request.user)).order_by(
        'project').order_by('date_finish')

    return render(request, 'JtdiTASKS/finished_task.html', {'tasks': tasks_finish})


def project_task_list(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    currentdate = datetime.datetime.today()
    start_day = currentdate.combine(currentdate, currentdate.min.time())
    end_day = currentdate.combine(currentdate, currentdate.max.time())

    tasks = Task.objects.filter(active=True).filter(Q(author=request.user) | Q(performer=request.user)). \
        filter(project=pk).order_by('date')
    tasks_finish = Task.objects.filter(active=False).filter(finished=True). \
        filter(Q(author=request.user) | Q(performer=request.user)).filter(project=pk) \
        .filter(date_finish__range=(start_day, end_day)).order_by(
        'date_finish')

    project = Project.objects.filter(pk=pk)[0]

    invited_users = InviteUser \
        .objects.filter(Q(user_sender__username__exact=request.user.username)
                        | Q(user_invite__username__exact=request.user.username)) \
        .filter(not_invited=False).filter(invited=True)

    users_in_project = PartnerGroup.objects.filter(project=project)

    all_users_in_project = User.objects.filter(
        Q(pk__in=[user.partner_id for user in users_in_project]) | Q(pk=project.author.pk))

    all_users_task_count = []
    for user_in_proj in all_users_in_project:
        all_users_task_count.append({'user': user_in_proj
                                        , 'task_count': Task.objects.filter(project=project)
                                    .filter(Q(author=user_in_proj) | Q(performer=user_in_proj))
                                    .filter(active=True).filter(finished=False).count()})

    if request.method == 'POST':
        if project.author == request.user:
            project_rename_form = ProjectFormRename(request.POST, prefix='rename_project')
            project_invite_form = ProjectInviteUser(request.POST, prefix='invite_project')

            project_invite_form.fields['user_invite'].queryset = User.objects.filter(
                pk__in=[user.user_invite.pk for user in invited_users])
            if project_rename_form.is_valid():
                project.title = project_rename_form.cleaned_data['title']
                project.save()
            if project_invite_form.is_valid():
                exist = PartnerGroup.objects.filter(partner=project_invite_form.cleaned_data['user_invite']) \
                    .filter(project=project).exists()
                if not exist:
                    new_partner = PartnerGroup()
                    new_partner.project = project
                    new_partner.partner = project_invite_form.cleaned_data['user_invite']
                    new_partner.save()

    return render(request, 'JtdiTASKS/project_task_list.html', {'tasks': tasks,
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

    return render(request, 'JtdiTASKS/search.html', {'search_result_data': search_result_data})


# Task view


def task_detail(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    task = get_object_or_404(Task, pk=pk)
    full_time = TasksTimeTracker.objects.filter(task__pk=pk).aggregate(Sum('full_time'))
    comment_form = CommentAddForm()

    return render(request, 'JtdiTASKS/task_detail.html', {'task': task,
                                                          'comment_form': comment_form,
                                                          'full_time': full_time['full_time__sum']
                                                          })


def task_edit(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    COLOR_CHOISE = {
        1: 'red',
        2: 'yellow',
        3: 'green',
        4: 'grey'}

    invited_users = InviteUser \
        .objects.filter(Q(user_sender__username__exact=request.user.username)
                        | Q(user_invite__username__exact=request.user.username)) \
        .filter(not_invited=False).filter(invited=True)

    users_in_project = PartnerGroup.objects.filter(partner_id__in=[user.user_invite.pk for user in invited_users])
    all_users_in_project = User.objects.filter(
        Q(pk__in=[user.partner_id for user in users_in_project]) | Q(pk=request.user.pk))

    task = get_object_or_404(Task, pk=pk)
    if task.author != request.user:
        return redirect('task_detail', pk=task.pk)

    if request.method == "POST":
        if task.author == request.user:
            form = TaskEditForm(request.POST, instance=task)
            form.fields['project'].queryset = Project.objects.filter(author=request.user)
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
                return redirect('task_detail', pk=task.pk)
    else:
        form = TaskEditForm(instance=task)
        form.fields['project'].queryset = Project.objects.filter(author=request.user)
        form.fields['performer'].queryset = all_users_in_project

    return render(request, 'JtdiTASKS/task_edit.html', {'form': form
                                                        })


def task_del(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    success_url = redirect('/')

    task = get_object_or_404(Task, pk=pk)
    if task.author == request.user:
        if task.project is not None:
            project_pk = task.project.pk
            success_url = redirect('project_tasks_list', pk=project_pk)
        task.delete()

    return success_url


def task_start_stop(request, pk, status):
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

        task.status = status
        task.save()

    return redirect('task_detail', pk=pk)


def task_finish(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    success_url = redirect('/')

    task = get_object_or_404(Task, pk=pk)
    if task.author == request.user or task.performer == request.user:
        task.finished = True
        task.active = False
        task.date_finish = datetime.datetime.today()
        task.date_time_finish = datetime.datetime.today()
        task.status = 'Finished'
        task.save()
        if task.project is not None:
            project_pk = task.project.pk
            success_url = redirect('project_tasks_list', pk=project_pk)

    return success_url


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

    task = get_object_or_404(Task, pk=pk)
    task.finished = False
    task.active = True
    task.status = 'Wait'
    task.save()
    if task.project is not None:
        project_pk = task.project.pk
        success_url = redirect('project_tasks_list', pk=project_pk)
    else:
        success_url = redirect('/')

    return success_url


def task_new(request, project=None):
    if not request.user.is_authenticated():
        return redirect('login')

    COLOR_CHOISE = {
        1: 'red',
        2: 'yellow',
        3: 'green',
        4: 'grey'}

    invited_users = InviteUser \
        .objects.filter(Q(user_sender__username__exact=request.user.username)
                        | Q(user_invite__username__exact=request.user.username)) \
        .filter(not_invited=False).filter(invited=True)

    users_in_project = PartnerGroup.objects.filter(project=project) \
        .filter(partner_id__in=[user.user_invite.pk for user in invited_users])

    proj = None

    if project is not None:
        proj = get_object_or_404(Project, pk=project)
        all_users_in_project = User.objects.filter(
            Q(pk__in=[user.partner_id for user in users_in_project]) | Q(pk=proj.author.pk))
        success_url = redirect('project_tasks_list', pk=project)
    else:
        users_in_project = PartnerGroup.objects.filter(partner_id__in=[user.user_invite.pk for user in invited_users])
        all_users_in_project = User.objects \
            .filter(Q(pk__in=[user.partner_id for user in users_in_project]) | Q(pk=request.user.pk))
        success_url = redirect('/')

    if request.method == "POST":

        form = TaskForm(request.POST, initial={'project': 'instance'})
        form.fields['project_field'].queryset = Project.objects.filter(author=request.user)
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

            return success_url
    else:
        form = TaskForm(initial={'project': 'instance'})
        form.fields['project_field'].queryset = Project.objects.filter(author=request.user)
        form.fields['performer'].queryset = all_users_in_project

    return render(request, 'JtdiTASKS/new_task.html', {'form': form
                                                       })


def task_transfer_date(request, pk, days):
    if not request.user.is_authenticated():
        return redirect('login')

    task = get_object_or_404(Task, pk=pk)
    task.date = task.date + datetime.timedelta(days=int(days))
    task.save()
    if task.project is not None:
        project_pk = task.project.pk
        success_url = redirect('project_tasks_list', pk=project_pk)
    else:
        success_url = redirect('/')

    return success_url


# Project view


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
        project.delete()

    return success_url


# User invite


def user_invite(request):
    if not request.user.is_authenticated():
        return redirect('login')

    my_invites = InviteUser.objects.filter(user_invite__username__exact=request.user.username).filter(not_invited=False)
    invites = InviteUser.objects.filter(user_sender__username__exact=request.user.username).filter(not_invited=False)

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

            return redirect('/invite')

    else:
        form = InviteUserForm()

    return render(request, 'JtdiTASKS/user_invite.html', {'invite_form': form,
                                                          'my_invites': my_invites,
                                                          'invites': invites,
                                                          })


def invited(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    invite_user = get_object_or_404(InviteUser, pk=pk)
    invite_user.invited = True
    invite_user.not_invited = False

    invite_user.save()
    success_url = redirect('user_invite')

    return success_url


def not_invited(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    invite_user = get_object_or_404(InviteUser, pk=pk)
    invite_user.invited = False
    invite_user.not_invited = True

    invite_user.save()
    success_url = redirect('user_invite')

    return success_url


# Comments


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
    

# Include tags


@register.inclusion_tag('JtdiTASKS/menu.html')
def project_recent_list(request, user):
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

    return {
        'projects': Project.objects.filter(author=user),
        'projects_group': projects_group,
        'project_form': ProjectForm(prefix='project'),
        'tasks_today_notify': tasks_today_notify,
        'tasks_overdue_notify': tasks_overdue_notify,
        'request': request
    }


@register.inclusion_tag('JtdiTASKS/profile_menu.html')
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


@register.inclusion_tag('JtdiTASKS/task_menu.html')
def task_menu(request, task, user):
    return {'task': task}


@register.inclusion_tag('JtdiTASKS/project_menu.html')
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


@register.inclusion_tag('JtdiTASKS/search_block.html')
def search_block(user):
    return {'user': user,
            'search_form': SearchForm()}


@register.inclusion_tag('JtdiTASKS/gantt.html')
def gantt_block():
    return {}

# TODO В модуле бутстрэп переписан темплейт с полями
