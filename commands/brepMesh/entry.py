import adsk.core, adsk.fusion
import os, pathlib
from ...lib import fusionAddInUtils as futil
from ... import config


app = adsk.core.Application.get()
ui = app.userInterface

CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_brep_mesh'
CMD_NAME = 'Mesh Body'
CMD_Description = 'Creates a mesh body from a unit tetrahedron boundary and tetrahedral mesh files.'
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
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)

    inputs = args.command.commandInputs

    template_body = inputs.addSelectionInput(
        'tetrahedron_template_input',
        'Template Body',
        'Select a body defined by a unit tetrahedron. This body will be patterned inside the mesh.'
    )
    template_body.setSelectionLimits(1, 1)
    template_body.clearSelectionFilter()
    template_body.addSelectionFilter(adsk.core.SelectionFilters.Bodies)

    node_file = inputs.addBoolValueInput(
        'node_file_input',
        'Node File',
        False,
        os.path.join(ICON_FOLDER, 'button'),
        False,
    )
    element_file = inputs.addBoolValueInput(
        'edge_file_input',
        'Edge File',
        False,
        os.path.join(ICON_FOLDER, 'button'),
        False,
    )

def command_execute(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Execute Event')
    inputs = args.command.commandInputs

def command_preview(args: adsk.core.CommandEventArgs):
    inputs = args.command.commandInputs
    futil.log(f'{CMD_NAME} Command Preview Event')

def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    if changed_input.id == 'node_file_input':
        node_dialog = ui.createFileDialog()
        node_dialog.filter = '*.node'
        node_dialog.title = 'Select Node File'
        node_dialog.isMultiSelectEnabled = False
        node_dialog.initialDirectory = os.path.join(os.path.abspath(pathlib.Path.home()), 'Desktop')
        node_dialog.showOpen()
    if changed_input.id == 'element_file_input':
        node_dialog = ui.createFileDialog()
        node_dialog.filter = '*.ele'
        node_dialog.title = 'Select Element File'
        node_dialog.isMultiSelectEnabled = False
        node_dialog.initialDirectory = os.path.join(os.path.abspath(pathlib.Path.home()), 'Desktop')
        node_dialog.showOpen()
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')

def command_destroy(args: adsk.core.CommandEventArgs):
    global local_handlers
    local_handlers = []
    futil.log(f'{CMD_NAME} Command Destroy Event')
