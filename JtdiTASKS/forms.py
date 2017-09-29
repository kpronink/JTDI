import datetime

from django import forms
from django.forms import Textarea, ClearableFileInput, DateTimeInput
from django.forms.widgets import Input

from JtdiTASKS.models import Profile, Task, User, Project

year = datetime.date.today().year


class TimeInput(Input):
    """
    The email input widget
    """
    input_type = 'time'


class DataTimeInput(Input):
    """
    The email input widget
    """
    input_type = 'date'


class UserProfileForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = ('timezone', 'formatdate', 'firstdayweek', 'sex', 'avatar')
        
        widgets = {
            'avatar': ClearableFileInput(attrs={'class': 'ask-signup-avatar-input',}),
            'required': False
        }

        labels = {
            'avatar': 'Аватар',
        }

    
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class TaskForm(forms.Form):
    title = forms.CharField(label='Заголовок')
    title.widget.attrs.update({'ng-model': "data.myinput", 'placeholder': 'забить гвоздь в стену через 20 минут'})

    description = forms.CharField(label='Описание', widget=forms.Textarea, required=False)

    date = forms.DateField(label='Дата начала', initial=datetime.date.today)
    date.widget.input_type = 'date'

    time_field = forms.TimeField(label='Время', required=False)
    time_field.widget.input_type = 'time'

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
