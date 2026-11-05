import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="GenerationActivity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("activity_date", models.DateField(unique=True, verbose_name="Дата")),
                ("generation_count", models.PositiveIntegerField(default=0, verbose_name="Количество генераций")),
            ],
            options={"verbose_name": "Активность", "verbose_name_plural": "Активность", "ordering": ["activity_date"]},
        ),
        migrations.CreateModel(
            name="MemeTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=50, verbose_name="Название")),
                ("category", models.CharField(max_length=30, verbose_name="Категория")),
                ("top_text", models.CharField(blank=True, max_length=120, verbose_name="Верхняя подпись")),
                ("bottom_text", models.CharField(blank=True, max_length=120, verbose_name="Нижняя подпись")),
                ("image", models.ImageField(blank=True, upload_to="memes/%Y/%m/", verbose_name="Изображение")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
            ],
            options={"verbose_name": "Шаблон мема", "verbose_name_plural": "Шаблоны мемов", "ordering": ["-created_at", "title"]},
        ),
    ]