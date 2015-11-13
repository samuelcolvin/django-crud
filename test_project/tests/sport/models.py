from django.db import models


class Town(models.Model):
    name = models.CharField(max_length=255)
    population = models.PositiveIntegerField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Town'
        verbose_name_plural = 'Towns'


class Team(models.Model):
    name = models.CharField(max_length=255)
    owner = models.CharField(max_length=255)
    home_town = models.ForeignKey(Town)
    details = models.TextField(null=True, blank=True)


class Player(models.Model):
    TYPE_STRIKER = 'striker'
    PLAYER_TYPES = [
        ('sk', 'Striker'),
        ('md', 'Midfielder'),
        ('df', 'Defender'),
        ('gc', 'Goal Keeper')
    ]
    name = models.CharField(max_length=255)
    dob = models.DateField()
    teams = models.ManyToManyField(Team)
    player_type = models.CharField(max_length=2, choices=PLAYER_TYPES)


class Competition(models.Model):
    name = models.CharField(max_length=255)



