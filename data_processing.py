import os
import vtk
import itk
import SimpleITK as sitk

input_image_file = "volume Rendering/CT_Masks.nrrd"

def compute_physical_size(extracted_region):
    physical_size = sitk.GetArrayFromImage(extracted_region).sum() * extracted_region.GetSpacing()[0] * extracted_region.GetSpacing()[1] * extracted_region.GetSpacing()[2]
    return physical_size

def generate_mask_polydata(output_segment_file, vtp_output_file, label_value=1.0):
    poly_data = vtk2polydata(output_segment_file, label_value, vtp_output_file)
    extracted_region = read_nrrd_file(output_segment_file) 
    physical_size = compute_physical_size(extracted_region)
    return poly_data, physical_size

def write_stl(stl_output_file, vtp_output_file):
    if not os.path.exists(stl_output_file):
        reader = read_polydata_file(vtp_output_file)
        stl_writer = vtk.vtkSTLWriter()
        stl_writer.SetFileName(stl_output_file)
        stl_writer.SetFileTypeToBinary()  # Set STL writer to binary mode (small file size)
        stl_writer.SetInputData(reader)
        stl_writer.Write()    

def extract_segment(output_segment_file, image, label_value):
    if not os.path.exists(output_segment_file):
        extracted_region = sitk.BinaryThreshold(image, lowerThreshold=label_value, upperThreshold=label_value)
        # Write Compressed NRRD file form  70MB to 1.5MB
        writer = sitk.ImageFileWriter()
        writer.SetFileName(output_segment_file)
        writer.UseCompressionOn()
        writer.Execute(extracted_region)
        return extracted_region
    else:
        return read_nrrd_file(output_segment_file)

def vtk2polydata(output_segment_file, label_value, vtp_output_file):
    if not os.path.exists(vtp_output_file):
        if not os.path.exists(output_segment_file):
            image = read_nrrd_file(input_image_file)
            _ = extract_segment(output_segment_file, image, label_value)
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
        return read_polydata_file(vtp_output_file)

def read_nrrd_file(filename):
    reader = sitk.ImageFileReader()
    reader.SetImageIO("NrrdImageIO")
    reader.SetFileName(filename)
    image = reader.Execute()
    return image

def read_polydata_file(vtp_output_file):
    reader = vtk.vtkXMLPolyDataReader()
    reader.SetFileName(vtp_output_file)
    reader.Update()
    poly_data = vtk.vtkPolyData()
    poly_data.ShallowCopy(reader.GetOutput())
    return poly_data
