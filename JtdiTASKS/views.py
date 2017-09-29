import random

import pytz
from allauth.socialaccount.models import SocialAccount
from django.contrib import messages

from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
import datetime

from django.template.defaulttags import register

from .forms import TaskForm, TaskEditForm, UserProfileForm, UserForm, ProjectForm, SearchForm
from django.contrib.auth.forms import AuthenticationForm
from .models import Task, Project, User
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
    if data['is_taken']:
        data['error_message'] = 'A user with this username already exists.'
    return JsonResponse(data)


def get_recent_task(request):
    if request.user.is_authenticated():
        tasks_alert = Task.objects.filter(active=True).filter(author=request.user).filter(project=None)\
            .filter(date__lte=datetime.datetime.today()).order_by('date')
        data = {}
        for task in tasks_alert:
            data['/task/'+str(task.pk)+'/'] = task.title

    else:

        data = {
           
        }

    return JsonResponse(data)


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
        project_form = ProjectForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('profile')
        if project_form.is_valid():
            project = Project()
            project.title = project_form.cleaned_data['title']
            project.author = request.user
            project.save(Project)
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

    tasks = Task.objects.filter(active=True).filter(author=request.user).filter(project=None).order_by('date')
    tasks_finish = Task.objects.filter(active=False).filter(finished=True).filter(author=request.user). \
        filter(project=None).order_by(
        'date_finish')
    tasks_finished_today = Task.objects.filter(active=False).filter(finished=True).filter(author=request.user). \
        filter(project=None).filter(date_finish__range=(start_day, end_day)).order_by(
        'date_finish')
    paginator_task = Paginator(tasks, 4)

    page = request.GET.get('page')
    try:
        tasks = paginator_task.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        tasks = paginator_task.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        tasks = paginator_task.page(paginator_task.num_pages)

    if request.method == 'POST':
        project_form = ProjectForm(request.POST)
        if project_form.is_valid():
            project = Project()
            project.title = project_form.cleaned_data['title']
            project.author = request.user
            color = generate_color()
            project.color_project = "color: " + color + "; background: " + color
            project.save(Project)
            return redirect('/')

    return render(request, 'JtdiTASKS/index.html', {'tasks': tasks,
                                                    'tasks_finish': tasks_finish,
                                                    'tasks_finished_today': tasks_finished_today})


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
        project_form = ProjectForm(request.POST)
        if project_form.is_valid():
            project = Project()
            project.title = project_form.cleaned_data['title']
            project.author = request.user
            project.save(Project)
            return redirect('/')

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

    if request.method == 'POST':
        project_form = ProjectForm(request.POST)
        if project_form.is_valid():
            project = Project()
            project.title = project_form.cleaned_data['title']
            project.author = request.user
            project.save(Project)
            return redirect('/')

    return render(request, 'JtdiTASKS/search.html', {'search_result_data': search_result_data})


def task_detail(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    task = get_object_or_404(Task, pk=pk)

    project_form = ProjectForm()
    if request.method == "POST":
        if project_form.is_valid():
            project = Project()
            project.title = project_form.cleaned_data['title']
            project.author = request.user
            project.save(Project)
            return redirect('task_detail', pk=task.pk)

    return render(request, 'JtdiTASKS/task_detail.html', {'task': task
                                                          })


def task_edit(request, pk):
    if not request.user.is_authenticated():
        return redirect('login')

    task = get_object_or_404(Task, pk=pk)

    if request.method == "POST":
        form = TaskEditForm(request.POST)
        if form.is_valid():
            task.author = request.user
            task.active = True
            task.save()
            return redirect('task_detail', pk=task.pk)
        project_form = ProjectForm(request.POST)
        if project_form.is_valid():
            project = Project()
            project.title = project_form.cleaned_data['title']
            project.author = request.user
            project.save(Project)
            return redirect('task_detail', pk=task.pk)
    else:
        form = TaskEditForm(instance=task)

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
    task.date_finish = datetime.date.today()
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

    if request.method == "POST":
        proj = None
        form = TaskForm(request.POST, initial={'project': 'instance'})
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
            task.project = proj
            task.active = True
            task.repeating = form.cleaned_data['repeating']
            task.save(Task)

            return success_url
        project_form = ProjectForm(request.POST)
        if project_form.is_valid():
            project = Project()
            project.title = project_form.cleaned_data['title']
            project.author = request.user
            project.save(Project)
            return success_url
    else:
        form = TaskForm()

    return render(request, 'JtdiTASKS/new_task.html', {'form': form
                                                       })


@register.inclusion_tag('JtdiTASKS/menu.html')
def project_recent_list(user):
    return {
        'projects': Project.objects.filter(author=user),
        'project_form': ProjectForm(),
    }


@register.inclusion_tag('JtdiTASKS/profile_menu.html')
def profile_menu(user):
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    sunday = today + datetime.timedelta(6 - today.weekday())
    week_end = today - datetime.timedelta(6 - today.weekday())
    tasks_finish_base = Task.objects.filter(active=False).filter(finished=True).filter(author=user).order_by(
        'date_finish')
    # считаем количество платежей...
    qsstats = QuerySetStats(tasks_finish_base, date_field='date_finish', aggregate=Count('id'))
    # ...в день за указанный период
    values = qsstats.time_series(week_end, today, interval='days')

    return {'user': user,
            'values': values}


@register.inclusion_tag('JtdiTASKS/search_block.html')
def search_block(user):
    return {'user': user,
            'search_form': SearchForm()}
