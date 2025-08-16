
from modeltranslation.translator import translator, TranslationOptions
from .models import City

class CityTranslationOptions(TranslationOptions):
    fields = ('name',) 

translator.register(City, CityTranslationOptions)
