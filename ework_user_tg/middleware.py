from django.utils import translation
from django.contrib.auth import get_user_model

User = get_user_model()

class UserLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request.user, 'language'):
            user_language = request.user.language
            if user_language and user_language != request.LANGUAGE_CODE:
                translation.activate(user_language)
                request.LANGUAGE_CODE = user_language

        response = self.get_response(request)
        return response
