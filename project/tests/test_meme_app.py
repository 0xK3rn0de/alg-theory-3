import json
from datetime import date
from pathlib import Path
import sqlite3

import pytest
from PyQt6.QtGui import QColor, QImage, QPainter
from PyQt6.QtWidgets import QApplication

from meme_app import (
    DataStorageError,
    MemeMainWindow,
    MemeRepository,
    MemeTemplate,
    ValidationError,
)


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.mark.parametrize(
    ("title", "category", "top_text", "bottom_text"),
    [
        ("", "Категория", "Текст", ""),
        ("Название", "", "Текст", ""),
        ("Название", "Категория", "", "  "),
    ],
)
def test_template_validation_rejects_missing_required_fields(title, category, top_text, bottom_text):
    with pytest.raises(ValidationError):
        MemeTemplate.create(title, category, top_text, bottom_text)


def test_new_database_contains_default_templates(tmp_path):
    repository = MemeRepository(tmp_path / "memes.db")

    assert [item.template_id for item in repository.all()] == ["sample-01", "sample-02", "sample-03"]


def test_template_is_persisted_in_sqlite(tmp_path):
    database_path = tmp_path / "memes.db"
    repository = MemeRepository(database_path)
    template = MemeTemplate.create("Тест", "Учёба", "Сверху", "Снизу")

    repository.add(template)
    loaded = MemeRepository(database_path).all()
    with sqlite3.connect(database_path) as connection:
        table_names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}

    assert loaded[-1] == template
    assert "templates" in table_names


def test_legacy_json_is_imported_without_losing_old_templates(tmp_path):
    legacy_path = tmp_path / "memes.json"
    database_path = tmp_path / "memes.db"
    old_template = {
        "title": "Старый шаблон",
        "category": "Архив",
        "top_text": "Верх",
        "bottom_text": "Низ",
        "template_id": "legacy-01",
    }
    legacy_path.write_text(json.dumps([old_template], ensure_ascii=False), encoding="utf-8")

    migrated = MemeRepository(database_path).all()

    assert migrated == [MemeTemplate(**old_template)]
    assert migrated[0].image_path == ""


def test_invalid_legacy_json_raises_storage_error(tmp_path):
    (tmp_path / "memes.json").write_text("not json", encoding="utf-8")

    with pytest.raises(DataStorageError):
        MemeRepository(tmp_path / "memes.db")


def test_image_template_is_saved_and_rendered(tmp_path, qapp):
    image_path = tmp_path / "sample.png"
    image = QImage(80, 60, QImage.Format.Format_RGB32)
    image.fill(QColor("orange"))
    assert image.save(str(image_path))

    database_path = tmp_path / "memes.db"
    window = MemeMainWindow(MemeRepository(database_path))
    window.title_input.setText("Картинка")
    window.category_input.setText("Тест")
    window.top_input.setText("Сверху")
    window.bottom_input.setText("Снизу")
    window.image_path = str(image_path)
    window._add_template()

    loaded = MemeRepository(database_path).all()[-1]
    preview = window.preview
    rendered = QImage(preview.size(), QImage.Format.Format_ARGB32)
    painter = QPainter(rendered)
    preview.render(painter)
    painter.end()
    window.close()

    assert loaded.image_path == str(image_path)
    assert not preview.image.isNull()
    assert rendered.pixelColor(rendered.width() // 2, rendered.height() // 2) == QColor("orange")


def test_generation_updates_chart_and_activity_log(tmp_path, qapp):
    window = MemeMainWindow(MemeRepository(tmp_path / "memes.db"))
    window.generate_button.click()

    assert window.chart.counts[-1] == 1
    assert "Создан мем" in window.activity_log.toPlainText()
    window.close()


def test_activity_is_restored_after_window_reopens(tmp_path, qapp):
    database_path = tmp_path / "memes.db"
    first_window = MemeMainWindow(MemeRepository(database_path))
    first_window.generate_button.click()
    first_window.close()

    reopened_window = MemeMainWindow(MemeRepository(database_path))

    assert reopened_window.chart.counts[-1] == 1
    reopened_window.generate_button.click()
    reopened_window.close()

    counts = MemeRepository(database_path).activity_between(date.today(), date.today())
    assert counts[date.today()] == 2
