from django_crud.rich_views import ItemDisplayMixin
from .models import Article


def test_basic():
    class DM(ItemDisplayMixin):
        model = Article
    dm = DM()
    assert list(dm.gen_short_props(Article())) == []
    assert list(dm.gen_long_props(Article())) == []


def test_vsimple():
    class DM(ItemDisplayMixin):
        model = Article
        display_items = ['title']
    dm = DM()
    assert list(dm.gen_short_props(Article())) == [{'value': '', 'help_text': 'the title of the article',
                                                    'extra': {}, 'name': 'title'}]
    assert list(dm.gen_long_props(Article())) == []


def test_help_text():
    class DM(ItemDisplayMixin):
        model = Article
        display_items = [('the title', 'title', 'ht')]
    dm = DM()
    assert list(dm.gen_short_props(Article())) == [{'value': '', 'help_text': 'ht', 'extra': {}, 'name': 'the title'}]
    assert list(dm.gen_long_props(Article())) == []


def test_func():
    class DM(ItemDisplayMixin):
        model = Article
        display_items = ['func|show_title']

        def show_title(self, obj):
            return obj.title
        show_title.short_description = 'ST'

    dm = DM()
    art1 = Article(title='__title__')
    assert list(dm.gen_short_props(art1)) == [{'value': '__title__', 'help_text': None, 'extra': {}, 'name': 'ST'}]
    assert list(dm.gen_long_props(art1)) == []


def test_text_field():
    class DM(ItemDisplayMixin):
        model = Article
        display_items = ['body']

    dm = DM()
    art = Article(body='__body__')
    assert list(dm.gen_short_props(art)) == []
    assert list(dm.gen_long_props(art)) == [{'extra': {}, 'help_text': None, 'name': 'body', 'value': '__body__'}]


def test_char_field_long():
    class DM(ItemDisplayMixin):
        model = Article
        display_items = [('title', 'long|title')]

    dm = DM()
    art = Article(title='__title__')
    assert list(dm.gen_short_props(art)) == []
    assert list(dm.gen_long_props(art)) == [{'extra': {}, 'help_text': None, 'name': 'title', 'value': '__title__'}]


def test_text_field_short():
    class DM(ItemDisplayMixin):
        model = Article
        display_items = ['short|body']

    dm = DM()
    art = Article(body='__body__')
    assert list(dm.gen_short_props(art)) == [{'extra': {}, 'help_text': None, 'name': 'body', 'value': '__body__'}]
    assert list(dm.gen_long_props(art)) == []
