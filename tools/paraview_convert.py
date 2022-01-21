import argparse
import meshio
from pathlib import Path
from itertools import takewhile

PVD_FORMAT_STRING = \
"""<?xml version="1.0"?>
<VTKFile type="Collection" version="0.1" byte_order="LittleEndian" compressor="vtkZLibDataCompressor">
    <Collection>
{}
    </Collection>
</VTKFile>
"""


def create_pvd(dataset_paths, dt, output_path):
    times = [float(dt) * float(extract_time_index(path)) for path in dataset_paths]
    s = "        "
    relative_paths = [Path(path).relative_to(output_path.parent) for path in dataset_paths]
    datasets = [f"""{s}<DataSet timestep="{t}" group="" part="0" file="{path}" />"""
                for (t, path) in zip(times, relative_paths)]
    document = PVD_FORMAT_STRING.format("\n".join(datasets))
    with open(output_path, "w") as file:
        file.write(document)


def extract_time_index(filename):
    # Assume pattern prefix<NUM>.ext
    return int(''.join(takewhile(lambda char: char.isnumeric(), reversed(filename.stem)))[::-1])


# Find OBJ files ordered by their temporal index
def find_ordered_obj_files(directory):
    directory = Path(directory)
    # This GLOB pattern is a bit hacky: it suffices for our purposes, since there won't be any other file names
    # that might match
    files = directory.glob("[0-9]*.obj")
    return sorted(files, key=extract_time_index)


# Converts the given filenames representing OBJ files and returns the corresponding output names (in the same order)
def convert_files(files, prefix):
    output_files = []
    for obj_file in files:
        mesh = meshio.read(obj_file)
        directory = Path(obj_file).parent
        output_path = directory / "{}_{}.vtu".format(prefix, obj_file.stem)
        output_files.append(output_path)
        mesh.write(output_path)
    return output_files


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert OBJ output from an IPC simulation to VTU+PVD.')
    parser.add_argument('directory', help='Directory in which to look for OBJ files')
    parser.add_argument('--prefix', default='mesh', help='Prefix to add to converted files')
    parser.add_argument('--dt')
    args = parser.parse_args()

    directory = Path(args.directory)
    obj_files = find_ordered_obj_files(args.directory)
    mesh_files = convert_files(obj_files, args.prefix)

    if args.dt is not None:
        create_pvd(mesh_files, args.dt, directory / "mesh.pvd")
