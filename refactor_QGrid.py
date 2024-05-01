import os
import vtk
import itk
import SimpleITK as sitk
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QGridLayout
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from Rendering import *

OUTPUT_Dir = "output"
input_image_file = "volume Rendering/CT_Masks.nrrd"

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
        self.ui.upload_ct_button.clicked.connect(self.open_ct_file)
        self.ui.export_stl.clicked.connect(self.export_stl_segment) # only export stl file
        self.ui.view_segment.clicked.connect(self.view_stl_segment) # TODO: make it only view segment from polydata 
        self.ui.segments_comboBox.currentIndexChanged.connect(self.segment_selection_changed)

    def open_ct_file(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self.find_main_window(), "Open CT File", "", "NRRD Files (*.nrrd)", options=options)
        print(filename)
        if filename:
            self.volume_renderer.set_filename(filename)
            self.volume_renderer.render_data(data_type="volume")

    def export_stl_segment(self):
        index = self.ui.segments_comboBox.currentIndex() 
        segment_labels = {0: 2.0, 1: 1.0, 2: 7.0, 3: 3.0}
        label_value = segment_labels.get(index, 1.0) 
        stl_output_file = os.path.join(OUTPUT_Dir, f"output_mesh_{label_value}.stl")
        output_segment_file = os.path.join(OUTPUT_Dir, f"segment_{label_value}.nrrd")
        vtp_output_file = os.path.join(OUTPUT_Dir, f"polydata_mesh_{label_value}.vtp")
        _ = self.generate_mask_polydata(output_segment_file, vtp_output_file, label_value)
        self.write_stl(stl_output_file, vtp_output_file)
        self.ui.vector_size.setText(f"Exported path: {stl_output_file} ")   
     
    def view_stl_segment(self):
        index = self.ui.segments_comboBox.currentIndex() 
        segment_labels = {0: 2.0, 1: 1.0, 2: 7.0, 3: 3.0}
        label_value = segment_labels.get(index, 1.0)  
        output_segment_file = os.path.join(OUTPUT_Dir, f"segment_{label_value}.nrrd")
        vtp_output_file = os.path.join(OUTPUT_Dir, f"polydata_mesh_{label_value}.vtp")
        poly_data = self.generate_mask_polydata(output_segment_file, vtp_output_file, label_value)
        self.volume_renderer.set_poly_data(poly_data)
        self.volume_renderer.render_data(data_type="polydata")
        
    def compute_physical_size(self, extracted_region):
        physical_size = sitk.GetArrayFromImage(extracted_region).sum() * extracted_region.GetSpacing()[0] * extracted_region.GetSpacing()[1] * extracted_region.GetSpacing()[2]
        return physical_size
    
    def generate_mask_polydata(self, output_segment_file, vtp_output_file, label_value=1.0):
        poly_data = self.vtk2polydata(output_segment_file, label_value, vtp_output_file)
        extracted_region = self.read_nrrd_file(output_segment_file) 
        physical_size = self.compute_physical_size(extracted_region)
        self.ui.vector_size.setText(f"{self.ui.segments_comboBox.currentText()} Surface Volume: {physical_size:.5f} (mm3)")
        return poly_data
         
    def write_stl(self, stl_output_file, vtp_output_file):
        if not os.path.exists(stl_output_file):
            reader = self.read_polydata_file(vtp_output_file)
            stl_writer = vtk.vtkSTLWriter()
            stl_writer.SetFileName(stl_output_file)
            stl_writer.SetFileTypeToBinary()  # Set STL writer to binary mode (small file size)
            stl_writer.SetInputData(reader)
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
            # Write Compressed NRRD file form  70MB to 1.5MB
            writer = sitk.ImageFileWriter()
            writer.SetFileName(output_segment_file)
            writer.UseCompressionOn()
            writer.Execute(extracted_region)
            return extracted_region
        else:
            return self.read_nrrd_file(output_segment_file)

    def vtk2polydata(self, output_segment_file, label_value, vtp_output_file):
        if not os.path.exists(vtp_output_file):
            if not os.path.exists(output_segment_file):
                image = self.read_nrrd_file(input_image_file)
                _ = self.extract_segment(output_segment_file, image, label_value)
            itk_image = itk.imread(output_segment_file)
            vtk_image = itk.vtk_image_from_image(itk_image)
            marching_cubes = vtk.vtkMarchingCubes()
            marching_cubes.SetInputData(vtk_image)
            marching_cubes.SetValue(0, 1.0)
            marching_cubes.Update()
            poly_data = vtk.vtkPolyData()
            poly_data.ShallowCopy(marching_cubes.GetOutput())
            writer = vtk.vtkXMLPolyDataWriter()
            writer.SetFileName(vtp_output_file)
            writer.SetInputData(poly_data)
            writer.Write()
            return poly_data
        else:
            return self.read_polydata_file(vtp_output_file)
        
    def read_polydata_file(self, vtp_output_file):
        reader = vtk.vtkXMLPolyDataReader()
        reader.SetFileName(vtp_output_file)
        reader.Update()
        poly_data = vtk.vtkPolyData()
        poly_data.ShallowCopy(reader.GetOutput())
        return poly_data    

    def segment_selection_changed(self, index):
        segment_labels = {0: 2.0, 1: 1.0, 2: 7.0, 3: 3.0}
        label_value = segment_labels.get(index, 1.0)
        segment = str(self.ui.segments_comboBox.currentText())     
        self.ui.vector_size.setText(f"{segment} with label {label_value} is ready for [View | Export] actions")


class DemoApp(QMainWindow):
    def __init__(self):
        super(DemoApp, self).__init__()
        self.ui = None
        self.setup()

    def setup(self):
        # TODO: Import the generated UI file using the pyuic5 command| self pointer 
        import demo_ui
        self.ui = demo_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        # uic.loadUi("demo.ui", self)  #The error AttributeError: 'NoneType' object has no attribute 'vtk_panel_layout'
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
