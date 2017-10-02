from django.contrib import admin
from .models import Task, Profile, Project, InviteUser

admin.site.register(Task)
admin.site.register(Profile)
admin.site.register(Project)
admin.site.register(InviteUser)
