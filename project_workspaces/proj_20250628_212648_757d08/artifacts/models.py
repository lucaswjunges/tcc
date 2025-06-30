from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('post-list-category', args=[self.slug])


class Tag(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('post-list-tag', args=[self.slug])


class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    join_date = models.DateTimeField(default=timezone.now)
    profile_image = models.ImageField(upload_to='authors/', blank=True, null=True)

    def __str__(self):
        return self.user.username


class Post(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    content = models.TextField()
    created_on = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft'
    )
    categories = models.ManyToManyField(
        Category,
        related_name='posts'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='posts'
    )

    class Meta:
        ordering = ['-created_on']
        indexes = [
            models.Index(fields=['created_on']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post-detail', args=[self.id, self.slug])


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.CharField(max_length=100)
    author_email = models.EmailField()
    content = models.TextField()
    created_on = models.DateTimeField(default=timezone.now)
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_on']
        indexes = [
            models.Index(fields=['created_on', 'is_approved']),
        ]

    def __str__(self):
        return f"Comment by {self.author} on {self.post.title[:50]}..."

    def get_absolute_url(self):
        return self.post.get_absolute_url()