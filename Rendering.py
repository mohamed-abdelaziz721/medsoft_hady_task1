import os
import vtk
import SimpleITK as sitk
from PyQt5.QtWidgets import QHBoxLayout, QFrame
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


class VolumeRenderer(QFrame):
    def __init__(self, vtk_widget):
        super(VolumeRenderer, self).__init__()
        self.filename = None
        self.stlfilename = None
        self.interactor = vtk_widget
        self.renderer = vtk.vtkRenderer()
        self.layout = QHBoxLayout()
        self.actor = vtk.vtkActor()
        self.initialize_renderer()

        self.add_placeholder_cube()


    def initialize_renderer(self):
        self.layout = QHBoxLayout()
        self.new_renderer = QVTKRenderWindowInteractor()
        self.layout.addWidget(self.new_renderer)
        self.layout.setContentsMargins(0,0,0,0)
        self.setLayout(self.layout)
        # Set up renderer background
        self.renderer.SetBackground(0.2, 0.3, 0.4) # blueish background
        # Set up render window
        self.render_window = self.new_renderer.GetRenderWindow()
        self.render_window.AddRenderer(self.renderer)


    def clear_all_actors(self):
        if self.actor is not None:
            self.renderer.RemoveActor(self.actor)
            self.renderer.RemoveAllViewProps()
            self.renderer.SetBackground(0.2, 0.3, 0.4)
            # Render the empty scene
            self.render_window.Render()
            print("Cleared all actors and view Props...")
        else:
            print("No actors to clear...") 


          
    def add_placeholder_cube(self):
        # Data Source
        cube = vtk.vtkCubeSource()
        # Mapper | pass datasource to mapper
        cube_mapper = vtk.vtkPolyDataMapper()
        cube_mapper.SetInputConnection(cube.GetOutputPort())
        # Actor | pass mapper to actor
        self.actor = vtk.vtkActor()  # Store cube actor as an attribute
        self.actor.SetMapper(cube_mapper)
        self.actor.GetProperty().SetColor(1, 0, 0)
        self.actor.GetProperty().SetRepresentationToWireframe()
        # Add the actor to the renderer
        self.renderer.AddActor(self.actor)
        # Add the renderer to the render window
        self.render_window = self.interactor.GetRenderWindow()
        self.render_window.AddRenderer(self.renderer)
        # Render the scene
        self.render_window.Render()
        print("Cube Placeholder Initialized")

    def add_cube(self):
        # Create a cube source
        cube = vtk.vtkCubeSource()
        # Create a cube mapper 
        cube_mapper = vtk.vtkPolyDataMapper()
        cube_mapper.SetInputConnection(cube.GetOutputPort())
        # create a cube actor | pass the mapper to the actor
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(cube_mapper)
        self.actor.GetProperty().SetColor(0, 1, 0)
        # self.actor.GetProperty().SetRepresentationToWireframe()
        # Add the actor to the renderer 
        self.renderer.AddActor(self.actor)
        # render the scene
        self.render_window.AddRenderer(self.renderer)
        self.render_window.Render()
        print("Cube added")


        

            
    def render_data(self, data_type="volume"):
        if data_type == "volume":
            self.render_volume()
        elif data_type == "stl":
            self.visualize_stl_file()


    def set_filename(self, filename):
        self.filename = filename

    def set_stlfilename(self, stlfilename):
        self.stlfilename = stlfilename

    def render_volume(self):
        print("Rendering volume...")
        if self.filename is None:
            print("Error: No filename provided.")
            return
        
        reader = vtk.vtkNrrdReader()
        reader.SetFileName(self.filename)

        # Set volume property attributes
        self.colors = vtk.vtkNamedColors()
        # self.colors.SetColor('BkgColor', [51, 77, 102, 255])
        
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

        volume_property = vtk.vtkVolumeProperty()
        volume_property.SetColor(colorTransferFunction)
        volume_property.SetScalarOpacity(volumeScalarOpacity)
        volume_property.SetGradientOpacity(volumeGradientOpacity)
        volume_property.SetInterpolationTypeToLinear()
        volume_property.ShadeOn()
        volume_property.SetAmbient(0.4)
        volume_property.SetDiffuse(0.6)
        volume_property.SetSpecular(0.2)
        print("Finished setting volume property...")
        volume_mapper = vtk.vtkGPUVolumeRayCastMapper()
        volume_mapper.SetInputConnection(reader.GetOutputPort())
        self.volume = vtk.vtkVolume()
        self.volume.SetMapper(volume_mapper)
        self.volume.SetProperty(volume_property)
        print("Adding volume to renderer...")
        self.renderer.AddVolume(self.volume)
        # self.renderer.SetBackground(self.colors.GetColor3d('BkgColor'))
        self.renderer.ResetCamera()
        self.render_window.AddRenderer(self.renderer)
        self.render_window.Render()
        print("Volume rendered end...")


    def visualize_stl_file(self):
        if self.stlfilename is None:
            print("Error: No STL filename provided.")
            return

        reader = vtk.vtkSTLReader()
        reader.SetFileName(self.stlfilename)
        reader.Update()

        # Set up colors
        colors = vtk.vtkNamedColors()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(reader.GetOutputPort())
        mapper.SetScalarVisibility(0)
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(mapper)
        self.actor.GetProperty().SetDiffuse(0.8)
        self.actor.GetProperty().SetDiffuseColor(colors.GetColor3d('Ivory'))
        self.actor.GetProperty().SetSpecular(0.3)
        self.actor.GetProperty().SetSpecularPower(60.0)
        # self.renderer.SetBackground(colors.GetColor3d('SlateGray'))
        self.renderer.AddActor(self.actor)
        self.renderer.ResetCamera()
         # render the scene
        self.render_window.AddRenderer(self.renderer)
        self.render_window.Render()
