import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm

from ..models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

USERNAME = "Test-User"


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.group = Group.objects.create(
            title="Тестовый заголовок",
            slug="test-slug",
            description="Тестовое описание"
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text="Тестовый текст"
        )
        cls.form = PostForm()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        posts_count = Post.objects.count()
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
        form_data = {
            "text": "Тестовый текст",
            "group": self.group.id,
            "image": uploaded,
        }
        response = self.authorized_client.post(
            reverse("posts:post_create"),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse("posts:profile",
                                               args=[USERNAME]))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        last_post = Post.objects.latest("id")
        self.assertEqual(last_post.text, form_data["text"])
        self.assertEqual(last_post.group.id, form_data["group"])
        self.assertFalse(last_post.image is None)

    def test_post_edit(self):
        form_data = {
            "text": "Новый пост",
            "group": self.group.pk,
        }
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse("posts:post_edit", kwargs={"post_id": self.post.pk}),
            data=form_data,
            follow=True
        )
        post_response = response.context["post"]
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(post_response.text, form_data["text"])
        self.assertEqual(post_response.author, self.user)
        self.assertEqual(post_response.group.pk, form_data["group"])
        self.assertRedirects(response,
                             reverse("posts:post_detail",
                                     kwargs={"post_id": self.post.pk}))

    def test_anonymous_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            "text": "Тестовый текст",
            "group": self.group.id,
        }
        response = self.client.post(
            reverse("posts:post_create"),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(response, (reverse("users:login") + "?next="
                                        + reverse("posts:post_create")))

    def test_anonymous_edit_post(self):
        posts_count = Post.objects.count()
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
        form_data = {
            "text": "Тест",
            "group": "other",
            "image": uploaded,
        }
        response = self.client.post(
            reverse("posts:post_edit", kwargs={"post_id": self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(response, (reverse("users:login")) + "?next="
                             + (reverse("posts:post_edit",
                                        kwargs={"post_id": self.post.pk})))
        post = Post.objects.get(id=self.post.id)
        self.assertNotEqual(post.text, form_data["text"])
        self.assertNotEqual(post.group.id, form_data["group"])
        self.assertNotEqual(post.image, form_data["image"])
