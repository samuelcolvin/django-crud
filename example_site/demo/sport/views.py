from django_crud.controllers import RichController

from .models import Town, Team


class TownController(RichController):
    model = Town


class TeamController(RichController):
    model = Team
    list_display_items = [
        'link|name',
        'owner',
        'home_town',
    ]

    detail_display_items = [
        'name',
        'owner',
        'home_town',
        'details',
    ]
