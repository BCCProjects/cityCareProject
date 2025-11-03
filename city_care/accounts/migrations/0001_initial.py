from django.db import migrations, models
import accounts.models
import django.core.validators
import django.utils.timezone


def create_default_organization(apps, schema_editor):
    State = apps.get_model("accounts", "State")
    City = apps.get_model("accounts", "City")
    Organization = apps.get_model("accounts", "Organization")

    state, _ = State.objects.get_or_create(abbreviation="DF", defaults={"name": "Distrito Federal"})
    city, _ = City.objects.get_or_create(name="Brasilia", state=state)
    Organization.objects.get_or_create(name="Default Organization", city=city)


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="State",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("abbreviation", models.CharField(max_length=2, unique=True)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="City",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("state", models.ForeignKey(on_delete=models.CASCADE, related_name="cities", to="accounts.state")),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Organization",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("city", models.OneToOneField(on_delete=models.PROTECT, related_name="organization", to="accounts.city")),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Citizen",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email", models.EmailField(max_length=254, unique=True, verbose_name="Email")),
                ("first_name", models.CharField(max_length=150, verbose_name="Nome")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="Sobrenome")),
                ("password", models.CharField(max_length=128, verbose_name="Senha")),
                (
                    "phone",
                    models.CharField(
                        max_length=20,
                        validators=[django.core.validators.RegexValidator("^[0-9()+\\-\\s]{8,20}$", "Telefone invalido")],
                        verbose_name="Telefone",
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("city", models.ForeignKey(on_delete=models.PROTECT, related_name="citizens", to="accounts.city")),
            ],
            options={
                "verbose_name": "Cidadao",
                "verbose_name_plural": "Cidadaos",
            },
        ),
        migrations.CreateModel(
            name="Employee",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                ("email", models.EmailField(max_length=254, unique=True, verbose_name="Email")),
                ("first_name", models.CharField(max_length=150, verbose_name="Nome")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="Sobrenome")),
                ("is_active", models.BooleanField(default=True)),
                ("is_staff", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=models.PROTECT, related_name="employees", to="accounts.organization"
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "Employee",
                "verbose_name_plural": "Employees",
            },
            managers=[
                ("objects", accounts.models.EmployeeManager()),
            ],
        ),
        migrations.AddConstraint(
            model_name="city",
            constraint=models.UniqueConstraint(fields=("name", "state"), name="unique_city_per_state"),
        ),
        migrations.RunPython(create_default_organization, migrations.RunPython.noop),
    ]
