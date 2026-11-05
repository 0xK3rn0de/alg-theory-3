import tempfile
import unittest
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from meme_app import MemeMainWindow, MemeRepository, MemeTemplate, ValidationError


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

    def test_generation_updates_activity_chart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            window = MemeMainWindow(MemeRepository(Path(directory) / "memes.json"))
            window.generate_button.click()

            self.assertEqual(window.chart.counts[-1], 1)
            self.assertIn("Создан мем", window.activity_log.toPlainText())
            window.close()


if __name__ == "__main__":
    unittest.main()