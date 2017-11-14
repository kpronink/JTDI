import datetime

from django.core.mail import send_mail, EmailMessage
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.template.loader import render_to_string

from JtdiTASKS.models import User, Task
from mysite import settings


class Command(BaseCommand):
    help = 'Рассылает дайджест задач на почту пользователям'

    def handle(self, *args, **options):
        users = User.objects.exclude(email='').filter(profile__mail_notify=True)
        for user in users:
            print(user)
            currentdate = datetime.datetime.today()
            start_day = currentdate.combine(currentdate, currentdate.min.time())
            end_day = currentdate.combine(currentdate, currentdate.max.time())
            first_day = datetime.date(1001, 1, 1)

            tasks_overdue = Task.objects.filter(active=True).filter(Q(author=user) | Q(performer=user)) \
                .filter(date_time__range=(first_day, start_day)).filter(remind=False) \
                .order_by('date', 'priority', 'time')

            tasks_today = Task.objects.filter(active=True).filter(Q(author=user) | Q(performer=user)) \
                .filter(date_time__range=(start_day, end_day)).filter(remind=False) \
                .order_by('date', 'priority', 'time')

            if tasks_today.count() or tasks_overdue.count():

                msg_html = render_to_string('JtdiTASKS/email.html', {'tasks_today': tasks_today,
                                                                     'tasks_overdue': tasks_overdue,
                                                                     'username': user.username})
                _send_email([user.email], subject='Дайджест задач', message=msg_html, sender=settings.EMAIL_HOST_USER)


def _send_email(to_list, subject, message, sender=''):
    msg = EmailMessage(subject=subject, body=message, from_email=sender, bcc=to_list)
    msg.content_subtype = "html"  # Main content is now text/html
    return msg.send()

