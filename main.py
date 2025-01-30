import os
import sys

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QStackedWidget, QTextEdit, \
    QFileDialog, QMessageBox, QGridLayout, QHBoxLayout, QLabel

from pdfplumber import open as pdf_open

from PyQt5.QtCore import Qt
import difflib


def find_similar_substrings(main_string, substring):
    substring_length = len(substring)
    threshold = 0.7 * substring_length
    ind = []
    temp_idx = -1
    while temp_idx < len(main_string) - substring_length + 1:
        temp_idx += 5
        current_substring = main_string[temp_idx:temp_idx + substring_length]
        similarity = difflib.SequenceMatcher(None, current_substring, substring).ratio()

        if similarity * substring_length >= threshold:
            ind.append(temp_idx)
            temp_idx += 50
    return ind


class HtmlLoading:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.html_content = ""

    def setPdf_path(self, pdf_path):
        self.pdf_path = pdf_path

    def pdf_to_html(self):
        images_dir = 'images'
        os.makedirs(images_dir, exist_ok=True)
        html_content = '<html><head><meta name="qrichtext" content="1" /><style type="text/css">p, li { white-space: pre-wrap; }</style></head><body>'
        with pdf_open(self.pdf_path) as pdf:
            for page_number in range(len(pdf.pages)):
                page = pdf.pages[page_number]
                text = page.extract_text()
                html_content += f'<p>{text}</p>'
                images = page.images
                for img_index, img in enumerate(images):
                    x0, top, x1, bottom = img['x0'], img['top'], img['x1'], img['bottom']
                    image = page.within_bbox((x0, top, x1, bottom)).to_image()
                    image_filename = os.path.join(images_dir, f'page_{page_number + 1}_img_{img_index + 1}.png')
                    image.save(image_filename)
                    html_content += f'<img src="{image_filename}" alt="Image" />'
        html_content += '</body></html>'
        self.html_content = html_content.replace("\n", "<br>")
        with open('output.html', 'w', encoding='utf-8') as file:
            file.write(self.html_content)
        return self.html_content

    def loading(self):
        try:
            with open('output.html', 'r', encoding='utf-8') as file:
                content = file.read()

            return content
        except FileNotFoundError:
            return "not file"


class Calculator(QWidget):
    def __init__(self, switch_to_pdf_callback):
        super().__init__()

        self.switch_to_pdf_callback = switch_to_pdf_callback

        self.layout = QVBoxLayout()

        self.result_display = QLineEdit()
        self.result_display.setStyleSheet("font-size: 24px; padding: 20px;")
        self.result_display.setAlignment(Qt.AlignRight)
        self.layout.addWidget(self.result_display)

        button_layout = QGridLayout()

        buttons = [
            ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
            ('0', 3, 1), ('+', 3, 2), ('-', 3, 0),
            ('*', 4, 0), ('/', 4, 1), ('=', 4, 2),
            ('del', 5, 0), ("C", 5, 1)
        ]

        for (text, row, col) in buttons:
            button = QPushButton(text)
            button.setStyleSheet("font-size: 24px; padding: 20px;")  # Увеличиваем размер шрифта и добавляем отступы
            button.clicked.connect(self.on_button_click)
            button_layout.addWidget(button, row, col)
        self.layout.addLayout(button_layout)
        button_pdf = QPushButton("Перейти к PDF")
        button_pdf.setStyleSheet("font-size: 4px; padding: 2px;")  # Увеличиваем размер шрифта и добавляем отступы
        button_pdf.clicked.connect(self.switch_to_pdf)
        self.layout.addWidget(button_pdf)
        self.setLayout(self.layout)
        self.current_expression = ""
        self.last_operator = ""

    def on_button_click(self):
        sender = self.sender()
        button_text = sender.text()
        if button_text == 'del':
            self.current_expression = self.current_expression[:-1]
            self.result_display.setText(self.current_expression)
        elif button_text == "C":
            self.current_expression = ""
            self.result_display.setText(self.current_expression)

        elif button_text in {'+', '-', '*', '/'}:
            if self.current_expression:
                self.current_expression += f" {button_text} "
                self.result_display.setText(self.current_expression)
        elif button_text == '=':
            try:
                result = eval(self.current_expression)
                self.result_display.setText(str(result))
                self.current_expression = str(result)  # Сохраняем результат для дальнейших операций
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", "Неверное выражение")
                self.current_expression = ""
                self.result_display.clear()
        else:
            self.current_expression += button_text
            self.result_display.setText(self.current_expression)

    def switch_to_pdf(self):
        self.switch_to_pdf_callback()


