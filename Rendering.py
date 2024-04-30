import os
import vtk
import SimpleITK as sitk
import random
from time import sleep  
from PyQt5.QtWidgets import QHBoxLayout, QFrame, QGridLayout
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


class VolumeRenderer(QFrame):
    def __init__(self, vtk_widgets):
        super(VolumeRenderer, self).__init__()
        self.filename = None
        self.stlfilename = None
        self.all_vtk_widgets = vtk_widgets
        # self.renderer = vtk.vtkRenderer()
        self.renderer_list = []  # Store renderers for each widget
        self.actor_list = []  # Store cube actors in a list
        self.next_grid_index = 0  # Track the index of the next grid to place the cube
        self.initialize_renderer()

    def initialize_renderer(self):
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        # Loop through all vtk_widgets and add a placeholder cube for each
        for vtk_widget in self.all_vtk_widgets:
            renderer = vtk.vtkRenderer()
            renderer.SetBackground(0.2, 0.3, 0.4)  # Set up renderer background
            render_window = vtk_widget.GetRenderWindow()
            render_window.AddRenderer(renderer)
            self.renderer_list.append(renderer)  # Store the renderer
            # render_window.Render()
            # Create an instance of VolumeRenderer and add a placeholder cube
            self.add_placeholder_cube(renderer)
        print(len(self.actor_list), len(self.all_vtk_widgets))    

    def clear_all_actors(self):
        for vtk_widget in self.all_vtk_widgets:
            render_window = vtk_widget.GetRenderWindow()
            renderer = render_window.GetRenderers().GetFirstRenderer()
            if renderer:
                renderer.RemoveAllViewProps()
                render_window.Render()
        self.actor_list = []  # Clear the list of actors
        print(len(self.actor_list), len(self.all_vtk_widgets))   

    def clear_actor_in_grid_index(self, index):
        if index < len(self.renderer_list):
            renderer = self.renderer_list[index]
            renderer.RemoveAllViewProps()
            render_window = self.all_vtk_widgets[index].GetRenderWindow()
            render_window.Render()
            print(f"Cleared actors in grid index {index}")
        else:
            print(f"Invalid grid index: {index}. No actors cleared.")

        
    def add_placeholder_cube(self, renderer):
        # Data Source
        cube = vtk.vtkCubeSource()
        # Mapper | pass datasource to mapper
        cube_mapper = vtk.vtkPolyDataMapper()
        cube_mapper.SetInputConnection(cube.GetOutputPort())
        # Actor | pass mapper to actor
        actor = vtk.vtkActor()
        actor.SetMapper(cube_mapper)
        actor.GetProperty().SetColor(1, 0, 0)
        actor.GetProperty().SetRepresentationToWireframe()
        # Add the actor to the renderer
        renderer.AddActor(actor)
        # Store the actor in the list for later reference or manipulation
        self.actor_list.append(actor)
        render_window = renderer.GetRenderWindow()
        render_window.Render()


    def add_cube(self):
        if self.next_grid_index < len(self.all_vtk_widgets):
            # Clear the actor in the current grid index
            self.clear_actor_in_grid_index(self.next_grid_index)
            print("Remove actor...adding cube...")
            # Add the cube to the current grid index
            renderer = self.renderer_list[self.next_grid_index]

            cube = vtk.vtkCubeSource()
            cube_mapper = vtk.vtkPolyDataMapper()
            cube_mapper.SetInputConnection(cube.GetOutputPort())
            actor = vtk.vtkActor()
            actor.SetMapper(cube_mapper)
            # actor.GetProperty().SetRepresentationToWireframe()
            # Generate random color values
            color = [random.random(), random.random(), random.random()]
            actor.GetProperty().SetColor(color)
            
            renderer.AddActor(actor)
            # Update the actor list and render the window
            self.actor_list.append(actor)
            render_window = self.all_vtk_widgets[self.next_grid_index].GetRenderWindow()
            render_window.Render()
            # Move to the next grid index
            renderer.ResetCamera()
            renderer.ResetCameraClippingRange()
            self.next_grid_index = (self.next_grid_index + 1) % len(self.all_vtk_widgets)
        else:
            print("No more available renderers. Starting from the first one.")
            self.next_grid_index = 0
            self.add_cube()


        

            
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
        if self.next_grid_index < len(self.all_vtk_widgets):
            # Clear the actor in the current grid index
            self.clear_actor_in_grid_index(self.next_grid_index)
            # Add the cube to the current grid index
            renderer = self.renderer_list[self.next_grid_index]
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
            volume = vtk.vtkVolume()
            volume.SetMapper(volume_mapper)
            volume.SetProperty(volume_property)
            print("Adding volume to renderer...")
            renderer.AddVolume(volume)

            self.actor_list.append(volume)
            # renderer.SetBackground(self.colors.GetColor3d('BkgColor'))
            renderer.ResetCamera()
            print("Volume rendered end...")
            render_window = self.all_vtk_widgets[self.next_grid_index].GetRenderWindow()
            render_window.AddRenderer(renderer) 
            render_window.Render()
            # Move to the next grid index
            self.next_grid_index = (self.next_grid_index + 1) % len(self.all_vtk_widgets)
        else:
            print("No more available renderers. Starting from the first one.")
            self.next_grid_index = 0
            self.render_volume()



    def visualize_stl_file(self):
        if self.next_grid_index < len(self.all_vtk_widgets):
            # Clear the actor in the current grid index
            self.clear_actor_in_grid_index(self.next_grid_index)
            # Add the cube to the current grid index
            renderer = self.renderer_list[self.next_grid_index]
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
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetDiffuse(0.8)
            actor.GetProperty().SetDiffuseColor(colors.GetColor3d('Ivory'))
            actor.GetProperty().SetSpecular(0.3)
            actor.GetProperty().SetSpecularPower(60.0)
            # self.renderer.SetBackground(colors.GetColor3d('SlateGray'))
            # self.renderer.AddActor(self.actor)
            renderer.ResetCamera()
             # render the scene
            # self.render_window.AddRenderer(self.renderer)
            # self.render_window.Render()
            
            renderer.AddActor(actor)
            # Update the actor list and render the window
            self.actor_list.append(actor)
            render_window = self.all_vtk_widgets[self.next_grid_index].GetRenderWindow()
            render_window.Render()
            # Move to the next grid index
            self.next_grid_index = (self.next_grid_index + 1) % len(self.all_vtk_widgets)
        else:
            print("No more available renderers. Starting from the first one.")
            self.next_grid_index = 0
            self.visualize_stl_file()
