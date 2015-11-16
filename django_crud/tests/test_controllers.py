from unittest import TestCase
from django_crud.controllers import VanillaController


class VanillaControllerTestCase(TestCase):
    def test_blank_controller(self):
        ctrl = VanillaController()
