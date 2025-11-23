from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QStackedWidget, QPushButton

class TestScreen(QWidget):
    def __init__(self, stack_widget: QStackedWidget):
        super().__init__()
        self.stack_widget = stack_widget
        self.setWindowTitle("Тестовый экран")

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Тестовый экран"))
        back_button = QPushButton("Назад")
        back_button.clicked.connect(self.go_back)
        layout.addWidget(back_button)
        self.setLayout(layout)

    def go_back(self):
        self.stack_widget.setCurrentIndex(0) 
