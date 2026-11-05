from datetime import timedelta
from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from memes.models import GenerationActivity, MemeTemplate


@pytest.fixture
def meme_template(db):
    return MemeTemplate.objects.create(
        title="Понедельник",
        category="Работа",
        top_text="Я утром",
        bottom_text="Я после обеда",
    )


@pytest.fixture
def png_upload():
    stream = BytesIO()
    Image.new("RGB", (40, 30), color="orange").save(stream, format="PNG")
    return SimpleUploadedFile("sample.png", stream.getvalue(), content_type="image/png")


@pytest.mark.django_db
def test_dashboard_renders_template_and_seven_day_chart(client, meme_template):
    response = client.get(reverse("memes:dashboard"))

    assert response.status_code == 200
    assert "Понедельник" in response.content.decode()
    assert len(response.context["chart"]) == 7
    assert response.context["selected"] == meme_template


@pytest.mark.django_db
def test_fresh_database_has_starter_templates(client):
    titles = set(MemeTemplate.objects.values_list("title", flat=True))

    assert {"Понедельник", "Перед дедлайном", "Ожидание и реальность"} <= titles


@pytest.mark.django_db
def test_add_template_with_uploaded_image(client, settings, tmp_path, png_upload):
    settings.MEDIA_ROOT = tmp_path
    response = client.post(
        reverse("memes:dashboard"),
        {
            "action": "add_template",
            "title": "Новый мем",
            "category": "Тест",
            "top_text": "Сверху",
            "bottom_text": "Снизу",
            "image": png_upload,
        },
    )

    template = MemeTemplate.objects.get(title="Новый мем")
    assert response.status_code == 302
    assert template.image
    assert template.image.storage.exists(template.image.name)


@pytest.mark.django_db
def test_generation_activity_is_saved_and_shown_in_chart(client, meme_template):
    response = client.post(
        reverse("memes:dashboard"),
        {"action": "generate", "template_id": meme_template.pk},
    )

    today = timezone.localdate()
    activity = GenerationActivity.objects.get(activity_date=today)
    assert response.status_code == 302
    assert activity.generation_count == 1

    dashboard = client.get(reverse("memes:dashboard"))
    assert dashboard.context["weekly_total"] == 1
    assert dashboard.context["chart"][-1]["count"] == 1


@pytest.mark.django_db
def test_generation_activity_increments_each_time(client, meme_template):
    payload = {"action": "generate", "template_id": meme_template.pk}
    client.post(reverse("memes:dashboard"), payload)
    client.post(reverse("memes:dashboard"), payload)

    activity = GenerationActivity.objects.get(activity_date=timezone.localdate())
    assert activity.generation_count == 2


@pytest.mark.django_db
def test_template_requires_caption_or_image(client):
    response = client.post(
        reverse("memes:dashboard"),
        {"action": "add_template", "title": "Пусто", "category": "Тест"},
    )

    assert response.status_code == 200
    assert not MemeTemplate.objects.filter(title="Пусто").exists()
    assert "Добавьте хотя бы одну подпись или изображение." in response.context["form"].non_field_errors()


@pytest.mark.django_db
def test_chart_excludes_activity_older_than_seven_days(client):
    today = timezone.localdate()
    GenerationActivity.objects.create(activity_date=today - timedelta(days=8), generation_count=9)
    GenerationActivity.objects.create(activity_date=today, generation_count=2)

    response = client.get(reverse("memes:dashboard"))

    assert response.context["weekly_total"] == 2
    assert response.context["chart"][-1]["count"] == 2