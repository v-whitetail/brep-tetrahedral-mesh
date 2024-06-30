from .brepMesh import entry as brepMesh

commands = [
    brepMesh,
]
def start():
    for command in commands:
        command.start()
def stop():
    for command in commands:
        command.stop()