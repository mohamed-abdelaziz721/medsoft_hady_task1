import os
import vtk
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QHBoxLayout, QFrame, QGridLayout
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import SimpleITK as sitk
import itk

output_dir = "output"

class VolumeRenderer(QFrame):
    def __init__(self, parent=None):
        super(VolumeRenderer, self).__init__(parent)
        # Initialize filename attribute
        self.filename = "volume Rendering/CT.nrrd"

        # Initially set interactor to None
        self.interactor = None

        # Create a layout for the interactor
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

    def render_volume_CT(self):
        if self.filename is None:
            print("Error: No filename provided.")
            return

        if self.interactor is None:
            # Create the QVTKRenderWindowInteractor widget
            self.interactor = QVTKRenderWindowInteractor(self)

            # Add the interactor to the layout
            self.layout.addWidget(self.interactor)
            self.layout.setContentsMargins(0, 0, 0, 0)


        colors = vtk.vtkNamedColors()
        colors.SetColor('BkgColor', [51, 77, 102, 255])

        reader = vtk.vtkNrrdReader()
        reader.SetFileName(self.filename)

        colorTransferFunction = vtk.vtkColorTransferFunction()
        colorTransferFunction.AddRGBPoint(0, 0.0, 0.0, 0.0)
        colorTransferFunction.AddRGBPoint(500, 240.0 / 255.0, 184.0 / 255.0, 160.0 / 255.0)
        colorTransferFunction.AddRGBPoint(1150, 240.0 / 255.0, 184.0 / 255.0, 160.0 / 255.0)
        colorTransferFunction.AddRGBPoint(1500, 1.0, 1.0, 240.0 / 255.0)

        volumeScalarOpacity = vtk.vtkPiecewiseFunction()
        volumeScalarOpacity.AddPoint(0, 0.00)
        volumeScalarOpacity.AddPoint(500, 0.15)
        volumeScalarOpacity.AddPoint(1150, 0.15)
        volumeScalarOpacity.AddPoint(1500, 0.85)

        volumeGradientOpacity = vtk.vtkPiecewiseFunction()
        volumeGradientOpacity.AddPoint(0, 0.0)
        volumeGradientOpacity.AddPoint(90, 0.5)
        volumeGradientOpacity.AddPoint(100, 1.0)

        volumeProperty = vtk.vtkVolumeProperty()
        volumeProperty.SetColor(colorTransferFunction)
        volumeProperty.SetScalarOpacity(volumeScalarOpacity)
        volumeProperty.SetGradientOpacity(volumeGradientOpacity)
        volumeProperty.SetInterpolationTypeToLinear()
        volumeProperty.ShadeOn()
        volumeProperty.SetAmbient(0.4)
        volumeProperty.SetDiffuse(0.6)
        volumeProperty.SetSpecular(0.2)

        volumeMapper = vtk.vtkGPUVolumeRayCastMapper()
        volumeMapper.SetInputConnection(reader.GetOutputPort())

        volume = vtk.vtkVolume()
        volume.SetMapper(volumeMapper)
        volume.SetProperty(volumeProperty)

        a_renderer = vtk.vtkRenderer()
        ren_win = vtk.vtkRenderWindow()
        ren_win.AddRenderer(a_renderer)

        a_renderer.AddVolume(volume)
        a_renderer.SetBackground(colors.GetColor3d('BkgColor'))

        ren_win.SetSize(640, 480)
        ren_win.SetWindowName('NRRDReader')
        ren_win.Render()

        iren = vtk.vtkRenderWindowInteractor()
        iren.SetRenderWindow(ren_win)
        iren.Initialize()
        iren.Start()




