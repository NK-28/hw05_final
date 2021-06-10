import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django import forms
from django.contrib.auth import get_user_model
from django.core.paginator import Page
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from ..models import Comment, Follow, Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

        cls.group = Group.objects.create(
            title='Новая группа',
            description='Описание',
            slug='new_group'
        )

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=User.objects.create_user(username='Хаски'),
            group=Group.objects.get(title='Новая группа'),
            image=SimpleUploadedFile(
                name='small.gif',
                content=small_gif,
                content_type='image/gif'),
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.get(username='Хаски')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'index.html': reverse('index'),
            'group.html': reverse(
                'group_posts', kwargs={'slug': self.group.slug}),
            'posts/new.html': reverse('new'),
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech'),
        }

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('index'))
        self.assertIsInstance(response.context['page'], Page)
        post = response.context.get('page').object_list[0]
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author.username, self.user.username)

    def test_group_shows_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'group_posts', kwargs={'slug': 'new_group'}))
        self.assertIsInstance(response.context['page'], Page)
        self.assertIsInstance(response.context['group'], Group)
        post = response.context.get('page').object_list[0]
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author.username, self.user.username)
        group = response.context.get('group')
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.description, self.group.description)

    def test_new_shows_correct_context(self):
        """Шаблон new сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('new'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
            'image': forms.fields.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_edit_shows_correct_context(self):
        """Шаблон edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'edit', kwargs={'username': self.user.username,
                            'post_id': self.post.id}))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
            'image': forms.fields.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_profile_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'profile', kwargs={'username': self.user.username}))
        post = response.context.get('page').object_list[0]
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author.username, self.user.username)

    def test_post_id_shows_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'post', kwargs={'username': self.user.username,
                            'post_id': self.post.id}))
        post = response.context.get('post')
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author.username, self.user.username)

    def test_cache_index_page(self):
        """Кэш страницы index работает верно"""
        response = self.authorized_client.get(reverse('index'))
        cache_content = response.content
        Post.objects.create(
            text='Текст 2',
            author=User.objects.get(username=self.user.username))
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(cache_content, response.content)
        cache.clear()
        response = self.authorized_client.get(reverse('index'))
        self.assertNotEqual(cache_content, response.content)

    def test_follow_profile(self):
        """Функция follow работают корректно"""
        response = self.authorized_client.get(reverse(
            'profile_follow', kwargs={'username': self.user.username}))
        follow_count = Follow.objects.count()
        Follow.objects.create(author=self.post.author, user=self.user)
        Post.objects.create(
            text='Текст 2',
            author=self.post.author)
        user_2 = User.objects.create(username='Вася')

        self.assertRedirects(response, reverse(
            'profile', kwargs={'username': self.user.username}))
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(
            Follow.objects.filter(
                author=self.post.author,
                user=self.user
            ).exists()
        )
        self.assertFalse(
            Follow.objects.filter(
                author=self.post.author,
                user=user_2
            ).exists()
        )

    def test_unfollow_profile(self):
        """Функция unfollow работают корректно"""
        follow_count = Follow.objects.count()
        Follow.objects.create(author=self.post.author, user=self.user)
        response = self.authorized_client.get(reverse(
            'profile_unfollow', kwargs={'username': self.user.username}))
        self.assertRedirects(response, reverse(
            'profile', kwargs={'username': self.user.username}))
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_profile_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        comment_count = Comment.objects.count()
        Comment.objects.create(author=self.post.author,
                               post=self.post, text='комментарий')
        response = self.authorized_client.get(reverse(
            'add_comment', kwargs={'username': self.user.username,
                                   'post_id': self.post.id}))
        self.assertRedirects(response, reverse(
            'post', kwargs={'username': self.user.username,
                            'post_id': self.post.id}))
        self.assertEqual(Comment.objects.count(), comment_count+1)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            text='Тестовый текст 1',
            author=User.objects.create_user(username='Хаски'))

        for i in range(2, 14):
            Post.objects.create(
                text=f'Тестовый текст {i}',
                author=User.objects.get(username='Хаски')
            )

    def setUp(self):
        self.client = Client()
        cache.clear()

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)
        response = self.client.get(reverse(
            'profile', kwargs={'username': self.post.author}))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page_contains_three_records(self):
        response = self.client.get(reverse('index') + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 3)
        response = self.client.get(reverse(
            'profile', kwargs={'username': self.post.author}) + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 3)
