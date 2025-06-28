from mistralai import Mistral
from django.conf import settings

def moderate_post(text):
    # Получаем API ключ из конфигурации
    from ework_config.utils import get_config
    config = get_config()
    
    if not config.mistral_api_key:
        print("Mistral API ключ не настроен, пропускаем модерацию")
        return True  # Пропускаем модерацию если нет ключа
    
    client = Mistral(api_key=config.mistral_api_key)
    print("Начало проверки")
    
    response = client.classifiers.moderate_chat(
        model="mistral-moderation-latest",
        inputs=[{"role": "user", "content": text}]
    )
    
    category_scores = response.results[0].category_scores
    
    has_violations = any(
        category_score > 0.5 
        for category_score in category_scores.values()
    )
    

    return not has_violations
