from django import forms
from ework_post.forms import BasePostForm
from ework_services.models import PostServices

class ServicePostForm(BasePostForm):
    class Meta(BasePostForm.Meta):
        model = PostServices
        fields = BasePostForm.Meta.fields 
