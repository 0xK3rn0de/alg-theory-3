from django.db import migrations


def seed_templates(apps, schema_editor):
    MemeTemplate = apps.get_model("memes", "MemeTemplate")
    defaults = [
        ("Понедельник", "Работа", "Я: сегодня лягу пораньше", "Также я в 02:47: ещё одно видео"),
        ("Перед дедлайном", "Учёба", "До срока ещё целая неделя", "Осталось 3 минуты"),
        ("Ожидание и реальность", "Жизнь", "План на выходные", "Фактический план на выходные"),
    ]
    for title, category, top_text, bottom_text in defaults:
        MemeTemplate.objects.get_or_create(
            title=title,
            defaults={"category": category, "top_text": top_text, "bottom_text": bottom_text},
        )


class Migration(migrations.Migration):
    dependencies = [("memes", "0001_initial")]

    operations = [migrations.RunPython(seed_templates, migrations.RunPython.noop)]