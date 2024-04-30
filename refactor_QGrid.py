import os
import vtk
import itk
import SimpleITK as sitk
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QGridLayout
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from Rendering import *

OUTPUT_Dir = "output"

class AppLogic:
    def __init__(self, ui, vtk_widgets):
        self.ui = ui
        self.volume_renderer = VolumeRenderer(vtk_widgets)  # Instantiate VolumeRenderer with all vtk_widgets
        self.setup_ui_connections()

    def find_main_window(self):
        parent = self.ui.upload_ct_button
        while parent:
            if isinstance(parent, QtWidgets.QMainWindow):
                return parent
            parent = parent.parent()
        # If no main window is found, return None or handle the error as needed
        return None       

    def setup_ui_connections(self):
        self.ui.upload_ct_button.clicked.connect(self.open_file_dialog)
        self.ui.export_stl.clicked.connect(self.open_stl_segment)
        self.ui.segments_comboBox.currentIndexChanged.connect(self.segment_selection_changed)
        self.ui.cyl_cube.clicked.connect(self.add_cube_in_grid)

    def add_cube_in_grid(self):
        self.volume_renderer.add_cube()
    
    def clear_window(self):
        self.volume_renderer.clear_all_actors()

    def open_file_dialog(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self.find_main_window(), "Open CT File", "", "NRRD Files (*.nrrd)", options=options)
        print(filename)
        if filename:
            self.volume_renderer.set_filename(filename)
            self.volume_renderer.render_data(data_type="volume")

    def open_stl_segment(self):
        index = self.ui.segments_comboBox.currentIndex() 
        segment_labels = {0: 2.0, 1: 1.0, 2: 7.0, 3: 3.0}
        label_value = segment_labels.get(index, 1.0)  
        stl_output_file = os.path.join(OUTPUT_Dir, f"output_mesh_{label_value}.stl")
        if not os.path.exists(stl_output_file):
            input_image_file = "volume Rendering/CT_Masks.nrrd"
            output_segment_file = os.path.join(OUTPUT_Dir, f"segment_{label_value}.nrrd")
            vtp_output_file = os.path.join(OUTPUT_Dir, f"polydata_mesh_{label_value}.vtp")
            self.generate_outputs(input_image_file, output_segment_file, stl_output_file, vtp_output_file, label_value)
        self.volume_renderer.set_stlfilename(stl_output_file)
        self.volume_renderer.render_data(data_type="stl")
        
    def compute_physical_size(self, extracted_region):
        physical_size = sitk.GetArrayFromImage(extracted_region).sum() * extracted_region.GetSpacing()[0] * extracted_region.GetSpacing()[1] * extracted_region.GetSpacing()[2]
        return physical_size
    
    def generate_outputs(self, input_image_file, output_segment_file, stl_output_file, vtp_output_file, label_value=1.0):
        image = self.read_nrrd_file(input_image_file)
        extracted_region = self.extract_segment(output_segment_file, image, label_value)
        physical_size = self.compute_physical_size(extracted_region)
        self.ui.vector_size.setText(f"{physical_size:.5f} (mm3)")
        itk_image = itk.imread(output_segment_file)
        vtk_image = itk.vtk_image_from_image(itk_image)
        self.vtk2polydata(vtk_image, vtp_output_file)
        self.write_stl(stl_output_file, vtp_output_file)

    def write_stl(self, stl_output_file, vtp_output_file):
        if not os.path.exists(stl_output_file):
            poly_data = vtk.vtkPolyData()
            reader = vtk.vtkXMLPolyDataReader()
            reader.SetFileName(vtp_output_file)
            reader.Update()
            poly_data.ShallowCopy(reader.GetOutput())
            if not os.path.exists(stl_output_file):
                stl_writer = vtk.vtkSTLWriter()
                stl_writer.SetFileName(stl_output_file)
                stl_writer.SetInputData(reader.GetOutput())
                stl_writer.Write()    

    def read_nrrd_file(self, filename):
        reader = sitk.ImageFileReader()
        reader.SetImageIO("NrrdImageIO")
        reader.SetFileName(filename)
        image = reader.Execute()
        return image

    def extract_segment(self, output_segment_file, image, label_value):
        if not os.path.exists(output_segment_file):
            extracted_region = sitk.BinaryThreshold(image, lowerThreshold=label_value, upperThreshold=label_value)
            sitk.WriteImage(extracted_region, output_segment_file)
            return extracted_region
        else:
            return self.read_nrrd_file(output_segment_file)

    def vtk2polydata(self, vtk_image, vtp_output_file):
        marching_cubes = vtk.vtkMarchingCubes()
        marching_cubes.SetInputData(vtk_image)
        marching_cubes.SetValue(0, 1.0)
        marching_cubes.Update()
        poly_data = vtk.vtkPolyData()
        poly_data.ShallowCopy(marching_cubes.GetOutput())
        if not os.path.exists(vtp_output_file):
            writer = vtk.vtkXMLPolyDataWriter()
            writer.SetFileName(vtp_output_file)
            writer.SetInputData(poly_data)
            writer.Write()

    def segment_selection_changed(self, index):
        segment_labels = {0: 2.0, 1: 1.0, 2: 7.0, 3: 3.0}
        label_value = segment_labels.get(index, 1.0)     
        input_image_file = "volume Rendering/CT_Masks.nrrd"
        output_segment_file = os.path.join(OUTPUT_Dir, f"segment_{label_value}.nrrd")
        stl_output_file = os.path.join(OUTPUT_Dir, f"output_mesh_{label_value}.stl")
        vtp_output_file = os.path.join(OUTPUT_Dir, f"polydata_mesh_{label_value}.vtp")
        self.generate_outputs(input_image_file, output_segment_file, stl_output_file, vtp_output_file, label_value)
        

class DemoApp(QMainWindow):
    def __init__(self):
        super(DemoApp, self).__init__()
        self.ui = None
        self.setup()

    def setup(self):
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
