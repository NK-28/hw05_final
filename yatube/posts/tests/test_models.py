from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=User.objects.create_user(username='Хаски'))

        cls.group = Group.objects.create(
            title='Новая группа',
            description='Описание',
            slug='new_group')

    def test_text_label(self):
        """verbose_name поля text совпадает с ожидаемым."""
        post = PostModelTest.post
        verbose = post.text
        self.assertEqual(verbose, 'Тестовый текст')

    def test_title_label(self):
        """verbose_name поля title совпадает с ожидаемым."""
        group = PostModelTest.group
        verbose = group.title
        self.assertEqual(verbose, 'Новая группа')
