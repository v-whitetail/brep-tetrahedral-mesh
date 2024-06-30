import adsk.core, adsk.fusion
import os
from math import sqrt
from ...lib import fusionAddInUtils as futil
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface
brep_manager = adsk.fusion.TemporaryBRepManager.get()

CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_default_joint'
CMD_NAME = 'Default Edge Joint'
CMD_Description = 'Creates an simple edge joint with the appropriate dimensions'
IS_PROMOTED = True

PALETTE_ID = config.sample_palette_id

WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidCreatePanel'
COMMAND_BESIDE_ID = ''

ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

local_handlers = []

def start():
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)
    futil.add_handler(cmd_def.commandCreated, command_created)
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)
    control.isPromoted = IS_PROMOTED

def stop():
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)
    if command_control:
        command_control.deleteMe()
    if command_definition:
        command_definition.deleteMe()

def command_created(args: adsk.core.CommandCreatedEventArgs):
    futil.log(f'{CMD_NAME} Command Created Event')
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)

def command_execute(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Execute Event')

    active_component = adsk.fusion.Design.cast(app.activeProduct).activeComponent

    new_base_feature = active_component.features.baseFeatures.add()
    new_base_feature.name = 'defaultJoint'
    new_base_feature.startEdit()

    new_body = define_default_joint()

    active_component.bRepBodies.add(new_body, new_base_feature)
    new_base_feature.finishEdit()

def command_destroy(args: adsk.core.CommandEventArgs):
    global local_handlers
    local_handlers = []
    futil.log(f'{CMD_NAME} Command Destroy Event')

def define_default_joint():
    bodies = [
        brep_manager.createSphere(adsk.core.Point3D.create(0.0, 0.0, 0.0), 1.0),
        brep_manager.createSphere(adsk.core.Point3D.create(10.0, 0.0, 0.0), 1.0),
        brep_manager.createCylinderOrCone(
            adsk.core.Point3D.create(0.0, 0.0, 0.0), 0.5,
            adsk.core.Point3D.create(10.0, 0.0, 0.0), 0.5,
        ),
    ]
    brep_manager.booleanOperation(bodies[0], bodies[1], adsk.fusion.BooleanTypes.UnionBooleanType)
    brep_manager.booleanOperation(bodies[0], bodies[2], adsk.fusion.BooleanTypes.UnionBooleanType)
    return bodies[0]
