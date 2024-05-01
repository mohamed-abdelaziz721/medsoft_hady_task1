import os
from app_logic import AppLogic
from PyQt5.QtWidgets import QMainWindow, QApplication, QGridLayout
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

class DemoApp(QMainWindow):
    def __init__(self):
        super(DemoApp, self).__init__()
        self.ui = None
        self.setup()

    def setup(self):
        # Import the generated UI file using the pyuic5 command| self pointer 
        import demo_ui
        self.ui = demo_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        # Create a grid layout
        self.ui.vtk_panel_layout = QGridLayout()
        self.ui.vtk_panel_layout.setContentsMargins(0, 0, 0, 0)
        self.ui.vtk_panel.setLayout(self.ui.vtk_panel_layout)
        # Create and add QVTKRenderWindowInteractor widgets to the grid layout
        self.vtk_widgets = []
        for i in range(2):
            for j in range(1):
                vtk_widget = QVTKRenderWindowInteractor()
                self.ui.vtk_panel_layout.addWidget(vtk_widget, i, j)
                self.vtk_widgets.append(vtk_widget)
        self.logic = AppLogic(self.ui, self.vtk_widgets)

if __name__ == "__main__":
    import sys
    os.chdir(os.path.dirname(__file__))
    app = QApplication([])
    main_window = DemoApp()
    main_window.setWindowTitle("CT-Task")
    main_window.show()
    sys.exit(app.exec_())