class PdfViewer(QWidget):
    def __init__(self, switch_to_calculator_callback):
        super().__init__()

        self.search_list_answer = []
        self.search_list_index = 0

        self.switch_to_calculator_callback = switch_to_calculator_callback
        self.layout = QVBoxLayout()
        search_layout = QHBoxLayout()

        self.search_line_edit = QLineEdit(self)
        self.search_line_edit.setPlaceholderText("Введите текст для поиска...")
        self.search_line_edit.setStyleSheet("font-size: 18px;")  # Увеличиваем размер шрифта

        self.search_button = QPushButton("Поиск", self)
        self.search_button.setStyleSheet(
            "font-size: 18px; padding: 10px;")  # Увеличиваем размер шрифта и добавляем отступы
        self.search_button.clicked.connect(self.perform_search)

        self.load_button = QPushButton("Загрузить файл", self)
        self.load_button.setStyleSheet(
            "font-size: 18px; padding: 10px;")  # Увеличиваем размер шрифта и добавляем отступы
        self.load_button.clicked.connect(self.open_file)

        search_layout.addWidget(self.search_line_edit)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.load_button)  # Добавляем кнопку загрузки файла

        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("font-size: 18px;")  # Увеличиваем размер шрифта в текстовом редакторе

        right_left_layout = QHBoxLayout()
        self.right_button = QPushButton(">")
        self.left_button = QPushButton("<")
        self.right_button.clicked.connect(self.right_index)
        self.left_button.clicked.connect(self.left_index)

        right_left_layout.addWidget(self.left_button)
        right_left_layout.addWidget(self.right_button)

        self.label_number = QLabel(self)
        self.label_number.setStyleSheet("font-size: 18px;")
        self.label_number.setText("0 / 0")

        self.button_back = QPushButton("Вернуться к калькулятору", self)
        self.button_back.setStyleSheet(
            "font-size: 24px; padding: 20px;")  # Увеличиваем размер шрифта и добавляем отступы
        self.button_back.clicked.connect(self.switch_to_calculator)

        self.layout.addLayout(search_layout)
        self.layout.addWidget(self.text_edit)
        self.layout.addWidget(self.label_number)
        self.layout.addLayout(right_left_layout)
        self.layout.addWidget(self.button_back)
        self.setLayout(self.layout)

        self.ht = HtmlLoading("output.html")
        self.ht.html_content = self.ht.loading()
        self.text_edit.setHtml(self.ht.html_content)

    def visible(self):
        if self.search_list_answer:
            idx = self.search_list_answer[self.search_list_index]
            text = self.ht.html_content[max(0, idx - 140):idx + 550]
            self.text_edit.setHtml(text[text.find("{{") + 2:text.rfind("}}") - 1])

    def right_index(self):
        if len(self.search_list_answer) > 1:
            self.search_list_index = (self.search_list_index + 1) % len(self.search_list_answer)
            self.label_number.setText(f"{self.search_list_index + 1} / {len(self.search_list_answer)}")
            self.visible()

    def left_index(self):
        if len(self.search_list_answer) > 1:
            self.search_list_index = (self.search_list_index - 1) % len(self.search_list_answer)
            self.label_number.setText(f"{self.search_list_index + 1} / {len(self.search_list_answer)}")
            self.visible()

    def perform_search(self):
        search_text = self.search_line_edit.text()
        if search_text:
            indices = find_similar_substrings(self.ht.html_content.lower(), search_text.lower())
            if not indices:
                self.text_edit.setHtml(":( ")
                return
            self.search_list_answer = indices
            self.search_list_index = 0
            self.label_number.setText(f"{self.search_list_index + 1} / {len(self.search_list_answer)}")
            self.visible()
            return
        self.text_edit.setHtml(":( ")

    def open_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Выберите PDF файл", "", "PDF Files (*.pdf);;All Files (*)",
                                                   options=options)
        if file_name:
            try:
                self.load_pdf(file_name)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл: {e}")

    def load_pdf(self, file_path):
        h_t = HtmlLoading(file_path)
        self.HTML = h_t.pdf_to_html()
        self.text_edit.setHtml(self.HTML)

    def switch_to_calculator(self):
        self.switch_to_calculator_callback()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.stacked_widget = QStackedWidget()

        self.calculator_widget = Calculator(self.switch_to_pdf_viewer)
        self.pdf_viewer_widget = PdfViewer(self.switch_to_calculator)  # Передаем функцию переключения

        self.stacked_widget.addWidget(self.calculator_widget)
        self.stacked_widget.addWidget(self.pdf_viewer_widget)

        layout = QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

    def switch_to_pdf_viewer(self):
        self.stacked_widget.setCurrentWidget(self.pdf_viewer_widget)

    def switch_to_calculator(self):
        self.stacked_widget.setCurrentWidget(self.calculator_widget)  # Переключаемся на калькулятор


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setWindowTitle("Калькулятор и PDF Viewer")
    window.resize(450, 650)
    window.show()
    sys.exit(app.exec_())
