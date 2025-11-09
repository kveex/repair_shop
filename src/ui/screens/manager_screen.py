from PySide6.QtWidgets import QWidget, QStackedWidget

class ManagerScreen(QWidget):
    def __init__(self, stack_widget: QStackedWidget):
        super().__init__()
        self.stack_widget = stack_widget
        self.setWindowTitle("Менеджер")