from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QLabel

class StoragerScreen(QWidget):
    def __init__(self, stack_widget: QStackedWidget):
        super().__init__()
        self.stack_widget = stack_widget
        self.layout = QVBoxLayout()
        self.label = QLabel("Менеджер")

        self.setLayout(self.layout)

    def on_show(self):
        self.layout.addWidget(self.label)