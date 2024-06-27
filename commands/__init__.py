from .brepMesh import entry as brepMesh
from .unitTetrahedron import entry as unitTetrahedron

commands = [
    unitTetrahedron,
    brepMesh,
]
def start():
    for command in commands:
        command.start()
def stop():
    for command in commands:
        command.stop()