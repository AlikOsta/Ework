from .models import SubRubric

def post_rubric_context_processor(request):
    context = {'rubrics': SubRubric.objects.all()}
    return context