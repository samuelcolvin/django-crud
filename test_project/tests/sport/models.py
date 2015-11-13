from django.db import models


class Town(models.Model):
    name = models.CharField('Name', max_length=255)
    population = models.PositiveIntegerField('Population')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Town'
        verbose_name_plural = 'Towns'


class Team(models.Model):
    name = models.CharField('Name', max_length=255)
    owner = models.CharField('Owner', max_length=255)
    home_town = models.ForeignKey(Town, verbose_name='Home Town')
    details = models.TextField('Details', null=True, blank=True)

    class Meta:
        verbose_name = 'Team'
        verbose_name_plural = 'Teams'


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



