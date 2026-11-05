import sys

from PyQt6.QtWidgets import QApplication, QMessageBox

from meme_app import DataStorageError, MemeMainWindow, MemeRepository


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Генератор мемов")

    try:
        window = MemeMainWindow(MemeRepository())
    except DataStorageError as error:
        QMessageBox.critical(None, "Ошибка данных", str(error))
        return 1

    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())