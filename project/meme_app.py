from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QFont, QFontMetrics, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


LOGGER = logging.getLogger("meme_generator")


class MemeAppError(Exception):
    """Base exception for errors that can be shown to the user."""


class ValidationError(MemeAppError):
    """Raised when a template does not contain valid data."""


class SelectionError(MemeAppError):
    """Raised when an operation needs a selected template."""


class DataStorageError(MemeAppError):
    """Raised when saved templates cannot be read or written."""


@dataclass
class MemeTemplate:
    title: str
    category: str
    top_text: str
    bottom_text: str
    template_id: str
    image_path: str = ""

    @classmethod
    def create(
        cls,
        title: str,
        category: str,
        top_text: str,
        bottom_text: str,
        image_path: str = "",
    ) -> MemeTemplate:
        values = {
            "Название": title.strip(),
            "Категория": category.strip(),
        }
        for field_name, value in values.items():
            if not value:
                raise ValidationError(f"Заполните поле «{field_name.lower()}».")
        if not top_text.strip() and not bottom_text.strip():
            raise ValidationError("Добавьте хотя бы одну подпись для мема.")
        if len(values["Название"]) > 50 or len(values["Категория"]) > 30:
            raise ValidationError("Название должно быть короче 50, а категория — 30 символов.")
        if len(top_text) > 120 or len(bottom_text) > 120:
            raise ValidationError("Длина каждой подписи не должна превышать 120 символов.")
        return cls(
            title=values["Название"],
            category=values["Категория"],
            top_text=top_text.strip(),
            bottom_text=bottom_text.strip(),
            template_id=uuid4().hex[:8],
            image_path=image_path,
        )


