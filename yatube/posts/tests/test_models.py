from django.contrib.auth import get_user_model

from ..models import Group, Post

User = get_user_model()


class PostModelTest():
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Тестовая группы",
            slug="Тестовый слаг",
            description="Тестовое описание"
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый текст"
        )

    def test_models_have_correct_objects_name(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(self.group, str(self.group))
        self.assertEqual(self.post, str(self.post.text[:15]))

    def test_verbose_name_post(self):
        post = PostModelTest.post
        field_verboses = {
            "author": "Автор",
            "group": "Группа",
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verboses_name, expected
                )

    def test_help_text(self):
        post = PostModelTest.post
        field_help_text = {
            "text": "Введите текст поста",
            "group": "Выберите группу",
        }
        for value, expected in field_help_text.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected
                )
