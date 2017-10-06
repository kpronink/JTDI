import datetime

from django import forms
from django.forms import Textarea, ClearableFileInput, DateTimeInput, CharField
from django.forms.widgets import Input

from JtdiTASKS.models import Profile, Task, User, Project, InviteUser

year = datetime.date.today().year


class TimeInput(Input):

    input_type = 'time'


class DataTimeInput(Input):

    input_type = 'date'


class CharFieldWidget(Input):
    def __init__(self, max_length=None, min_length=None, strip=True, empty_value='', name='', *args, **kwargs):
        self.max_length = max_length
        self.min_length = min_length
        self.name = name
        self.strip = strip
        self.empty_value = empty_value
        super(CharFieldWidget, self).__init__(*args, **kwargs)


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('timezone', 'formatdate', 'firstdayweek', 'sex', 'avatar')

        widgets = {
            'avatar': ClearableFileInput(attrs={'class': 'ask-signup-avatar-input', }),
            'required': False
        }

        labels = {
            'avatar': 'Аватар',
            'timezone': 'Часовой пояс',
            'formatdate': 'Формат даты',
            'sex': 'Пол',
            'firstdayweek': 'Первый день недели'
        }


class InviteUserForm(forms.ModelForm):
    class Meta:
        model = InviteUser
        fields = ('user_invite',)

        labels = {
            'user_invite': 'Имя пользователя',
        }

        widgets = {'user_invite': CharFieldWidget(attrs={'id': 'id_username',
                                                   }),
                   }


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class TaskForm(forms.Form):
    PRIORITY_1 = '1'
    PRIORITY_2 = '2'
    PRIORITY_3 = '3'
    PRIORITY_4 = '4'

    PRIORITY_CHOISE = (
        (PRIORITY_4, 'Степень важности 4'),
        (PRIORITY_3, 'Степень важности 3'),
        (PRIORITY_2, 'Степень важности 2'),
        (PRIORITY_1, 'Степень важности 1'),
    )

    title = forms.CharField(label='Заголовок')
    title.widget.attrs.update({'ng-model': "data.myinput", 'placeholder': 'забить гвоздь в стену через 20 минут'})

    description = forms.CharField(label='Описание', widget=forms.Textarea, required=False)

    date = forms.DateField(label='Дата начала', initial=datetime.date.today)
    date.widget.input_type = 'date'

    time_field = forms.TimeField(label='Время', required=False)
    time_field.widget.input_type = 'time'

    priority_field = forms.ChoiceField(
        label='Важность',
        required=False,
        choices=PRIORITY_CHOISE,
    )

    repeating = forms.BooleanField(label='Повторяющаяся задача', required=False)


class SearchForm(forms.Form):
    search_field = forms.CharField()
    search_field.widget.attrs.update({'class': "form-control", 'placeholder': "Поиск..."})


class TaskEditForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ("title", "description", "date", "time", "repeating")

        widgets = {
            'description': Textarea(attrs={'cols': 80, 'rows': 20}),
            'date': DataTimeInput(attrs={'input_type': 'date'}),
            'time': TimeInput(attrs={'input_type': 'date'}),

        }
        labels = {
            'title': 'Заголовок',
            'description': 'Описание',
            'date': 'Дата начала',
            'time': 'Время',
            'repeating': 'Повторяющаяся задача',
        }

        date = forms.DateField(label='Дата начала', initial=datetime.date.today)
        date.widget.input_type = 'date'

        time_field = forms.TimeField(label='Время', required=False)
        time_field.widget.input_type = 'time'

    ''''date': SelectDateWidget(years=range(year, year - 100, -1))'''


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ('title',)

        labels = {
            'title': '',
        }


class ProjectFormRename(forms.Form):
    title = forms.CharField(label='Новый заголовок')

