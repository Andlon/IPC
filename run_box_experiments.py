import glob
import subprocess
from pathlib import Path
from tools.paraview_convert import find_ordered_obj_files, convert_files, create_pvd

OUTPUTS_DIR = "outputs"

PARAVIEW_STATE_TEMPLATE = """
from paraview.simple import *

# create a new 'Plane'
ground = Plane(registrationName='Ground plane')
ground.Origin = [-50.0, 0.0, -50.0]
ground.Point1 = [50.0, 0.0, -50.0]
ground.Point2 = [-50.0, 0.0, 50.0]
ground.XResolution = 100
ground.YResolution = 100

{}
"""


class SimulationConfig:
    integrator = None
    duration = None
    dt = None


def parse_config(path):
    config = SimulationConfig()

    with open(path) as file:
        lines = file.readlines()
        for line in lines:
            parts = [part.strip() for part in line.split(" ") if part.strip() != ""]
            if len(parts) > 0:
                if parts[0] == "timeIntegration":
                    config.integrator = parts[1]
                elif parts[0] == "time":
                    config.duration = parts[1]
                    config.dt = parts[2]

    assert (config.dt is not None)
    assert (config.duration is not None)
    assert (config.integrator is not None)
    return config


def run_ipc(input, output):
    args = [
        './build/IPC_bin',
        'offline',  # no GUI
        input,
        '-o',
        output
    ]
    subprocess.call(args)


# Creates a .py file that when loaded by ParaView loads all the PVD files we exported
def produce_paraview_state_file(pvd_paths):
    def create_python_entry(path):
        path = Path(path)
        return f"PVDReader(registrationName='{path.stem}', FileName='{path.absolute()}')"

    entries = [create_python_entry(path) for path in pvd_paths]
    entries_string = "\n".join(entries)
    python_content = PARAVIEW_STATE_TEMPLATE.format(entries_string)
    state_file_path = Path(OUTPUTS_DIR) / "load_paraview_state.py"
    with open(state_file_path, 'w') as file:
        file.write(python_content)


if __name__ == "__main__":
    pvd_paths = []
    for file in glob.glob("input/problems/cube_slide/*.txt"):
        config = parse_config(file)
        output_directory = "{}/cube_slide_{}_dt={}".format(OUTPUTS_DIR, config.integrator, float(config.dt))
        run_ipc(file, output_directory)
        directory = Path(output_directory)
        obj_files = find_ordered_obj_files(directory)
        mesh_files = convert_files(obj_files, prefix="mesh")
        pvd_file_name = f"mesh_{config.integrator}_dt={config.dt}.pvd"
        pvd_path = directory / f"mesh_{config.integrator}_dt={config.dt}.pvd"
        create_pvd(mesh_files, config.dt, directory / f"mesh_{config.integrator}_dt={config.dt}.pvd")
        pvd_paths.append(pvd_path)

    produce_paraview_state_file(pvd_paths)
