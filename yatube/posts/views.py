from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Comment, Follow, Group, Post, User


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, settings.PER_PAGE_COUNT)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request, 'index.html',
        {'page': page}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.post_set.all()
    paginator = Paginator(posts, settings.PER_PAGE_COUNT)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request, 'group.html',
        {'group': group, 'page': page, }
    )


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts_of_author = author.posts.all()
    paginator = Paginator(posts_of_author, settings.PER_PAGE_COUNT)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    form = CommentForm()
    following = False
    if request.user.is_authenticated:
        if author.following.filter(user=request.user).exists():
            following = True
    return render(
        request, 'posts/profile.html',
        {'author': author,
         'page': page, 'form': form,
         'following': following
         }
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    comments = Comment.objects.filter(post=post)
    form = CommentForm(request.POST or None)
    return render(
        request, 'posts/post.html',
        {'form': form, 'post': post,
         'author': post.author, 'post_id': post_id,
         'username': username, 'comments': comments
         }
    )


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    return render(
        request, 'posts/new.html',
        {'form': form, 'is_edit': False}
    )


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    if post.author != request.user:
        return redirect('post', username, post_id)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('post', username, post_id)

    return render(
        request, 'posts/new.html',
        {'form': form, 'post_id': post_id,
         'post': post, 'username': username,
         'is_edit': True}
    )


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {'path': request.path}, status=404)


def server_error(request):
    return render(request, 'misc/500.html', status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('post', username=username, post_id=post_id)


@login_required
def follow_index(request):
    user = request.user
    post = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post, settings.PER_PAGE_COUNT)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {'page': page, 'user': user})


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if request.user == author:
        return redirect('profile', username=username)
    follow = Follow(user=user, author=author)
    if author.following.filter(user=request.user).exists():
        return redirect('profile', username=username)
    follow.save()
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(author=author, user=request.user)
    follow.delete()
    return redirect('profile', username=username)
