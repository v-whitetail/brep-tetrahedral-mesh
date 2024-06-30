from .brepMesh import entry as brepMesh
from .defaultJoint import entry as defaultJoint

commands = [
    defaultJoint,
    brepMesh,
]
def start():
    for command in commands:
        command.start()
def stop():
    for command in commands:
        command.stop()