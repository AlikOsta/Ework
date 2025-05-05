
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView




class BasePostListView(ListView):
    ...


class BasePostDetailView(DetailView):
    ...

class BasePostCreateView(CreateView):
    ...

class BasePostUpdateView(UpdateView):
    ...

class BasePostDeleteView(DeleteView):
    ...