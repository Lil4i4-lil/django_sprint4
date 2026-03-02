from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.views.generic import DetailView, CreateView, UpdateView, ListView, DeleteView

from .models import Post, Category, Comment
from .forms import PostForm, ProfileForm, CommentForm


class ProfileMixin:
    model = get_user_model()
    slug_field = 'username'
    slug_url_kwarg = 'username'


class PostMixin:
    model = Post
    form_class = PostForm


class ProfileCreateView(CreateView):
    template_name = 'registration/registration_form.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('blog:index')


class ProfileDetailView(ProfileMixin, DetailView):
    template_name = 'blog/profile.html'
    context_object_name = 'profile'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.get_object()
        posts = Post.objects.filter(
            author=user
        ).annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')

        paginator = Paginator(posts, 10)
        page_number = self.request.GET.get('page')

        context['page_obj'] = paginator.get_page(page_number)
        return context


class ProfileUpdateView(LoginRequiredMixin, ProfileMixin, UpdateView):
    template_name = 'blog/user.html'
    form_class = ProfileForm

    def get_success_url(self):
        username = self.request.user.username
        if not username:
            return reverse_lazy('blog:index')

        return reverse_lazy('blog:profile', kwargs={'username': self.request.user.username})


class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = 10

    def get_queryset(self):
        return Post.objects.select_related(
            'category', 'location', 'author'
                ).annotate(
                    comment_count=Count('comments')
                ).filter(
                    pub_date__lte=timezone.now(),
                    is_published=True,
                    category__is_published=True
                ).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Лента записей'
        return context


class PostCreateView(LoginRequiredMixin, PostMixin, CreateView):
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse_lazy('blog:profile', kwargs={'username': self.request.user.username})

    def form_valid(self, form):
        form.instance.author = get_user_model().objects.get(pk=self.request.user.pk)
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == 'POST':
            kwargs['files'] = self.request.FILES
        return kwargs


class PostDeleteView(PostMixin, DeleteView):
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        return reverse_lazy('blog:profile', kwargs={'username': self.request.user.username})

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)


class PostUpdateView(LoginRequiredMixin, PostMixin, UpdateView):
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def handle_no_permission(self):
        # Перенаправляем неавторизованных на страницу поста
        obj = self.get_object()
        post_id = obj.id
        return redirect('blog:post_detail', post_id=post_id)

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not request.user.is_authenticated:
            post_id = self.kwargs.get(self.pk_url_kwarg)
            return redirect('blog:post_detail', post_id=post_id)

        if self.object.author != request.user:
            raise PermissionDenied("Вы не можете редактировать чужие посты")

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'post_id': self.object.id})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == 'POST':
            kwargs['files'] = self.request.FILES
        return kwargs


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'
    context_object_name = 'post'

    def get_queryset(self):
        return Post.objects.select_related(
            'category', 'location', 'author'
        ).annotate(
            comment_count=Count('comments')
        )

    def get_object(self, queryset=None):
        post = super().get_object(queryset)

        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = self.object.title
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.order_by('created_at').select_related('author')

        return context


def category_posts(request, category_slug):
    """Страница с постами определенной категории."""
    category = get_object_or_404(Category, slug=category_slug)

    # Проверка публикации категории
    if not category.is_published:
        raise Http404("Категория не найдена или недоступна")

    # Получение опубликованных постов категории
    post_list = Post.objects.select_related(
        'category', 'location', 'author'
    ).filter(
        category=category,  # Лучше использовать объект, чем slug
        is_published=True,
        pub_date__lte=timezone.now()
    ).annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')

    context = {
        'title': f'Публикации в категории "{category.title}"',
        'category': category,
        'page_obj': paginator.get_page(page_number),
    }
    return render(request, 'blog/category.html', context)

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    post = get_object_or_404(Post, pk=post_id)
    comment = get_object_or_404(Comment, pk=comment_id, post=post)

    if comment.author != request.user:
        raise Http404("Вы не можете редактировать этот комментарий")

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm(instance=comment)

    context = {
        'form': form,
        'comment': comment,
        'post': post,
    }

    return render(request, 'blog/comment.html', context)


@login_required
def delete_comment(request, post_id, comment_id):
    post = get_object_or_404(Post, pk=post_id)
    comment = get_object_or_404(Comment, pk=comment_id, post=post)

    if comment.author != request.user:
        raise Http404("Вы не можете редактировать этот комментарий")

    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)

    context = {
        'comment': comment,
        'post': post,
    }

    return render(request, 'blog/comment.html', context)