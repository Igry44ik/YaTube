from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()

USERNAME = "Test"


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.group = Group.objects.create(
            title="Тестовый заголовок",
            slug="test-slug",
            description="Тестовый текст"
        )
        cls.post = Post.objects.create(
            text="Тестовый текст",
            author=cls.user,
            group=cls.group
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_page_for_guest_client(self):
        page_url = {
            "/": 200,
            "/about/author/": 200,
            "/about/tech/": 200,
            f"/group/{self.group.slug}/": 200,
            f"/posts/{self.post.id}/": 200,
            f"/profile/{USERNAME}/": 200,
        }
        for url, status_code in page_url.items():
            with self.subTest(url=url, status_code=status_code):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test__page_for_authorized_client(self):
        page_url = {
            "/create/": 200,
            reverse("posts:post_edit", args=[self.post.id]): 200,
        }
        for url, status_code in page_url.items():
            with self.subTest(url=url, status_code=status_code):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_unexisting_page(self):
        """Несуществующая страница"""
        response = self.client.get("/unexisting_page/")
        self.assertEqual(response.status_code, 404)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            "posts/index.html": "/",
            "posts/create_post.html": "/create/",
            "posts/group_list.html": reverse("posts:slug",
                                             args=[self.group.slug]),
            "posts/profile.html": reverse("posts:profile", args=[USERNAME]),
            "posts/post_detail.html": reverse("posts:post_detail",
                                              args=[self.post.id]),
        }
        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_post_edit_correct_template(self):
        response = self.authorized_client.get(reverse("posts:post_edit",
                                              args=[self.post.id]))
        self.assertTemplateUsed(response, "posts/create_post.html")
