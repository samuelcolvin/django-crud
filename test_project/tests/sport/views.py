from django_crud.controllers import RichController

from .models import Town


class TownController(RichController):
    model = Town
