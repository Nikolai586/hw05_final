from django.shortcuts import render, get_object_or_404
from .forms import PostForm, CommentForm
from .models import Post, Group, Comment, Follow
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.views.decorators.cache import cache_page
User = get_user_model()

@cache_page(20)
def index(request):
    post_list = Post.objects.order_by("-pub_date").all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page, 'paginator': paginator})

def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.filter(group=group).order_by('-pub_date').all()
    paginator = Paginator(post_list, 10)
    page_namber = request.GET.get('page')
    page = paginator.get_page(page_namber)
    return render(request, 'group.html', {'paginator': paginator, 'page': page, 'group': group})

@login_required
def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST or None, files=request.FILES or None)
        if form.is_valid():
            new = Post.objects.create(author=request.user, text=form.cleaned_data['text'], group=form.cleaned_data['group'], image=form.cleaned_data['image'])
            new.save()
            return redirect('index')
    else:
        form = PostForm()
    return render(request, 'new.html', {'form': form})

def profile(request, username):
    profile = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author__username=username).order_by('-pub_date').all()
    paginator = Paginator(post_list, 10)
    page_namber = request.GET.get('page')
    page = paginator.get_page(page_namber)
    quantity = Post.objects.filter(author__username=username).count()
    author = User.objects.get(username=username)
    follow = Follow.objects.filter(author=profile)
    return render(request, "profile.html", {
        'page': page,
         'paginator': paginator,
          'quantity': quantity,
           'author': author,
            'profile': profile,
             'following': follow
             })

def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id, author=author)
    post_count = Post.objects.filter(author=post.author).count()
    form = CommentForm()
    comments = Comment.objects.filter(post=post).order_by('-created').all()
    return render(request, "post.html", {'post': post, 'post_count': post_count, 'author': author, 'form': form, 'comments': comments})


def post_edit(request, username, post_id):
    profile = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id, author=profile)
    if request.user != profile:
        return redirect("post", username=request.user.username, post_id=post_id)
    # добавим в form свойство files
    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect("post", username=request.user.username, post_id=post_id)

    return render(request, "new.html", {"form": form, "post": post})

def page_not_found(request, exception):
    return render(request, "misc/404.html", {"path": request.path}, status=404)

def server_error(request):
    return render(request, "misc/500.html", status=500)

@login_required
def add_comment(request, username, post_id):
    profile = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id, author=profile)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            new = Comment.objects.create(post=post, text=form.cleaned_data['text'], author=request.user)
            new.save()
            return redirect('post', username=post.author, post_id=post_id)
    else:
        form = CommentForm()
        comments = Comment.objects.filter(author=profile).order_by('-created').all()
    return render(request, 'comment.html', {'form': form, 'comments': comments, 'post': post})

@login_required
def follow_index(request):
    follow = Follow.objects.filter(user=request.user).all()
    authors = []
    for i in follow:
        authors.append(i.author)
    post_list = Post.objects.filter(author__in=authors).order_by('-pub_date').all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {'page': page, 'paginator': paginator})

@login_required
def profile_follow(request, username):
    profile = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=request.user, author=profile)
    if request.user != profile:
        if follow.count() < 1:
            Follow.objects.create(user=request.user, author=profile)
    return redirect('profile', username)

@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('profile', username)
    