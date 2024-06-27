import adsk.core, adsk.fusion
import os, pathlib, itertools
from math import sqrt
from ...lib import fusionAddInUtils as futil
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface
brep_manager = adsk.fusion.TemporaryBRepManager.get()

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
    inputs = args.command.commandInputs
    futil.log(f'{CMD_NAME} Command Created Event')
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)

    template_body = inputs.addSelectionInput(
        'tetrahedron_template_input',
        'Template Body',
        'Select a body defined by a unit tetrahedron. This body will be patterned inside the mesh.'
    )
    template_body.setSelectionLimits(1, 1)
    template_body.clearSelectionFilter()
    template_body.addSelectionFilter(adsk.core.SelectionFilters.Bodies)
    node_file_button = inputs.addBoolValueInput(
        'node_file_button_input',
        'Node File',
        False,
        os.path.join(ICON_FOLDER, 'button'),
        False,
    )
    element_file_button = inputs.addBoolValueInput(
        'element_file_button_input',
        'Element File File',
        False,
        os.path.join(ICON_FOLDER, 'button'),
        False,
    )
    node_file = inputs.addTextBoxCommandInput(
        'node_file_input',
        'Selected Node File',
        'None Selected',
        1,
        True,
    )
    element_file = inputs.addTextBoxCommandInput(
        'element_file_input',
        'Selected Element File',
        'None Selected',
        1,
        True,
    )

def command_execute(args: adsk.core.CommandEventArgs):
    inputs = args.command.commandInputs
    futil.log(f'{CMD_NAME} Command Execute Event')

    template_body_input = adsk.core.SelectionCommandInput.cast(inputs.itemById('tetrahedron_template_input'))
    node_file_input = adsk.core.TextBoxCommandInput.cast(inputs.itemById('node_file_input')).text
    element_file_input = adsk.core.TextBoxCommandInput.cast(inputs.itemById('element_file_input')).text

    node_file_lines = open(node_file_input).readlines()[1:]
    element_file_lines = open(element_file_input).readlines()[1:-1]
    nodes = [line.split()[1:] for line in node_file_lines]
    elements = [line.split()[1:-1] for line in element_file_lines]

    template_body = adsk.fusion.BRepBody.cast(template_body_input.selection(0).entity)

    active_component = adsk.fusion.Design.cast(app.activeProduct).activeComponent

    new_base_feature = active_component.features.baseFeatures.add()
    new_base_feature.name = "TetrahedralMesh"
    new_base_feature.startEdit()

    new_bodies = []
    for element in elements:
        nodes_in_element = [
            tuple(map(lambda p: float(p), nodes[int(vertex)-1]))
            for vertex in element
        ]
        raw_target_matrix = [
            nodes_in_element[0][0], nodes_in_element[1][0], nodes_in_element[2][0], nodes_in_element[3][0],
            nodes_in_element[0][1], nodes_in_element[1][1], nodes_in_element[2][1], nodes_in_element[3][1],
            nodes_in_element[0][2], nodes_in_element[1][2], nodes_in_element[2][2], nodes_in_element[3][2],
            1.0, 1.0, 1.0, 1.0
        ]
        target_matrix = adsk.core.Matrix3D.create()
        target_matrix.setWithArray(raw_target_matrix)
        transformation_matrix = create_transformation_matrix(target_matrix)

        new_bodies.append(brep_manager.copy(template_body))
        brep_manager.transform(new_bodies[-1], transformation_matrix)

    target_body = new_bodies[0]
    for tool_body in new_bodies[1:]:
        res = brep_manager.booleanOperation(target_body, tool_body, adsk.fusion.BooleanTypes.UnionBooleanType)

    active_component.bRepBodies.add(target_body, new_base_feature)
    new_base_feature.finishEdit()

def command_preview(args: adsk.core.CommandEventArgs):
    inputs = args.command.commandInputs
    futil.log(f'{CMD_NAME} Command Preview Event')

def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    if changed_input.id == 'node_file_button_input':
        node_dialog = ui.createFileDialog()
        node_dialog.filter = '*.node'
        node_dialog.title = 'Select Node File'
        node_dialog.isMultiSelectEnabled = False
        node_dialog.initialDirectory = os.path.join(os.path.abspath(pathlib.Path.home()), 'Desktop')
        if node_dialog.showOpen() == adsk.core.DialogResults.DialogOK:
            node_file = adsk.core.TextBoxCommandInput.cast(args.inputs.itemById('node_file_input'))
            node_file.formattedText = node_dialog.filename

    if changed_input.id == 'element_file_button_input':
        element_dialog = ui.createFileDialog()
        element_dialog.filter = '*.ele'
        element_dialog.title = 'Select Element File'
        element_dialog.isMultiSelectEnabled = False
        element_dialog.initialDirectory = os.path.join(os.path.abspath(pathlib.Path.home()), 'Desktop')
        if element_dialog.showOpen() == adsk.core.DialogResults.DialogOK:
            element_file = adsk.core.TextBoxCommandInput.cast(args.inputs.itemById('element_file_input'))
            element_file.formattedText = element_dialog.filename

    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')

def command_destroy(args: adsk.core.CommandEventArgs):
    global local_handlers
    local_handlers = []
    futil.log(f'{CMD_NAME} Command Destroy Event')

def create_transformation_matrix(target: adsk.core.Matrix3D):
    raw_tetrahedron = [
        sqrt(8 / 9), -sqrt(2 / 9), -sqrt(2 / 9), 0.0,
        0.0, -sqrt(2 / 3), sqrt(2 / 3), 0.0,
        -1 / 3, -1 / 3, -1 / 3, 1.0,
        1.0, 1.0, 1.0, 1.0,
    ]
    transformation_matrix = adsk.core.Matrix3D.create()
    transformation_matrix.setWithArray(raw_tetrahedron)
    transformation_matrix.invert()
    transformation_matrix.transformBy(target)
    return transformation_matrix
