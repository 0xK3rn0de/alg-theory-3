import tempfile
import unittest
from pathlib import Path

from PyQt6.QtGui import QColor, QImage, QPainter
from PyQt6.QtWidgets import QApplication

from meme_app import MemeMainWindow, MemePreview, MemeRepository, MemeTemplate, ValidationError


class MemeAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])

    def test_template_requires_at_least_one_caption(self) -> None:
        with self.assertRaises(ValidationError):
            MemeTemplate.create("Название", "Категория", "  ", "  ")

    def test_templates_are_saved_and_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "memes.json"
            repository = MemeRepository(path)
            template = MemeTemplate.create("Тест", "Учёба", "Сверху", "Снизу")
            repository.add(template)

            loaded = MemeRepository(path).all()

        self.assertEqual(loaded[-1], template)

    def test_image_path_is_saved_and_preview_loads_image(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            image_path = Path(directory) / "sample.png"
            image = QImage(80, 60, QImage.Format.Format_RGB32)
            image.fill(QColor("orange"))
            self.assertTrue(image.save(str(image_path)))

            window = MemeMainWindow(MemeRepository(Path(directory) / "memes.json"))
            window.title_input.setText("Картинка")
            window.category_input.setText("Тест")
            window.top_input.setText("Сверху")
            window.bottom_input.setText("Снизу")
            window.image_path = str(image_path)
            window._add_template()

            loaded_template = MemeRepository(Path(directory) / "memes.json").all()[-1]
            preview = window.preview
            self.assertFalse(preview.image.isNull())
            rendered = QImage(preview.size(), QImage.Format.Format_ARGB32)
            painter = QPainter(rendered)
            preview.render(painter)
            painter.end()
            window.close()

        self.assertEqual(loaded_template.image_path, str(image_path))
        self.assertEqual(rendered.pixelColor(rendered.width() // 2, rendered.height() // 2), QColor("orange"))

    def test_generation_updates_activity_chart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            window = MemeMainWindow(MemeRepository(Path(directory) / "memes.json"))
            window.generate_button.click()

            self.assertEqual(window.chart.counts[-1], 1)
            self.assertIn("Создан мем", window.activity_log.toPlainText())
            window.close()


if __name__ == "__main__":
    unittest.main()