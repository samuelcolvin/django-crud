from django.db import models


class Article(models.Model):
    title = models.CharField(max_length=30)
    body = models.TextField()
    slug = models.SlugField(blank=True)
