from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.core.cache import cache

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=User.objects.create_user(username='Хаски')
        )

        cls.group = Group.objects.create(
            title='Новая группа',
            description='Описание',
            slug='new_group'
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.get(username='Хаски')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_url_exists_at_desired_location_not_auth(self):
        """Страница доступна неавторизованному пользователю."""
        adress_status_code_names = {
            '/': 200,
            '/about/author/': 200,
            '/about/tech/': 200,
            (f'/group/{self.group.slug}/'): 200,
            '/404/': 404,
        }

        for adress, status_code in adress_status_code_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, status_code)

    def test_url_exists_at_desired_location_auth(self):
        """Страница доступна авторизованному пользователю."""
        adress_status_code_names = {
            '/new/': 200,
            (f'/{self.user.username}/{self.post.id}/edit/'): 200,
        }

        for adress, status_code in adress_status_code_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, status_code)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'index.html': '/',
            'group.html': '/group/new_group/',
            'posts/new.html': '/new/',
        }
        for template, adress in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)
