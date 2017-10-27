import datetime

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import EmailValidator
from django.db.models import Q
from django.forms import Textarea, ClearableFileInput
from django.forms.widgets import Input

from JtdiTASKS.models import Profile, Task, User, Project, PartnerGroup, InviteUser

year = datetime.date.today().year


class TimeInput(Input):
    input_type = 'time'


class DataTimeInput(Input):
    input_type = 'date'


class BooleanFieldInput(Input):
    input_type = 'checkbox'


class CharFieldWidget(Input):
    def __init__(self, max_length=None, min_length=None, strip=True, empty_value='', name='', *args, **kwargs):
        self.max_length = max_length
        self.min_length = min_length
        self.name = name
        self.strip = strip
        self.empty_value = empty_value
        super(CharFieldWidget, self).__init__(*args, **kwargs)


class MyUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email')
        unique_together = [['email']]

    email = forms.CharField(
        label="email",
        widget=forms.EmailInput,
        strip=False,
        help_text="Укажите активный email.",
        validators=[EmailValidator]
    )

    def __init__(self, *args, **kwargs):
        super(MyUserCreationForm, self).__init__(*args, **kwargs)

        self.fields['email'].required = True

    def clean_email(self):
        email = self.cleaned_data["email"]
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует")
        return email


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('timezone', 'formatdate', 'firstdayweek', 'mail_notify', 'sex', 'avatar')

        widgets = {
            'avatar': ClearableFileInput(attrs={'class': 'ask-signup-avatar-input', }),
            'required': False
        }

        labels = {
            'avatar': 'Аватар',
            'timezone': 'Часовой пояс',
            'formatdate': 'Формат даты',
            'sex': 'Пол',
            'firstdayweek': 'Первый день недели',
            'mail_notify': 'Уведомления на почту',
        }


class InviteUserForm(forms.Form):
    username = forms.CharField(label='Имя пользователя')
    widgets = {'user_name': CharFieldWidget(attrs={'id': 'id_username',
                                                   }),
               }


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    email = forms.CharField(
        label="Адрес электронной почты",
        widget=forms.EmailInput,
        strip=False,
        validators=[EmailValidator]
    )

    def clean_email(self):
        email = self.cleaned_data["email"]
        if email and User.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует")
        return email


class TaskForm(forms.Form):
    PRIORITY_1 = '1'
    PRIORITY_2 = '2'
    PRIORITY_3 = '3'
    PRIORITY_4 = '4'

    PRIORITY_CHOISE = (
        (PRIORITY_4, 'Приоритет 4'),
        (PRIORITY_3, 'Приоритет 3'),
        (PRIORITY_2, 'Приоритет 2'),
        (PRIORITY_1, 'Приоритет 1'),
    )

    title = forms.CharField(label='Заголовок')
    title.widget.attrs.update({'ng-model': "data.myinput", 'placeholder': 'забить гвоздь в стену через 20 минут'})

    description = forms.CharField(label='Описание', widget=forms.Textarea, required=False)

    date = forms.DateField(label='Дата начала', initial=datetime.date.today)
    date.widget.input_type = 'date'

    time_field = forms.TimeField(label='Время', required=False)
    time_field.widget.input_type = 'time'

    date_planed = forms.DateField(label='Планируемая дата сдачи')
    date_planed.widget.input_type = 'date'

    project_field = forms.ModelChoiceField(
        label='Проект',
        required=False,
        queryset=None,
    )

    priority_field = forms.ChoiceField(
        label='Важность',
        required=False,
        choices=PRIORITY_CHOISE,
    )

    performer = forms.ModelChoiceField(
        label='Исполнитель',
        required=False,
        queryset=None,
    )

    repeating = forms.BooleanField(label='Повторяющаяся задача', required=False, )
    remind = forms.BooleanField(label='Не напоминать', required=False)

    def clean(self):
        project = self.cleaned_data['project_field']
        performer = self.cleaned_data['performer']

        users_in_project = PartnerGroup.objects.filter(project=project)

        if project is not None:
            all_users_in_project = User.objects.filter(
                Q(pk__in=[user.partner_id for user in users_in_project]) | Q(pk=project.author.pk))
        else:
            all_users_in_project = User.objects.filter(pk__in=[user.partner_id for user in users_in_project])

        pass_performer = (project is None and performer is None)
        for user_in_proj in all_users_in_project:
            if user_in_proj == performer:
                pass_performer = True

        if not pass_performer:
            if project is not None:
                raise forms.ValidationError("Исполнитель не состоит в проекте (" + project.title + ")")
            else:
                raise forms.ValidationError("Нельзя назначать исполнителя без проекта")

        # Always return a value to use as the new cleaned data, even if
        # this method didn't change it.
        return self.cleaned_data


class SearchForm(forms.Form):
    search_field = forms.CharField()
    search_field.widget.attrs.update({'class': "form-control", 'placeholder': "Поиск..."})


class TaskEditForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ("title", "description", "date", "time", "repeating", "remind", "project"
                  , "priority", "performer", "planed_date_finish")

        widgets = {
            'description': Textarea(attrs={'cols': 80, 'rows': 20}),
            'date': DataTimeInput(attrs={'input_type': 'date'}),
            'planed_date_finish': DataTimeInput(attrs={'input_type': 'date'}),
            'time': TimeInput(attrs={'input_type': 'date'}),

        }
        labels = {
            'title': 'Заголовок',
            'description': 'Описание',
            'date': 'Дата начала',
            'time': 'Время',
            'repeating': 'Повторяющаяся задача',
            'remind': 'Не напоминать',
            'project': 'Проект',
            'performer': 'Исполнитель',
            'planed_date_finish': 'Планируемая дата сдачи',
        }

        date = forms.DateField(label='Дата начала', initial=datetime.date.today)
        date.widget.input_type = 'date'

        planed_date_finish = forms.DateField(label='Планируемая дата сдачи')
        planed_date_finish.widget.input_type = 'date'

        project = forms.ModelChoiceField(queryset=None)
        performer = forms.ModelChoiceField(queryset=None)

        time_field = forms.TimeField(label='Время', required=False)
        time_field.widget.input_type = 'time'


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ('title',)

        labels = {
            'title': '',
        }


class FormMoveInProject(forms.Form):
    project_field = forms.ChoiceField(
        label='Переместить',
        required=False,
    )


class ProjectFormRename(forms.Form):
    title = forms.CharField(label='Новый заголовок')


class ProjectInviteUser(forms.Form):
    user_invite = forms.ModelChoiceField(queryset=None,
                                         label='Добавить пользователя',
                                         required=True,
                                         )


class CommentAddForm(forms.Form):
    addComment = forms.CharField(label='', widget=forms.Textarea, required=True)
