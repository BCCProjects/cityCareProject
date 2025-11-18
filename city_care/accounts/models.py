from __future__ import annotations

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.models import PermissionsMixin
from django.core import validators
from django.db import models
from django.utils import timezone


class State(models.Model):
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=2, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return self.name


class City(models.Model):
    name = models.CharField(max_length=100)
    state = models.ForeignKey(State, related_name="cities", on_delete=models.CASCADE)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["name", "state"], name="unique_city_per_state"),
        ]

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return f"{self.name} - {self.state.abbreviation}"


class Organization(models.Model):
    name = models.CharField(max_length=150)
    city = models.OneToOneField(City, related_name="organization", on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return self.name


class EmployeeManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields):
        if not email:
            raise ValueError("Email is required for employees.")
        if not extra_fields.get("organization"):
            raise ValueError("Employees must be linked to an organization.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser precisa ter is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser precisa ter is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class AdministratorManager(EmployeeManager):
    """Backward compatibility alias used by historic migrations."""


class Employee(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField("Email", unique=True)
    first_name = models.CharField("Nome", max_length=150)
    last_name = models.CharField("Sobrenome", max_length=150, blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="employees",
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = ["first_name", "organization"]

    objects = EmployeeManager()

    class Meta:
        verbose_name = "Employee"
        verbose_name_plural = "Employees"

    def get_full_name(self) -> str:
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return self.email


class Administrator(Employee):
    objects = AdministratorManager()

    class Meta:
        proxy = True
        verbose_name = "Administrator"
        verbose_name_plural = "Administrators"


class Citizen(models.Model):
    email = models.EmailField("Email", unique=True)
    first_name = models.CharField("Nome", max_length=150)
    last_name = models.CharField("Sobrenome", max_length=150, blank=True)
    password = models.CharField("Senha", max_length=128)
    phone = models.CharField(
        "Telefone",
        max_length=20,
        validators=[validators.RegexValidator(r"^[0-9()+\-\s]{8,20}$", "Telefone invalido")],
    )
    city = models.ForeignKey(City, related_name="citizens", on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cidadao"
        verbose_name_plural = "Cidadaos"

    def set_password(self, raw_password: str) -> None:
        self.password = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password(raw_password, self.password)

    @property
    def state(self) -> State | None:
        if self.city_id:
            return self.city.state
        return None

    @property
    def is_authenticated(self) -> bool:  # pragma: no cover - compatibilidade DRF
        return True

    @property
    def is_anonymous(self) -> bool:  # pragma: no cover - compatibilidade DRF
        return False

    def save(self, *args, **kwargs):
        if not self.password.startswith("pbkdf2_"):
            raise ValueError("A senha precisa ser definida via set_password.")
        return super().save(*args, **kwargs)

    def get_full_name(self) -> str:
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name
