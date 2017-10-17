import json
import random

import pytz
from allauth.socialaccount.models import SocialAccount
from django.contrib import messages

from django.db.models import Q, Count
from django.forms import formset_factory
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
import datetime

from django.template.defaulttags import register

from .forms import TaskForm, TaskEditForm, UserProfileForm, UserForm, ProjectForm, SearchForm, InviteUserForm, \
    ProjectFormRename, FormMoveInProject
from django.contrib.auth.forms import AuthenticationForm
from .models import Task, Project, User, InviteUser
from django.contrib.auth import logout, login
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic.edit import FormView
from django.contrib.auth.forms import UserCreationForm
from qsstats import QuerySetStats


def generate_color():
    r = lambda: random.randint(0, 255)
    return '#%02X%02X%02X' % (r(), r(), r())


def time_to_utc(t):
    dt = datetime.datetime.combine(datetime.date.today(), t)
    utc_dt = dt.astimezone(pytz.utc)
    return utc_dt.time()


class RegisterFormView(FormView):
    form_class = UserCreationForm

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
            .filter(date__range=(today_min, today_max)).order_by('date')
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
        tasks_total = Task.objects.filter().filter(author=request.user).filter(project=proj).order_by('date').count()
        tasks_finished = Task.objects.filter(finished=True).filter(author=request.user).filter(project=proj).order_by(
            'date').count()

    return JsonResponse(
        [{'label': 'Всего задач', 'value': tasks_total}, {'label': 'Задач завершено', 'value': tasks_finished},
         {'label': 'Участников проекта', 'value': 1}], safe=False)


def logout_view(request):
    logout(request)
    return redirect('login')


def update_profile(request):
    search_form = SearchForm()
    soc_acc = SocialAccount.objects.filter(user=request.user)
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    sunday = today + datetime.timedelta(6 - today.weekday())
    tasks_finish = Task.objects.filter(active=False).filter(finished=True).filter(author=request.user). \
        filter(project=None).order_by(
        'date_finish')
    # считаем количество платежей...
    qsstats = QuerySetStats(tasks_finish, date_field='date_finish', aggregate=Count('id'))
    # ...в день за указанный период
    values = qsstats.time_series(monday, sunday, interval='days')
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=request.user.profile)
    return render(request, 'JtdiTASKS/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'values': values,
        'search_form': search_form,
        'accounts': soc_acc,
    })


def task_list(request):
    if not request.user.is_authenticated():
        return redirect('login')

    currentdate = datetime.datetime.today()
    start_day = currentdate.combine(currentdate, currentdate.min.time())
    end_day = currentdate.combine(currentdate, currentdate.max.time())

    tasks = Task.objects.filter(active=True).filter(author=request.user).filter(project=None). \
        order_by('date', 'priority', 'time')
    tasks_finish = Task.objects.filter(active=False).filter(finished=True).filter(author=request.user). \
        filter(project=None).order_by(
        'date_finish')
    tasks_finished_today = Task.objects.filter(active=False).filter(finished=True).filter(author=request.user). \
        filter(project=None).filter(date_finish__range=(start_day, end_day)).order_by(
        'date_finish')
    paginator_task = Paginator(tasks, 8)

    page = request.GET.get('page')
    try:
        tasks = paginator_task.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        tasks = paginator_task.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        tasks = paginator_task.page(paginator_task.num_pages)

    return render(request, 'JtdiTASKS/index.html', {'tasks': tasks,
                                                    'tasks_finish': tasks_finish,
                                                    'tasks_finished_today': tasks_finished_today})


def task_list_today(request):
    if not request.user.is_authenticated():
        return redirect('login')

    currentdate = datetime.datetime.today()
    start_day = currentdate.combine(currentdate, currentdate.min.time())
    end_day = currentdate.combine(currentdate, currentdate.max.time())

    tasks = Task.objects.filter(active=True).filter(author=request.user).filter(date__range=(start_day, end_day)) \
        .filter(project=None).order_by('date', 'priority', 'time')
    tasks_finish = Task.objects.filter(active=False).filter(finished=True).filter(author=request.user). \
        filter(project=None).order_by(
        'date_finish')
    tasks_finished_today = Task.objects.filter(active=False).filter(finished=True).filter(author=request.user). \
        filter(project=None).filter(date_finish__range=(start_day, end_day)).order_by(
        'date_finish')
    paginator_task = Paginator(tasks, 8)

    page = request.GET.get('page')
    try:
        tasks = paginator_task.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        tasks = paginator_task.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        tasks = paginator_task.page(paginator_task.num_pages)

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

    tasks = Task.objects.filter(active=True).filter(author=request.user).filter(date__range=(first_day, start_day)) \
        .order_by('date', 'priority', 'time')
    tasks_finish = Task.objects.filter(active=False).filter(finished=True).filter(author=request.user). \
        filter(project=None).order_by(
        'date_finish')
    tasks_finished_today = Task.objects.filter(active=False).filter(finished=True).filter(author=request.user). \
        filter(project=None).filter(date_finish__range=(start_day, end_day)).order_by(
        'date_finish')
    paginator_task = Paginator(tasks, 8)

    page = request.GET.get('page')
    try:
        tasks = paginator_task.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        tasks = paginator_task.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        tasks = paginator_task.page(paginator_task.num_pages)

    return render(request, 'JtdiTASKS/task_overdue.html', {'tasks': tasks,
                                                           'tasks_finish': tasks_finish,
                                                           'tasks_finished_today': tasks_finished_today})


