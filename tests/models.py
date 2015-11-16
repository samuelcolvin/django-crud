from django.db import models


class Article(models.Model):
    title = models.CharField(max_length=30, help_text='the title of the article')
    body = models.TextField()
    slug = models.SlugField(blank=True)

    class Meta:
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'

    def __str__(self):
        return self.title


class Section(models.Model):
    article = models.ForeignKey(Article, on_delete=models.PROTECT)
    text = models.TextField(null=True)