class DemoApp(QMainWindow):
    def __init__(self):
        super(DemoApp, self).__init__()
        self.ui = None
        self.setup()

    def setup(self):
        import demo_ui
        self.ui = demo_ui.Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.vtk_layout = QHBoxLayout()
        self.ui.vtk_layout.setContentsMargins(0, 0, 0, 0)
        self.ui.vtk_panel.setLayout(self.ui.vtk_layout)

        self.vtk_widget = VolumeRenderer(self.ui.vtk_panel)
        self.ui.vtk_layout.addWidget(self.vtk_widget)

        self.ui.upload_ct_button.clicked.connect(self.open_file_dialog)

        self.ui.segments_comboBox.currentIndexChanged.connect(self.segment_selection_changed)
        self.ui.export_stl.clicked.connect(self.open_stl_segment)


        # self.vtk_widget = VolumeRenderer()
        # self.ui.threshold_slider.setValue(50)
        # self.ui.threshold_slider.valueChanged.connect(self.vtk_widget.render_volume_CT)
    

    def open_file_dialog(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, "Open CT File", "", "NRRD Files (*.nrrd)", options=options)
        if filename:
            self.vtk_widget.filename = filename
            self.vtk_widget.render_volume_CT()


    def open_stl_segment(self):
        index = self.ui.segments_comboBox.currentIndex() 
        segment_labels = {0: 1.0, 1: 2.0, 2: 7.0, 3: 3.0}
        label_value = segment_labels.get(index, 1.0)  # Default to 1.0 if index is not found

        print("index from stl segment",index)
        print(f"Selected label: {label_value}")

        stl_output_file = os.path.join(output_dir, f"output_mesh_{label_value}.stl")

        self.visualize_stl_file(stl_output_file)

        # pass
    def segment_selection_changed(self, index):
        segment_labels = {0: 1.0, 1: 2.0, 2: 7.0, 3: 3.0}
        label_value = segment_labels.get(index, 1.0)  # Default to 1.0 if index is not found

        print(f"Selected index: {index}")
        print(f"Selected segment name: {self.ui.segments_comboBox.itemText(index)}")

       
        input_image_file = "volume Rendering/CT_Masks.nrrd"
        output_segment_file = os.path.join(output_dir, f"segment_{label_value}.nrrd")
        stl_output_file = os.path.join(output_dir, f"output_mesh_{label_value}.stl")
        vtp_output_file = os.path.join(output_dir, f"polydata_mesh_{label_value}.vtp")

        # Read input image
        reader = sitk.ImageFileReader()
        reader.SetImageIO("NrrdImageIO")
        reader.SetFileName(input_image_file)
        image = reader.Execute()

        # Write segment file if it doesn't exist
        if not os.path.exists(output_segment_file):
            extracted_region = sitk.BinaryThreshold(image, lowerThreshold=label_value, upperThreshold=label_value)
            physical_size = sitk.GetArrayFromImage(extracted_region).sum() * image.GetSpacing()[0] * image.GetSpacing()[1] * image.GetSpacing()[2]
            sitk.WriteImage(extracted_region, output_segment_file)
            # Compute the physical size of the binary mask
            print(f"Segment file written: {output_segment_file}")
        else:
            extracted_region = sitk.BinaryThreshold(image, lowerThreshold=label_value, upperThreshold=label_value)
            physical_size = sitk.GetArrayFromImage(extracted_region).sum() * image.GetSpacing()[0] * image.GetSpacing()[1] * image.GetSpacing()[2]
            print(f"Pysical Size (mm3): {physical_size}")
            print(f"Segment file already exists: {output_segment_file}")

        
        self.ui.vector_size.setText(f"{physical_size:.3f} (mm3)")

        # Convert SimpleITK image to VTK image
        print(output_segment_file)
        itk_image = itk.imread(output_segment_file)
        vtk_image = itk.vtk_image_from_image(itk_image)

        # Create a Marching Cubes filter
        marching_cubes = vtk.vtkMarchingCubes()
        marching_cubes.SetInputData(vtk_image)
        marching_cubes.SetValue(0, 1.0) # Should be 1.0 as we already converted the image to binary 
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

        # Write STL file if it doesn't exist
        if not os.path.exists(stl_output_file):
            stl_writer = vtk.vtkSTLWriter()
            stl_writer.SetFileName(stl_output_file)
            stl_writer.SetInputData(poly_data)
            stl_writer.Write()
            print(f"STL file written: {stl_output_file}")
        else:
            print(f"STL file already exists: {stl_output_file}")

   
    def visualize_stl_file(self, input_filename):
        # Set up colors
        colors = vtk.vtkNamedColors()

        # Create STL reader
        reader = vtk.vtkSTLReader()
        reader.SetFileName(input_filename)
        reader.Update()

        # Create mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(reader.GetOutputPort())
        mapper.SetScalarVisibility(0)

        # Create actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetDiffuse(0.8)
        actor.GetProperty().SetDiffuseColor(colors.GetColor3d('Ivory'))
        actor.GetProperty().SetSpecular(0.3)
        actor.GetProperty().SetSpecularPower(60.0)

        # Create renderer
        renderer = vtk.vtkRenderer()
        renderer.AddActor(actor)
        renderer.SetBackground(colors.GetColor3d('SlateGray'))

        # Create render window
        render_window = vtk.vtkRenderWindow()
        render_window.AddRenderer(renderer)
        render_window.SetSize(500, 500)

        # Create interactor
        interactor = vtk.vtkRenderWindowInteractor()
        interactor.SetRenderWindow(render_window)

        # Start interaction
        interactor.Start()



    def render_volume(self, filename):
        if self.vtk_widget is not None:
            # If vtk_widget already exists, delete it before creating a new one
            self.vtk_widget.deleteLater()

        # Create a new instance of VolumeRenderer
        volume_renderer = VolumeRenderer()

        # Set the filename for rendering volume
        volume_renderer.filename = filename

        # Render the volume on the VTK widget
        volume_renderer.render_volume_CT()



if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    app = QApplication([])
    main_window = DemoApp()
    # main_window.initialize()
    main_window.setWindowTitle("CT-Task")
    main_window.show()
    app.exec_()

