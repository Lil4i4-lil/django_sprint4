from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import models


class BaseModel(models.Model):
    is_published = models.BooleanField(default=True, null=False, blank=False,
                                       verbose_name='Опубликовано',
                                       help_text='Снимите галочку, '
                                                 'чтобы скрыть публикацию.')
    created_at = models.DateTimeField(auto_now_add=True, null=False,
                                      blank=False,
                                      verbose_name='Добавлено')

    class Meta:
        abstract = True


class Post(BaseModel):
    title = models.CharField(max_length=256, null=False, blank=False,
                             verbose_name='Заголовок')
    text = models.TextField(null=False, blank=False,
                            verbose_name='Текст')
    pub_date = models.DateTimeField(null=False, blank=False,
                                    verbose_name='Дата и время публикации',
                                    help_text='Если установить '
                                              'дату и время в будущем — '
                                              'можно делать отложенные '
                                              'публикации.')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False,
                               blank=False,
                               verbose_name='Автор публикации')
    location = models.ForeignKey('Location', on_delete=models.SET_NULL,
                                 null=True,
                                 blank=True,
                                 verbose_name='Местоположение')
    category = models.ForeignKey('Category', on_delete=models.SET_NULL,
                                 null=True,
                                 blank=False,
                                 verbose_name='Категория')
    image = models.ImageField("Image", upload_to='posts_images', blank=True, null=True)

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'

    def __str__(self):
        return self.title


class Category(BaseModel):
    title = models.CharField(max_length=256, null=False, blank=False,
                             verbose_name='Заголовок')
    description = models.TextField(null=False, blank=False,
                                   verbose_name='Описание')
    slug = models.SlugField(unique=True, null=False, blank=False,
                            verbose_name='Идентификатор',
                            help_text='Идентификатор страницы для URL; '
                                      'разрешены символы латиницы, '
                                      'цифры, дефис и подчёркивание.')

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.title


class Location(BaseModel):
    name = models.CharField(max_length=256, null=False, blank=False,
                            verbose_name='Название места')

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return self.name


class Comment(models.Model):
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        ordering = ('-created_at',)