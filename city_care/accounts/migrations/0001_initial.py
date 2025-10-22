from __future__ import annotations

from django.db import migrations, models
import django.utils.timezone
import django.core.validators


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="Administrator",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, help_text="Designates that this user has all permissions without explicitly assigning them.", verbose_name="superuser status")),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("first_name", models.CharField(max_length=150)),
                ("last_name", models.CharField(blank=True, max_length=150)),
                ("is_active", models.BooleanField(default=True)),
                ("is_staff", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Administrador",
                "verbose_name_plural": "Administradores",
            },
        ),
        migrations.CreateModel(
            name="Citizen",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("full_name", models.CharField(max_length=255)),
                ("password", models.CharField(max_length=128)),
                ("phone", models.CharField(max_length=20, validators=[django.core.validators.RegexValidator("^[0-9()+\\-\\s]{8,20}$", "Telefone inválido")])),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Cidadão",
                "verbose_name_plural": "Cidadãos",
            },
        ),
        migrations.AddField(
            model_name="administrator",
            name="groups",
            field=models.ManyToManyField(blank=True, help_text="The groups this user belongs to.", related_name="administrator_set", related_query_name="administrator", to="auth.group", verbose_name="groups"),
        ),
        migrations.AddField(
            model_name="administrator",
            name="user_permissions",
            field=models.ManyToManyField(blank=True, help_text="Specific permissions for this user.", related_name="administrator_set", related_query_name="administrator", to="auth.permission", verbose_name="user permissions"),
        ),
    ]
