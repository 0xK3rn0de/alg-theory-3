from django.db import models


class MemeTemplate(models.Model):
    title = models.CharField("Название", max_length=50)
    category = models.CharField("Категория", max_length=30)
    top_text = models.CharField("Верхняя подпись", max_length=120, blank=True)
    bottom_text = models.CharField("Нижняя подпись", max_length=120, blank=True)
    image = models.ImageField("Изображение", upload_to="memes/%Y/%m/", blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "title"]
        verbose_name = "Шаблон мема"
        verbose_name_plural = "Шаблоны мемов"

    def __str__(self):
        return self.title


class GenerationActivity(models.Model):
    activity_date = models.DateField("Дата", unique=True)
    generation_count = models.PositiveIntegerField("Количество генераций", default=0)

    class Meta:
        ordering = ["activity_date"]
        verbose_name = "Активность"
        verbose_name_plural = "Активность"

    def __str__(self):
        return f"{self.activity_date}: {self.generation_count}"