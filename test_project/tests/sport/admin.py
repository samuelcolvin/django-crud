from django.contrib import admin
from tests.sport.models import Town, Team, Player, Competition


class TownAdmin(admin.ModelAdmin):
    pass


class TeamAdmin(admin.ModelAdmin):
    pass


class PlayerAdmin(admin.ModelAdmin):
    pass


class CompetitionAdmin(admin.ModelAdmin):
    pass


admin.site.register(Town, TownAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(Competition, CompetitionAdmin)
