import os
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog
from Rendering import VolumeRenderer
from data_processing import generate_mask_polydata, write_stl

OUTPUT_Dir = "output"

class AppLogic:
    def __init__(self, ui, vtk_widgets):
        self.ui = ui
        self.volume_renderer = VolumeRenderer(vtk_widgets)  
        self.setup_ui_connections()

    def find_main_window(self):
        parent = self.ui.upload_ct_button
        while parent:
            if isinstance(parent, QtWidgets.QMainWindow):
                return parent
            parent = parent.parent()
        return None 
  
    def generate_file_paths_label(self, index):
        segment_labels = {0: 2.0, 1: 1.0, 2: 7.0, 3: 3.0}
        label_value = segment_labels.get(index, 1.0)
        stl_output_file = os.path.join(OUTPUT_Dir, f"output_mesh_{label_value}.stl")
        output_segment_file = os.path.join(OUTPUT_Dir, f"segment_{label_value}.nrrd")
        vtp_output_file = os.path.join(OUTPUT_Dir, f"polydata_mesh_{label_value}.vtp")
        return stl_output_file, output_segment_file, vtp_output_file, label_value      

    def setup_ui_connections(self):
        self.ui.upload_ct_button.clicked.connect(self.open_ct_file)
        self.ui.export_stl.clicked.connect(self.export_stl_segment) # only export stl file
        self.ui.view_segment.clicked.connect(self.view_stl_segment) # TODO: make it only view segment from polydata 
        self.ui.segments_comboBox.currentIndexChanged.connect(self.segment_selection_changed)

    def open_ct_file(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self.find_main_window(), "Open CT File", "", "NRRD Files (*.nrrd)", options=options)
        if filename:
            self.volume_renderer.set_filename(filename)
            self.volume_renderer.render_data(data_type="volume")

    def export_stl_segment(self):
        stl_output_file, output_segment_file, vtp_output_file, label_value = self.generate_file_paths_label(self.ui.segments_comboBox.currentIndex())
        _,_ = generate_mask_polydata(output_segment_file, vtp_output_file, label_value)
        write_stl(stl_output_file, vtp_output_file)
        self.ui.vector_size.setText(f"Exported path: {stl_output_file} ")   
     
    def view_stl_segment(self):
        _, output_segment_file, vtp_output_file, label_value = self.generate_file_paths_label(self.ui.segments_comboBox.currentIndex())
        poly_data, physical_size = generate_mask_polydata(output_segment_file, vtp_output_file, label_value)
        self.ui.vector_size.setText(f"{str(self.ui.segments_comboBox.currentText())} has a surface volume of: {physical_size:.4f} mm^3")
        self.volume_renderer.set_poly_data(poly_data)
        self.volume_renderer.render_data(data_type="polydata")
   
    def segment_selection_changed(self):
        self.ui.vector_size.setText(f"{str(self.ui.segments_comboBox.currentText())} is ready for [View | Export] actions")
