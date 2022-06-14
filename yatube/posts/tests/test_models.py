from django.test import TestCase
from posts.models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='User')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост с длинной имени более 15 символов',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__.""" 
        group = PostModelTest.group
        post = PostModelTest.post
        corteg = (
            (self.group, self.group.title),
            (self.post, self.post.text[:15]),
        )
        for value, expected in corteg:
            with self.subTest(value=value):
                self.assertEqual(str(value), expected)

    def test_help_text(self):
        """Проверяем, что корректно отображается help text."""
        post = PostModelTest.post
        field_help_texts = {
            'group': 'Группа, к которой будет относиться пост',
            'text': 'Текст нового поста',
            'image': 'Картинка',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected
                )
