from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings


class Client(models.Model):
    name = models.CharField(max_length=255)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, role="user", client=None):
        if not email:
            raise ValueError("Users must have an email")
        user = self.model(email=self.normalize_email(email), name=name, role=role, client=client)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, role="admin", client=None):
        user = self.create_user(email=email, name=name, password=password, role=role, client=client)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('viewer', 'Viewer'),
    )

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'role']

    def __str__(self):
        return self.email


class InsuranceEdit(models.Model):
    client = models.ForeignKey('Client', on_delete=models.CASCADE)

    payer_name = models.CharField(max_length=255)
    payer_category = models.CharField(max_length=255)
    edit_type = models.CharField(max_length=50)
    edit_sub_category = models.CharField(max_length=255, blank=True, null=True)
    instruction = models.TextField()

    version = models.CharField(max_length=50)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.payer_name} - {self.edit_type} - {self.version}"


class ModifierRule(models.Model):
    client = models.ForeignKey('Client', on_delete=models.CASCADE)

    payer_name = models.CharField(max_length=255)
    payer_category = models.CharField(max_length=255)
    code_type = models.CharField(max_length=100)
    code_list = models.TextField(help_text="Comma-separated list of codes")
    sub_category = models.CharField(max_length=255, blank=True, null=True)
    modifier_instruction = models.TextField()

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.payer_name} - {self.code_type} - {self.sub_category or ''}"


class ModelAccessPermission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    model_name = models.CharField(max_length=100)
    can_view = models.BooleanField(default=False)
    can_add = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'model_name')
