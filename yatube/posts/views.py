from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


@cache_page(20)
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, settings.QUANTITY_POSTS)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
    }
    return render(request, "posts/index.html", context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts_list = group.posts.all()
    paginator = Paginator(posts_list, settings.QUANTITY_POSTS)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "group": group,
        "page_obj": page_obj,
    }
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    profile_list = author.posts.all()
    paginator = Paginator(profile_list, settings.QUANTITY_POSTS)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    following = Follow.objects.filter(author=author)
    following if request.user.is_authenticated else False
    context = {
        "author": author,
        "page_obj": page_obj,
        "following": following,
    }
    return render(request, "posts/profile.html", context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        "post": post,
        "comments": comments,
        "form": form,
    }
    return render(request, "posts/post_detail.html", context)


@login_required
def post_create(request):
    """Функция создания нового поста"""
    form = PostForm(request.POST or None)
    if form.is_valid():
        form.instance.author = request.user
        form.save()
        return redirect("posts:profile", username=request.user)
    return render(request, "posts/create_post.html", {"form": form, })


@login_required
def post_edit(request, post_id):
    """Функция редактирования поста"""
    is_edit = True
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect("posts:post_detail", post_id=post.id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id=post.id)
    else:
        return render(request, "posts/create_post.html",
                      {"form": form, "post": post, "is_edit": is_edit, })


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def follow_index(request):
    """Страница постов тех авторов, на которых подписан пользователь"""
    posts_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts_list, settings.QUANTITY_POSTS)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
    }
    return render(request, "posts/follow.html", context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user,
                                     author=author)
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    """Отписка от автора"""
    get_object_or_404(
        Follow,
        user=request.user,
        author__username=username
    ).delete()
    return redirect("posts:profile", username=username)
