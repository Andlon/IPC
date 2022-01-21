import glob
import subprocess
from pathlib import Path
from tools.paraview_convert import find_ordered_obj_files, convert_files, create_pvd


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


for file in glob.glob("input/problems/cube_slide/*.txt"):
    config = parse_config(file)
    output_directory = "outputs/cube_slide_{}_dt={}".format(config.integrator, float(config.dt))
    run_ipc(file, output_directory)
    directory = Path(output_directory)
    obj_files = find_ordered_obj_files(directory)
    mesh_files = convert_files(obj_files, prefix="mesh")
    create_pvd(mesh_files, config.dt, directory / f"mesh_{config.integrator}_dt={config.dt}.pvd")

