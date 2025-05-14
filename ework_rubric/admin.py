from django.contrib import admin

from .models import SuperRubric, SubRubric
from .forms import SubRubricForm



admin.site.register(SuperRubric)
admin.site.register(SubRubric)
