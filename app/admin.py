from django.contrib import admin
from .models import Citys


@admin.register(Citys)
class CitysAdmin(admin.ModelAdmin):
    list_display=["id","name"]
