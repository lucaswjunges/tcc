from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Nome da Categoria')
    slug = models.SlugField(max_length=100, unique=True, verbose_name='URL Slug')
    description = models.TextField(blank=True, verbose_name='Descrição')
    is_active = models.BooleanField(default=True, verbose_name='Ativo?')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('blog:category-detail', args=[self.slug])


class Tag(models.Model):
    name = models.CharField(max_length=50, verbose_name='Nome da Tag')
    slug = models.SlugField(max_length=50, unique=True, verbose_name='URL Slug')
    is_active = models.BooleanField(default=True, verbose_name='Ativo?')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('blog:tag-detail', args=[self.slug])


class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Usuário')
    display_name = models.CharField(max_length=100, blank=True, verbose_name='Nome para exibição')
    bio = models.TextField(blank=True, null=True, verbose_name='Biografia')
    is_verified = models.BooleanField(default=False, verbose_name='Verificado?')
    website = models.URLField(blank=True, null=True, verbose_name='Site')
    profile_image = models.ImageField(upload_to='authors/', blank=True, null=True, verbose_name='Imagem do Perfil')
    joined_date = models.DateTimeField(default=timezone.now, verbose_name='Data de Cadastro')

    class Meta:
        verbose_name = 'Autor'
        verbose_name_plural = 'Autores'

    def __str__(self):
        return f'{self.user.username} ({self.display_name})'

    def get_absolute_url(self):
        return reverse('blog:author-detail', args=[str(self.user.id)])


class Post(models.Model):
    title = models.CharField(max_length=200, verbose_name='Título')
    slug = models.SlugField(max_length=200, unique=True, verbose_name='URL Slug')
    content = models.TextField(verbose_name='Conteúdo')
    excerpt = models.TextField(blank=True, null=True, verbose_name='Excerto')
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='posts', verbose_name='Autor')
    categories = models.ManyToManyField(Category, related_name='posts', blank=True, verbose_name='Categorias')
    tags = models.ManyToManyField(Tag, related_name='posts', blank=True, verbose_name='Tags')
    published_date = models.DateTimeField(auto_now_add=True, verbose_name='Data de Publicação')
    last_updated = models.DateTimeField(auto_now=True, verbose_name='Última Atualização')
    is_published = models.BooleanField(default=True, verbose_name='Publicado?')
    featured = models.BooleanField(default=False, verbose_name='Destacado?')
    read_time = models.PositiveIntegerField(blank=True, null=True, verbose_name='Tempo de Leitura (minutos)')

    class Meta:
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'
        ordering = ['-published_date']
        indexes = [
            models.Index(fields=['published_date']),
            models.Index(fields=['is_published'])
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog:post-detail', args=[self.slug])

    def save(self, *args, **kwargs):
        # Placeholder for word count and read time calculation
        super().save(*args, **kwargs)


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name='Post')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Autor')
    content = models.TextField(verbose_name='Conteúdo')
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, blank=True, null=True, related_name='replies', verbose_name='Resposta a'
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Criado em')
    is_approved = models.BooleanField(default=False, verbose_name='Aprovado?')
    is_active = models.BooleanField(default=True, verbose_name='Ativo?')

    class Meta:
        verbose_name = 'Comentário'
        verbose_name_plural = 'Comentários'
        ordering = ['-created_at']

    def __str__(self):
        return f'Comentário de {self.author} em {self.post.title[:50]}...'

    def get_absolute_url(self):
        return reverse('blog:comment-detail', args=[str(self.id)])

    def reply_to(self):
        return self.parent

    def is_root_comment(self):
        return self.parent is None

