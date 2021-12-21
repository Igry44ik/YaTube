import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()

USERNAME = "Test"

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.group = Group.objects.create(
            title="test-group",
            slug="test-slug",
        )
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
        cls.post = Post.objects.create(
            text="Тестовый текст",
            author=cls.user,
            group=cls.group,
            image=uploaded
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cache.clear()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def tets_pages_uses_correct_template(self):
        template_pages_names = {
            "posts/index.html": reverse("posts:index"),
            "posts/group_list.html": reverse("posts:slug",
                                             args={"slug": self.group.slug}),
            "posts/profile.html": reverse("posts:profile"),
            "posts/post_detail.html": reverse("posts:post_detail",
                                              args=[self.post.id]),
            "posts/create_post.html": reverse("posts:post_create"),
        }
        for template, reverse_name in template_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_correct_context(self):
        templates_pages_names = {
            reverse("posts:index"),
            reverse("posts:slug", kwargs={"slug": self.group.slug}),
            reverse("posts:profile", kwargs={"username": self.user.username}),
            reverse("posts:post_detail", args=[self.post.id]),
        }
        for reverse_name in templates_pages_names:
            cache.clear()
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                if reverse_name == reverse("posts:post_detail",
                                           args=[self.post.id]):
                    first_object = response.context["post"]
                else:
                    first_object = response.context.get("page_obj")[0]
                    post_author_0 = first_object.author
                    post_id_0 = first_object.pk
                    post_text_0 = first_object.text
                    post_group_0 = first_object.group.slug
                    post_image_0 = first_object.image
                    self.assertEqual(post_text_0, self.post.text)
                    self.assertEqual(post_id_0, self.post.pk)
                    self.assertEqual(post_author_0, self.post.author)
                    self.assertEqual(post_group_0, self.group.slug)
                    self.assertEqual(post_image_0, self.post.image)

    def test_post_edit_correct_context(self):
        response = self.authorized_client.get(reverse("posts:post_edit",
                                                      args=[self.post.id]))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_post_correct_context(self):
        response = self.authorized_client.get(reverse("posts:post_create"))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_in_main_page(self):
        """Новый пост отображается на главной странице
            и на странице группы.
        """
        cache.clear()
        url = ((reverse("posts:index")),
               reverse("posts:slug", kwargs={"slug": self.group.slug}),)
        for urls in url:
            with self.subTest(url=url):
                response = self.authorized_client.get(urls)
                self.assertEqual(len(response.context["page_obj"]), 1)

    def test_post_in_profile_page(self):
        url = reverse("posts:profile", args=[USERNAME])
        response = self.authorized_client.get(url)
        self.assertEqual(response.context.get("author"), self.user)

    def test_post_not_in_your_group(self):
        """Новый пост попал не в свою группу."""
        url = reverse("posts:slug", kwargs={"slug": self.group.slug},)
        response = self.authorized_client.get(url)
        self.assertNotEqual(response.context.get("page_obj"), self.post)

    def test_authorized_client_allowed_to_add_comment(self):
        '''Авторизованный пользователь может оставлять комментарий.'''
        comment_quantity = Comment.objects.count()
        form_data = {
            "text": "Comment"
        }
        self.authorized_client.post(
            reverse("posts:add_comment",
                    kwargs={"post_id": self.post.id, }),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_quantity + 1)

    def test_guest_client_not_allowed_to_add_comment(self):
        '''Неавторизованный пользователь не может оставлять комментарий.'''
        comment_quantity = Comment.objects.count()
        form_data = {"text": "Оставляем комментарий"}
        self.client.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.id, }),
            data=form_data,
            follow=True
        )
        self.assertNotEqual(Comment.objects.count(), comment_quantity + 1)

    def test_cache(self):
        url = reverse("posts:index")
        response = self.client.get(url).content
        Post.objects.create(
            text="Текст тестовый",
            group=self.group,
            author=self.user
        )
        self.assertEqual(response, self.client.get(url).content)
        cache.clear()
        self.assertNotEqual(response, self.client.get(url).content)


class TestPaginator(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.authorized_client = Client()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.group = Group.objects.create(
            title="test-group",
            slug="test-slug",
        )
        cls.post = (Post(
            author=cls.user,
            group=cls.group,
            text="тестовый текст") for i in range(settings.QUANTITY_POSTS))
        Post.objects.bulk_create(cls.post)

    def test_paginator(self):
        urls = [
            reverse("posts:index"),
            reverse("posts:slug", kwargs={"slug": self.group.slug, }),
            reverse("posts:profile", args=[USERNAME])
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    len(response.context["page_obj"]),
                    settings.QUANTITY_POSTS)