def task_list_finished(request):
    if not request.user.is_authenticated():
        return redirect('login')

    tasks_finish = Task.objects.filter(active=False).filter(finished=True).filter(author=request.user). \
        filter(project=None).order_by(
        'date_finish')

    paginator_task = Paginator(tasks_finish, 16)

    page = request.GET.get('page')
    try:
        tasks_finish = paginator_task.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        tasks_finish = paginator_task.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        tasks_finish = paginator_task.page(paginator_task.num_pages)

    return render(request, 'JtdiTASKS/finished_task.html', {'tasks': tasks_finish})


def project_task_list(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    tasks = Task.objects.filter(active=True).filter(author=request.user). \
        filter(project=pk).order_by('date')
    tasks_finish = Task.objects.filter(active=False).filter(finished=True). \
        filter(author=request.user).filter(project=pk).order_by(
        'date_finish')

    project = Project.objects.filter(pk=pk)[0]

    if request.method == 'POST':
        project_rename_form = ProjectFormRename(request.POST, prefix='rename_project')
        if project_rename_form.is_valid():
            project.title = project_rename_form.cleaned_data['title']
            project.save()

    return render(request, 'JtdiTASKS/project_task_list.html', {'tasks': tasks,
                                                                'tasks_finish': tasks_finish,
                                                                'project': pk,
                                                                'project_object': project})


def search_result(request):
    if not request.user.is_authenticated():
        return redirect('login')

    search_str = request.GET['search_field']
    search_str = search_str.replace('.', ' ')
    search_str_split = search_str.split(' ')
    search_result_data = []
    for item in search_str_split:
        search_result_data = Task.objects.filter(Q(title__contains=item) |
                                                 Q(description__contains=item)).order_by(
            '-date_finish')

    return render(request, 'JtdiTASKS/search.html', {'search_result_data': search_result_data})


def task_detail(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    task = get_object_or_404(Task, pk=pk)

    return render(request, 'JtdiTASKS/task_detail.html', {'task': task
                                                          })


# Task view


def task_edit(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    COLOR_CHOISE = {
        1: 'red',
        2: 'yellow',
        3: 'green',
        4: 'grey'}

    task = get_object_or_404(Task, pk=pk)

    if request.method == "POST":
        form = TaskEditForm(request.POST, instance=task)
        form.fields['project'].queryset = Project.objects.filter(author=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.author = request.user
            task.active = True
            task.color = COLOR_CHOISE[int(task.priority)]
            task.save()
            return redirect('task_detail', pk=task.pk)
    else:
        form = TaskEditForm(instance=task)
        form.fields['project'].queryset = Project.objects.filter(author=request.user)

    return render(request, 'JtdiTASKS/task_edit.html', {'form': form
                                                        })


def task_del(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    task = get_object_or_404(Task, pk=pk)
    if task.project is not None:
        project_pk = task.project.pk
        success_url = redirect('project_tasks_list', pk=project_pk)
    else:
        success_url = redirect('/')
    task.delete()

    return success_url


def task_finish(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    task = get_object_or_404(Task, pk=pk)
    task.finished = True
    task.active = False
    task.date_finish = datetime.datetime.today()
    task.date_time_finish = datetime.datetime.today()
    task.save()
    if task.project is not None:
        project_pk = task.project.pk
        success_url = redirect('project_tasks_list', pk=project_pk)
    else:
        success_url = redirect('/')

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

    if request.method == "POST":
        proj = None
        form = TaskForm(request.POST, initial={'project': 'instance'})
        form.fields['project_field'].queryset = Project.objects.filter(author=request.user)
        if project is not None:
            proj = get_object_or_404(Project, pk=project)
            success_url = redirect('project_tasks_list', pk=project)
        else:
            success_url = redirect('/')
        if form.is_valid():
            task = Task()
            task.title = form.cleaned_data['title']
            task.description = form.cleaned_data['description']
            task.date = form.cleaned_data['date']
            task.time = datetime.datetime.combine(task.date, form.cleaned_data['time_field'])
            task.author = request.user
            if proj is not None:
                task.project = proj
            else:
                task.project = form.cleaned_data['project_field']
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

    project = get_object_or_404(Project, pk=pk)
    tasks = Task.objects.filter(active=True).filter(author=request.user). \
        filter(project=pk).order_by('date')
    for task in tasks:
        task_obj = get_object_or_404(Task, pk=task.pk)
        task_obj.delete()
    project.delete()
    success_url = redirect('/')

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


# Include tags


@register.inclusion_tag('JtdiTASKS/menu.html')
def project_recent_list(request, user):
    currentdate = datetime.datetime.today()
    start_day = currentdate.combine(currentdate, currentdate.min.time())
    end_day = currentdate.combine(currentdate, currentdate.max.time())
    first_day = datetime.date(1001, 1, 1)

    tasks_today_notify = Task.objects.filter(active=True).filter(author=user).filter(date__range=(start_day, end_day)) \
        .filter(project=None).order_by('date', 'priority', 'time').count()
    tasks_overdue_notify = Task.objects.filter(active=True).filter(author=user).filter(
        date__range=(first_day, start_day)) \
        .order_by('date', 'priority', 'time').count()

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
def project_menu(project):
    return {'project': project,
            'project_rename_form': ProjectFormRename(prefix='rename_project')}


@register.inclusion_tag('JtdiTASKS/search_block.html')
def search_block(user):
    return {'user': user,
            'search_form': SearchForm()}




    # TODO В модуле бутстрэп переписан теплейт с полями
