
from modeltranslation.translator import translator, TranslationOptions
from .models import SubRubric

class SubRubricTranslationOptions(TranslationOptions):
    fields = ('name',) 

translator.register(SubRubric, SubRubricTranslationOptions)
