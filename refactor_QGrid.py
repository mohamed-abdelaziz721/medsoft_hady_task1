from time import sleep
import os
import vtk
import itk
import SimpleITK as sitk
from PyQt5 import QtWidgets, uic
import gc
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QHBoxLayout, QGridLayout
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from Rendering import *

OUTPUT_Dir = "output"


class AppLogic:
    def __init__(self, ui, vtk_widgets):
        self.ui = ui
        # self.vtk_widgets = vtk_widgets
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
        self.ui.export_stl.clicked.connect(self.export_stl)
        self.ui.segments_comboBox.currentIndexChanged.connect(self.segment_selection_changed)
        self.ui.export_stl.clicked.connect(self.open_stl_segment)
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
            # self.volume_renderer.clear_all_actors()
            self.volume_renderer.render_data(data_type="volume")


    def read_nrrd_file(self, filename):
        reader = sitk.ImageFileReader()
        reader.SetImageIO("NrrdImageIO")
        reader.SetFileName(filename)
        image = reader.Execute()
        return image

    def extract_segment(self, output_segment_file, image, label_value):
        if not os.path.exists(output_segment_file):
            print(f"Segment is being extracted: {output_segment_file}")
            extracted_region = sitk.BinaryThreshold(image, lowerThreshold=label_value, upperThreshold=label_value)
            sitk.WriteImage(extracted_region, output_segment_file)
            return extracted_region
        else:
            print(f"Segment file already exists: {output_segment_file}")
            return self.read_nrrd_file(output_segment_file)

    def vtk2polydata(self, vtk_image, vtp_output_file):
        # Convert VTK image to PolyData
        marching_cubes = vtk.vtkMarchingCubes()
        marching_cubes.SetInputData(vtk_image)
        marching_cubes.SetValue(0, 1.0)
        marching_cubes.Update()
        poly_data = vtk.vtkPolyData()
        poly_data.ShallowCopy(marching_cubes.GetOutput())

        # Write VTP file if it doesn't exist
        if not os.path.exists(vtp_output_file):
            writer = vtk.vtkXMLPolyDataWriter()
            writer.SetFileName(vtp_output_file)
            writer.SetInputData(poly_data)
            writer.Write()
            print(f"VTP file written: {vtp_output_file}")
        else:
            print(f"VTP file already exists: {vtp_output_file}")

        return poly_data

    def export_stl(self, stl_output_file, vtp_output_file):
        # Read VTP file and convert to STL
        if os.path.exists(vtp_output_file):
            poly_data = vtk.vtkPolyData()
            reader = vtk.vtkXMLPolyDataReader()
            reader.SetFileName(vtp_output_file)
            reader.Update()
            poly_data.ShallowCopy(reader.GetOutput())

            # Write STL file if it doesn't exist
            if not os.path.exists(stl_output_file):
                stl_writer = vtk.vtkSTLWriter()
                stl_writer.SetFileName(stl_output_file)
                stl_writer.SetInputData(poly_data)
                stl_writer.Write()
                print(f"STL file written: {stl_output_file}")
            else:
                print(f"STL file already exists: {stl_output_file}")
        else:
            print(f"VTP file does not exist: {vtp_output_file}")


    def open_stl_segment(self):

        # self.volume_renderer.clear_all_actors()
        
        index = self.ui.segments_comboBox.currentIndex() 
        segment_labels = {0: 2.0, 1: 1.0, 2: 7.0, 3: 3.0}
        label_value = segment_labels.get(index, 1.0)  # Default to 1.0 if index is not found

        print("index from stl segment",index)
        print(f"Selected label: {label_value}")
        
        # if not exists, calculate the segment and export the stl file
        if not os.path.exists(os.path.join(OUTPUT_Dir, f"output_mesh_{label_value}.stl")):
            input_image_file = "volume Rendering/CT_Masks.nrrd"
            output_segment_file = os.path.join(OUTPUT_Dir, f"segment_{label_value}.nrrd")
            stl_output_file = os.path.join(OUTPUT_Dir, f"output_mesh_{label_value}.stl")
            vtp_output_file = os.path.join(OUTPUT_Dir, f"polydata_mesh_{label_value}.vtp")
            self.generate_outputs(input_image_file, output_segment_file, stl_output_file, vtp_output_file, label_value)
            self.volume_renderer.set_stlfilename(stl_output_file)
            self.volume_renderer.render_data(data_type="stl")
        else:
            stl_output_file = os.path.join(OUTPUT_Dir, f"output_mesh_{label_value}.stl")
            print(f".....{stl_output_file}.....")
            self.volume_renderer.set_stlfilename(stl_output_file)
            self.volume_renderer.render_data(data_type="stl")
                

    def generate_outputs(self, input_image_file, output_segment_file, stl_output_file, vtp_output_file, label_value=1.0):
        # Read input image
        image = self.read_nrrd_file(input_image_file)

        # Extract segment if it doesn't exist
        extracted_region = self.extract_segment(output_segment_file, image, label_value)

        # Compute the physical size of the binary mask
        physical_size = sitk.GetArrayFromImage(extracted_region).sum() * image.GetSpacing()[0] * image.GetSpacing()[1] * image.GetSpacing()[2]
        #
        self.ui.vector_size.setText(f"{physical_size:.5f} (mm3)")
    
        # Convert SimpleITK image to VTK image
        itk_image = itk.imread(output_segment_file)
        vtk_image = itk.vtk_image_from_image(itk_image)

        # Convert VTK image to PolyData
        self.vtk2polydata(vtk_image, vtp_output_file)
        
        # connect to the relevant button only if the segment is selected
        # Export STL if VTP file exists
        self.export_stl(stl_output_file, vtp_output_file)



    def segment_selection_changed(self, index):
        # mapping of data from CT.nnrd "Not Generic"
        segment_labels = {0: 2.0, 1: 1.0, 2: 7.0, 3: 3.0}
        label_value = segment_labels.get(index, 1.0)  # Default to 1.0 if index is not found

        print(f"Selected index: {index}")
        print(f"Selected segment name: {self.ui.segments_comboBox.itemText(index)}")
        
        # not generic .. may be mapped to a function that exract segment from CT.nrrd
        input_image_file = "volume Rendering/CT_Masks.nrrd"
        # set the path to the output directory
        # TODO: make it run on another thread to avoid blocking the UI
        output_segment_file = os.path.join(OUTPUT_Dir, f"segment_{label_value}.nrrd")
        stl_output_file = os.path.join(OUTPUT_Dir, f"output_mesh_{label_value}.stl")
        vtp_output_file = os.path.join(OUTPUT_Dir, f"polydata_mesh_{label_value}.vtp")

        # TODO remove all logic from here as all depend on each other
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

        # Create AppLogic instance passing vtk_widgets
        self.logic = AppLogic(self.ui, self.vtk_widgets)
    
    
    # def initialize(self):
    #     # Initialize and start the VTK widgets
    #     for vtk_widget in self.vtk_widgets:
    #         vtk_widget.Initialize()
    #         vtk_widget.Start()



if __name__ == "__main__":
    import sys
    os.chdir(os.path.dirname(__file__))
    app = QApplication([])
    main_window = DemoApp()
    main_window.setWindowTitle("CT-Task")
    main_window.show()
    # main_window.initialize()
    sys.exit(app.exec_())
