import shutil
import tempfile

from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from posts.models import Follow, Group, Post, User
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        # Создаем неавторизованный клиент
        cls.guest_client = Client()
        # Создаем авторизованый клиент
        cls.user = User.objects.create(username='User')
        cls.second_user = User.objects.create(username='Second_User')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client.force_login(cls.second_user)
        # Создадим группу в БД
        cls.group = Group.objects.create(
            title='Первая группа',
            slug='test-slug',
            description='Описание группы'
        )
        # Создадим вторую группу в БД
        cls.second_group = Group.objects.create(
            title='Вторая группа',
            slug='test-slug-new',
            description='Отличная группа от тестовой'
        )
        # Создадим 13 постов в первой группе БД
        for post in range(13):
            cls.post = Post.objects.create(
                text='Записи первой группы',
                author=cls.user,
                group=cls.group,
                image=uploaded
            )

        # Создадим 2 поста во второй группе в БД
        for post in range(2):
            cls.post = Post.objects.create(
                text='Записи второй группы',
                author=cls.second_user,
                group=cls.second_group,
                image=uploaded
            )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}): (
                'posts/group_list.html'
            ),
            reverse('posts:profile', kwargs={'username': 'User'}): (
                'posts/profile.html'
            ),
            reverse('posts:post_detail', kwargs={'post_id': 13}): (
                'posts/post_detail.html'
            ),
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': 14}): (
                'posts/create_post.html'
            ),
        }
        # Проверяем, что при обращении к name вызывается
        # соответствующий HTML-шаблон
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Проверка словаря контекста главной страницы
    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        # Изображение передаётся в словаре context
        post_image = Post.objects.first().image
        self.assertEqual(post_image, 'posts/small.gif')

    def test_group_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'})
        )
        self.assertIn('group', response.context)
        self.assertEqual(response.context['group'], self.group)
        self.assertIn('page_obj', response.context)
        self.assertIn('title', response.context)
        self.assertIn('description', response.context)
        # Изображение передаётся в словаре context
        post_image = Post.objects.first().image
        self.assertEqual(post_image, 'posts/small.gif')

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'User'})
        )
        self.assertIn('author', response.context)
        self.assertEqual(response.context['author'], self.user)
        self.assertIn('posts', response.context)
        self.assertIn('posts_count', response.context)
        self.assertIn('page_obj', response.context)
        self.assertEqual(response.context['author'], self.user)
        # Изображение передаётся в словаре context
        post_image = Post.objects.first().image
        self.assertEqual(post_image, 'posts/small.gif')

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': (self.post.pk)})
        )
        self.assertIn('post', response.context)
        self.assertIn('posts_count', response.context)
        self.assertIn('title', response.context)
        # Изображение передаётся в словаре context
        post_image = Post.objects.first().image
        self.assertEqual(post_image, 'posts/small.gif')

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', args=(self.post.pk,)))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_paginator_first_page_contains_ten_records(self):
        response = self.guest_client.get(reverse('posts:index'))
        # Проверка: количество постов из созданной группs
        # на первой странице равно 10.
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_paginator_second_page_contains_three_records(self):
        # Проверка: на второй странице должно быть три поста
        # первой группы и два второй.
        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 5)

    def test_paginator_group_list_contains_two_records(self):
        # Проверка: посты второй группы созданы в количестве двух штук.
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug-new'})
        )
        self.assertEqual(len(response.context['page_obj']), 2)

    def test_paginator_profile_contains_two_records(self):
        # Проверка: у второго пользователя всего 2 поста.
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': 'Second_User'})
        )
        self.assertEqual(len(response.context['page_obj']), 2)

    def test_cache_index(self):
        """Тест кэширования главной страницы."""
        first = self.authorized_client.get(reverse('posts:index'))
        post = Post.objects.get(pk=1)
        post.text = 'Измененный текст'
        post.save()
        second = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(first.content, second.content)
        cache.clear()
        third = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(first.content, third.content)


class FollowTests(TestCase):
    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.user_follower = User.objects.create(username='follower')
        self.user_following = User.objects.create(username='following')
        self.post = Post.objects.create(
            author=self.user_following,
            text='Тестовая запись для тестирования ленты'
        )
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)

    def test_follow(self):
        self.client_auth_follower.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_following.username}
            )
        )
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        self.client_auth_follower.get(reverse('posts:profile_follow',
                                              kwargs={'username':
                                                      self.user_following.
                                                      username}))
        self.client_auth_follower.get(reverse('posts:profile_unfollow',
                                      kwargs={'username':
                                              self.user_following.username}))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_subscription(self):
        """Запись появляется в ленте подписчиков."""
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        response = self.client_auth_follower.get('/follow/')
        post_text_0 = response.context['page_obj'][0].text
        self.assertEqual(post_text_0, 'Тестовая запись для тестирования ленты')
        # проверка, что запись не появилась у неподписанного пользователя
        response = self.client_auth_following.get('/follow/')
        self.assertNotEqual(response, 'Тестовая запись для тестирования ленты')

    def test_add_comment(self):
        """Проверка добавления комментария."""
        self.client_auth_following.post(f'/posts/{self.post.pk}/comment/',
                                        {'text': 'тестовый комментарий'},
                                        follow=True)
        response = self.client_auth_following.get(f'/posts/{self.post.pk}/')
        self.assertContains(response, 'тестовый комментарий')
        self.client_auth_following.logout()
        self.client_auth_following.post(f'/posts/{self.post.pk}/comment/',
                                        {'text': 'комментарий от гостя'},
                                        follow=True)
        response = self.client_auth_following.get(f'/posts/{self.post.pk}/')
        self.assertNotContains(response, 'комментарий от гостя')