class MemeRepository:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path(__file__).with_name("memes.json")
        self._templates = self._load()

    def all(self) -> list[MemeTemplate]:
        return list(self._templates)

    def add(self, template: MemeTemplate) -> None:
        self._templates.append(template)
        self._save()

    def _load(self) -> list[MemeTemplate]:
        if not self.path.exists():
            return [
                MemeTemplate("Понедельник", "Работа", "Я: сегодня лягу пораньше", "Также я в 02:47: ещё одно видео" , "sample-01"),
                MemeTemplate("Перед дедлайном", "Учёба", "До срока ещё целая неделя", "Осталось 3 минуты", "sample-02"),
                MemeTemplate("Ожидание и реальность", "Жизнь", "План на выходные", "Фактический план на выходные", "sample-03"),
            ]
        try:
            raw_templates = json.loads(self.path.read_text(encoding="utf-8"))
            return [MemeTemplate(**item) for item in raw_templates]
        except (OSError, json.JSONDecodeError, TypeError, KeyError) as error:
            raise DataStorageError(f"Не удалось прочитать файл шаблонов: {error}") from error

    def _save(self) -> None:
        try:
            self.path.write_text(
                json.dumps([asdict(item) for item in self._templates], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as error:
            self._templates.pop()
            raise DataStorageError(f"Не удалось сохранить шаблон: {error}") from error


class MemePreview(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.top_text = "Выберите шаблон"
        self.bottom_text = "и создайте мем"
        self.image = QPixmap()
        self.setMinimumSize(360, 250)

    def set_caption(self, top_text: str, bottom_text: str, image_path: str = "") -> None:
        self.top_text = top_text or " "
        self.bottom_text = bottom_text or " "
        self.image = QPixmap(image_path) if image_path else QPixmap()
        self.update()

    def paintEvent(self, event) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bounds = self.rect().adjusted(2, 2, -2, -2)
        gradient = QLinearGradient(QPointF(bounds.topLeft()), QPointF(bounds.bottomRight()))
        gradient.setColorAt(0, Qt.GlobalColor.yellow)
        gradient.setColorAt(1, Qt.GlobalColor.darkYellow)
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(bounds, 14, 14)
        if not self.image.isNull():
            clip_path = QPainterPath()
            clip_path.addRoundedRect(QRectF(bounds), 14, 14)
            painter.save()
            painter.setClipPath(clip_path)
            scaled_image = self.image.scaled(
                bounds.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            image_x = bounds.center().x() - scaled_image.width() // 2
            image_y = bounds.center().y() - scaled_image.height() // 2
            painter.drawPixmap(image_x, image_y, scaled_image)
            painter.restore()

        font = QFont("DejaVu Sans", 18, QFont.Weight.Black)
        metrics = QFontMetrics(font)
        painter.setFont(font)
        text_bounds = bounds.adjusted(20, 32, -20, -32)
        self._draw_outlined_text(painter, metrics, self.top_text.upper(), text_bounds, True)
        self._draw_outlined_text(painter, metrics, self.bottom_text.upper(), text_bounds, False)

        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.setFont(QFont("DejaVu Sans", 8, QFont.Weight.Bold))
        painter.drawText(bounds.adjusted(0, 10, -14, 0), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop, "MEME / STUDIO")

    @staticmethod
    def _draw_outlined_text(
        painter: QPainter,
        metrics: QFontMetrics,
        text: str,
        area,
        at_top: bool,
    ) -> None:
        words = text.split()
        lines: list[str] = []
        current_line = ""
        for word in words:
            candidate = f"{current_line} {word}".strip()
            if current_line and metrics.horizontalAdvance(candidate) > area.width():
                lines.append(current_line)
                current_line = word
            else:
                current_line = candidate
        if current_line:
            lines.append(current_line)

        line_height = metrics.height()
        visible_lines = lines[:3]
        start_y = area.top() + metrics.ascent() if at_top else area.bottom() - line_height * (len(visible_lines) - 1)
        for index, line in enumerate(visible_lines):
            y = start_y + index * line_height
            path = QPainterPath()
            x = area.center().x() - metrics.horizontalAdvance(line) / 2
            path.addText(x, y, painter.font(), line)
            painter.setPen(QPen(Qt.GlobalColor.black, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            painter.setBrush(Qt.GlobalColor.white)
            painter.drawPath(path)


class ActivityChart(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.counts = [0] * 7
        self.setMinimumHeight(145)

    def set_counts(self, counts: list[int]) -> None:
        self.counts = counts[-7:]
        self.update()

    def paintEvent(self, event) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(Qt.GlobalColor.lightGray, 1))
        baseline = self.height() - 28
        painter.drawLine(8, baseline, self.width() - 8, baseline)
        max_count = max(self.counts, default=0)
        slot = max(1, (self.width() - 24) // 7)
        bar_width = max(8, int(slot * 0.52))
        today = date.today()
        for index, count in enumerate(self.counts):
            x = 12 + index * slot + (slot - bar_width) // 2
            bar_height = int((baseline - 35) * count / max_count) if max_count else 2
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(Qt.GlobalColor.darkGreen)
            painter.drawRoundedRect(x, baseline - bar_height, bar_width, bar_height, 4, 4)
            painter.setPen(Qt.GlobalColor.darkGray)
            painter.setFont(QFont("DejaVu Sans", 8))
            day_label = (today - timedelta(days=6 - index)).strftime("%d.%m")
            painter.drawText(x - 6, baseline + 16, slot + 8, 14, Qt.AlignmentFlag.AlignHCenter, day_label)
            if count:
                painter.drawText(x - 6, baseline - bar_height - 18, slot + 8, 16, Qt.AlignmentFlag.AlignHCenter, str(count))


class MemeMainWindow(QMainWindow):
    def __init__(self, repository: MemeRepository) -> None:
        super().__init__()
        self.repository = repository
        self.daily_counts: dict[date, int] = {}
        self.setWindowTitle("Генератор мемов")
        self.resize(1120, 820)
        self._build_ui()
        self._populate_table()
        self._update_chart()
        self._log("Приложение запущено")

    def _build_ui(self) -> None:
        self.setStyleSheet(
            "QMainWindow { background: #f3f4ef; }"
            "QWidget { color: #111; }"
            "QLabel { color: #111; }"
            "QGroupBox { color: #111; font-weight: 700; border: 1px solid #d5d9ce; border-radius: 6px; margin-top: 10px; padding: 10px; }"
            "QGroupBox::title { color: #111; subcontrol-origin: margin; left: 10px; padding: 0 4px; }"
            "QLineEdit, QTableWidget, QTextEdit { color: #111; background: #fff; border: 1px solid #d5d9ce; border-radius: 4px; padding: 5px; }"
            "QTableWidget::item { color: #111; }"
            "QPushButton { background: #273027; color: white; border: 0; border-radius: 4px; padding: 8px 13px; font-weight: 700; }"
            "QPushButton:hover { background: #3d4b3b; }"
            "QHeaderView::section { color: #111; background: #e7e9e1; border: 0; padding: 6px; font-weight: 700; }"
        )

        file_menu = self.menuBar().addMenu("Файл")
        add_action = file_menu.addAction("Добавить шаблон")
        add_action.triggered.connect(self._add_template)
        generate_action = file_menu.addAction("Создать мем")
        generate_action.setShortcut("Ctrl+Return")
        generate_action.triggered.connect(self._generate_meme)
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Выход")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        help_menu = self.menuBar().addMenu("Справка")
        about_action = help_menu.addAction("О программе")
        about_action.triggered.connect(self._show_about)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)

        heading = QLabel("ГЕНЕРАТОР МЕМОВ")
        heading.setStyleSheet("font-size: 22px; font-weight: 900; color: #111;")
        subtitle = QLabel("Выберите заготовку, добавьте свои идеи и создайте мем")
        subtitle.setStyleSheet("color: #111;")
        layout.addWidget(heading)
        layout.addWidget(subtitle)

        content = QSplitter(Qt.Orientation.Horizontal)
        template_panel = QWidget()
        template_layout = QVBoxLayout(template_panel)
        template_layout.setContentsMargins(0, 0, 8, 0)
        template_layout.addWidget(QLabel("Заготовки"))
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Название", "Категория"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._show_selected_preview)
        template_layout.addWidget(self.table)

        preview_panel = QWidget()
        preview_layout = QVBoxLayout(preview_panel)
        preview_layout.setContentsMargins(8, 0, 0, 0)
        preview_layout.addWidget(QLabel("Предпросмотр"))
        self.preview = MemePreview()
        preview_layout.addWidget(self.preview, 1)
        self.generate_button = QPushButton("Создать мем")
        self.generate_button.clicked.connect(self._generate_meme)
        preview_layout.addWidget(self.generate_button)
        content.addWidget(template_panel)
        content.addWidget(preview_panel)
        content.setStretchFactor(0, 4)
        content.setStretchFactor(1, 5)
        layout.addWidget(content, 3)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Например, Понедельник")
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("Например, Работа")
        self.top_input = QLineEdit()
        self.top_input.setPlaceholderText("Верхняя подпись")
        self.bottom_input = QLineEdit()
        self.bottom_input.setPlaceholderText("Нижняя подпись")
        self.image_path = ""
        self.image_button = QPushButton("Выбрать…")
        self.image_button.clicked.connect(self._select_image)
        self.clear_image_button = QPushButton("Убрать")
        self.clear_image_button.clicked.connect(self._clear_image)
        self.image_label = QLabel("Не выбрано")
        image_controls = QHBoxLayout()
        image_controls.addWidget(self.image_button)
        image_controls.addWidget(self.clear_image_button)
        image_controls.addWidget(self.image_label, 1)
        image_row = QWidget()
        image_row.setLayout(image_controls)
        form = QFormLayout()
        form.addRow("Название", self.title_input)
        form.addRow("Категория", self.category_input)
        form.addRow("Сверху", self.top_input)
        form.addRow("Снизу", self.bottom_input)
        form.addRow("Изображение", image_row)
        self.add_button = QPushButton("Добавить заготовку")
        self.add_button.clicked.connect(self._add_template)
        form.addRow("", self.add_button)
        form_group = QGroupBox("Новая заготовка")
        form_group.setLayout(form)
        layout.addWidget(form_group)

        lower = QHBoxLayout()
        chart_group = QGroupBox("Активность за 7 дней")
        chart_layout = QVBoxLayout(chart_group)
        self.chart = ActivityChart()
        chart_layout.addWidget(self.chart)
        log_group = QGroupBox("Журнал действий")
        log_layout = QVBoxLayout(log_group)
        self.activity_log = QTextEdit()
        self.activity_log.setReadOnly(True)
        self.activity_log.setMaximumHeight(155)
        log_layout.addWidget(self.activity_log)
        lower.addWidget(chart_group, 1)
        lower.addWidget(log_group, 1)
        layout.addLayout(lower, 1)
        self.setCentralWidget(root)
        self.statusBar().showMessage("Готово")

    def _populate_table(self) -> None:
        templates = self.repository.all()
        self.table.setRowCount(len(templates))
        for row, template in enumerate(templates):
            self.table.setItem(row, 0, QTableWidgetItem(template.title))
            self.table.setItem(row, 1, QTableWidgetItem(template.category))
        if templates:
            self.table.selectRow(0)

    def _selected_template(self) -> MemeTemplate:
        row = self.table.currentRow()
        templates = self.repository.all()
        if row < 0 or row >= len(templates):
            raise SelectionError("Сначала выберите заготовку в таблице.")
        return templates[row]

    def _show_selected_preview(self) -> None:
        try:
            template = self._selected_template()
        except SelectionError:
            return
        self.preview.set_caption(template.top_text, template.bottom_text, template.image_path)

    def _select_image(self) -> None:
        image_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите изображение",
            "",
            "Изображения (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not image_path:
            return
        if QPixmap(image_path).isNull():
            self._show_error(ValidationError("Не удалось загрузить выбранное изображение."))
            return
        self.image_path = image_path
        self.image_label.setText(Path(image_path).name)
        self.image_label.setToolTip(image_path)
        self.preview.set_caption(self.top_input.text(), self.bottom_input.text(), image_path)

    def _clear_image(self) -> None:
        self.image_path = ""
        self.image_label.setText("Не выбрано")
        self.image_label.setToolTip("")
        self.preview.set_caption(self.top_input.text(), self.bottom_input.text())

    def _add_template(self) -> None:
        try:
            template = MemeTemplate.create(
                self.title_input.text(),
                self.category_input.text(),
                self.top_input.text(),
                self.bottom_input.text(),
                self.image_path,
            )
            self.repository.add(template)
        except MemeAppError as error:
            self._show_error(error)
            return
        self._populate_table()
        self.table.selectRow(self.table.rowCount() - 1)
        for field in (self.title_input, self.category_input, self.top_input, self.bottom_input):
            field.clear()
        self.image_path = ""
        self.image_label.setText("Не выбрано")
        self.image_label.setToolTip("")
        self._log(f"Добавлена заготовка «{template.title}»")

    def _generate_meme(self) -> None:
        try:
            template = self._selected_template()
        except MemeAppError as error:
            self._show_error(error)
            return
        today = date.today()
        self.daily_counts[today] = self.daily_counts.get(today, 0) + 1
        self.preview.set_caption(template.top_text, template.bottom_text, template.image_path)
        self._update_chart()
        self._log(f"Создан мем по заготовке «{template.title}»")
        self.statusBar().showMessage("Мем готов", 3000)

    def _update_chart(self) -> None:
        today = date.today()
        self.chart.set_counts([
            self.daily_counts.get(today - timedelta(days=offset), 0)
            for offset in range(6, -1, -1)
        ])

    def _log(self, message: str) -> None:
        LOGGER.info(message)
        self.activity_log.append(f"{date.today():%d.%m.%Y}  {message}")

    def _show_error(self, error: MemeAppError) -> None:
        LOGGER.warning("Операция не выполнена: %s", error)
        QMessageBox.warning(self, "Не удалось выполнить действие", str(error))

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "О программе",
            "Генератор мемов\nВыбирайте готовые заготовки или добавляйте свои.",
        )