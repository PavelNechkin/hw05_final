from datetime import datetime

from django.http import HttpRequest
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

from yatube.settings import PAGES
from .models import Follow, Post, Group, User, Comment
from .forms import PostForm, CommentForm


def index(request: HttpRequest) -> HttpResponse:
    """Создание страницы со свежими постами."""
    post_list = Post.objects.all()
    paginator = Paginator(post_list, PAGES)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request: HttpRequest, slug: str) -> HttpResponse:
    """Создание страницы с постами, отфильтрованными по группе."""
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.filter(group=group)
    paginator = Paginator(post_list, PAGES)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request: HttpRequest, username: str) -> HttpResponse:
    """Создание страницы профиля."""
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    count_posts = author.posts.count
    paginator = Paginator(posts, PAGES)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'author': author,
        'posts': posts,
        'page_obj': page_obj,
        'count_posts': count_posts,

    }
    return render(request, 'posts/profile.html', context)


def post_detail(request: HttpRequest, post_id: int) -> HttpResponse:
    """Создание страницы с описанием поста."""
    post = get_object_or_404(Post, pk=post_id)
    group = post.group
    author = post.author
    count_posts = author.posts.count
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post=post)
    context = {
        'post': post,
        'group': group,
        'author': author,
        'comments': comments,
        'count_posts': count_posts,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request: HttpRequest) -> HttpResponse:
    """Страница для создание новых постов."""
    author = request.user
    if request.method != 'POST':
        form = PostForm()
        context = {
            'form': form
        }
        return render(request, 'posts/create_post.html', context)
    form = PostForm(request.POST)
    if not form.is_valid():
        context = {
            'form': form,
        }
        return render(request, 'posts/create_post.html', context)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    post = form.save(commit=False)
    post.author = author
    post.pub_date = datetime.now()
    post.save()
    return redirect('posts:profile', author)


@login_required
def post_edit(request: HttpRequest, post_id: int) -> HttpResponse:
    """Создание страницы для редактирования постов."""
    author = request.user
    post = get_object_or_404(Post, id=post_id)
    if request.method != 'POST':
        form = PostForm()
        context = {
            'form': form,
            'is_edit': True,
        }
        return render(request, 'posts/create_post.html', context)
    form = PostForm(request.POST)
    if not form.is_valid():
        context = {
            'form': form,
            'is_edit': True,
        }
        return render(request, 'posts/create_post.html', context)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    post = form.save(commit=False)
    post.author = author
    post.save()
    return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request: HttpRequest, post_id: int) -> HttpResponse:
    """Функция для добавления комментов."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request: HttpRequest) -> HttpResponse:
    """Создание страницы с постами понравившихся авторов."""
    user = request.user
    post_list = Post.objects.filter(author__following__user=user)
    paginator = Paginator(post_list, PAGES)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request: HttpRequest, username: str) -> HttpResponse:
    """Функция, позволяющая подписаться на авторов."""
    author = get_object_or_404(User, username=username)
    count_posts = author.posts.count
    posts = author.posts.all()
    user = request.user
    following = Follow.objects.filter(
        user=user, author=author).exists()
    if author != user and following is False:
        Follow.objects.create(author=author, user=user)
    paginator = Paginator(posts, PAGES)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'author': author,
        'posts': posts,
        'page_obj': page_obj,
        'count_posts': count_posts,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


@login_required
def profile_unfollow(request: HttpRequest, username: str) -> HttpResponse:
    """Функция, позволяющая отписаться от авторов."""
    author = get_object_or_404(User, username=username)
    user = request.user
    follower = get_object_or_404(Follow, user=user, author=author)
    count_posts = author.posts.count
    posts = author.posts.all()
    follower.delete()
    following = Follow.objects.filter(
        user=user, author=author).exists()
    paginator = Paginator(posts, PAGES)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'author': author,
        'posts': posts,
        'page_obj': page_obj,
        'count_posts': count_posts,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)
