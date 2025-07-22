from mistralai import Mistral

def moderate_post(text):
    from ework_config.utils import get_config
    config = get_config()
    
    if not config.mistral_api_key:
        return True 
    client = Mistral(api_key=config.mistral_api_key)
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
