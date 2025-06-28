from django.core.cache import cache
from .models import SubRubric

def post_rubric_context_processor(request):
    # Кэшируем рубрики на 1 час
    rubrics = cache.get('rubrics_list')
    if rubrics is None:
        rubrics = SubRubric.objects.select_related('super_rubric').order_by(
            'super_rubric__order', 'order'
        )
        cache.set('rubrics_list', rubrics, 3600)
    
    return {'rubrics': rubrics}