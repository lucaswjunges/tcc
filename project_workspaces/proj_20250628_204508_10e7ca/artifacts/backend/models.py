from django.db import models

# User Model (representing the portfolio owner)

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    bio = models.TextField(max_length=500, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


# Project Model

class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=1000)
    project_image = models.ImageField(upload_to='project_images/', blank=True, null=True)
    project_link = models.URLField(blank=True, null=True)
    github_link = models.URLField(blank=True, null=True)
    tags = models.ManyToManyField('Tag', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


# Tag Model for Projects

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


# Skill Model

class Skill(models.Model):
    name = models.CharField(max_length=100)
    proficiency_level = models.IntegerField(default=50, help_text="Level: 1-100")
    description = models.TextField(max_length=300, blank=True)

    def __str__(self):
        return self.name


# Experience Model

class Experience(models.Model):
    job_title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(max_length=1000)

    def __str__(self):
        return f"{self.job_title} at {self.company}"


# Education Model

class Education(models.Model):
    degree = models.CharField(max_length=200)
    institution = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    description = models.TextField(max_length=500, blank=True)

    def __str__(self):
        return f"{self.degree} at {self.institution}"


# Contact Model

class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField(max_length=500)
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name