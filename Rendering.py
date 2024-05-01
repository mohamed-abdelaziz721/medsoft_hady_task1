import vtk
import random
from PyQt5.QtWidgets import  QFrame

class VolumeRenderer(QFrame):
    def __init__(self, vtk_widgets):
        super(VolumeRenderer, self).__init__()
        self.filename = None
        self.all_vtk_widgets = vtk_widgets
        self.renderer_list = []
        self.actor_list = [] 
        self.next_grid_index = 0 
        self.poly_data = None
        self.initialize_renderers()

    def render_data(self, data_type="volume"):
        if data_type == "volume":
            self.render_volume()
        elif data_type == "polydata":
            self.render_polydata()    

    def set_filename(self, filename):
        self.filename = filename

    def set_poly_data(self, poly_data):
        self.poly_data = poly_data    
    
    def set_vtk_widgets(self, vtk_widgets):
        # TODO: move to refactor_QGrid
        # for loop QVTKRenderWindowInteractor
        # initialize widgets from outside the renderer
        pass

    def initialize_renderers(self):
        for vtk_widget in self.all_vtk_widgets:
            renderer = vtk.vtkRenderer()
            renderer.SetBackground(0.2, 0.3, 0.4)  # Set up renderer background
            render_window = vtk_widget.GetRenderWindow()
            render_window.AddRenderer(renderer)
            self.renderer_list.append(renderer)  # Store the renderer
        print(len(self.actor_list), len(self.all_vtk_widgets))    

    def clear_actor_in_grid_index(self, index):
        if index < len(self.renderer_list):
            renderer = self.renderer_list[index]
            renderer.RemoveAllViewProps()
            render_window = self.all_vtk_widgets[index].GetRenderWindow()
            render_window.Render()

    def render_volume(self):
        if self.next_grid_index < len(self.all_vtk_widgets):
            self.clear_actor_in_grid_index(self.next_grid_index)
            renderer = self.renderer_list[self.next_grid_index]
            if self.filename is None:
                print("Error: No filename provided.")
                return
            reader = vtk.vtkNrrdReader()
            reader.SetFileName(self.filename)
            self.colors = vtk.vtkNamedColors()
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
            volume_mapper = vtk.vtkGPUVolumeRayCastMapper()
            volume_mapper.SetInputConnection(reader.GetOutputPort())
            volume = vtk.vtkVolume()
            volume.SetMapper(volume_mapper)
            volume.SetProperty(volume_property)
            renderer.AddVolume(volume)
            self.actor_list.append(volume)
            renderer.ResetCamera()
            render_window = self.all_vtk_widgets[self.next_grid_index].GetRenderWindow()
            render_window.AddRenderer(renderer) 
            render_window.Render()
        self.next_grid_index = (self.next_grid_index + 1) % len(self.all_vtk_widgets)

    def render_polydata(self):
        if self.next_grid_index < len(self.all_vtk_widgets):
            self.clear_actor_in_grid_index(self.next_grid_index)
            renderer = self.renderer_list[self.next_grid_index]
            if self.poly_data is None:
                print("Error: No poly data provided.")
                return
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(self.poly_data)
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            renderer.AddActor(actor)
            self.actor_list.append(actor)
            renderer.ResetCamera()
            render_window = self.all_vtk_widgets[self.next_grid_index].GetRenderWindow()
            render_window.Render()
        self.next_grid_index = (self.next_grid_index + 1) % len(self.all_vtk_widgets)