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

    node_template_input = inputs.addSelectionInput(
        'node_template_input',
        'Template Node',
        'Select a body to serve as template geometry at every node.'
    )
    node_template_input.setSelectionLimits(1, 1)
    node_template_input.clearSelectionFilter()
    node_template_input.addSelectionFilter(adsk.core.SelectionFilters.Bodies)

    edge_template_input = inputs.addSelectionInput(
        'edge_template_input',
        'Template Edge',
        'Select a body to serve as template geometry at every node.'
    )
    edge_template_input.setSelectionLimits(1, 1)
    edge_template_input.clearSelectionFilter()
    edge_template_input.addSelectionFilter(adsk.core.SelectionFilters.Bodies)

    _node_file_button = inputs.addBoolValueInput(
        'node_file_button_input',
        'Node File',
        False,
        os.path.join(ICON_FOLDER, 'button'),
        False,
    )
    _element_file_button = inputs.addBoolValueInput(
        'element_file_button_input',
        'Element File',
        False,
        os.path.join(ICON_FOLDER, 'button'),
        False,
    )
    _node_file = inputs.addTextBoxCommandInput(
        'node_file_input',
        'Selected Node File',
        'None Selected',
        1,
        True,
    )
    _element_file = inputs.addTextBoxCommandInput(
        'element_file_input',
        'Selected Element File',
        'None Selected',
        1,
        True,
    )

def command_execute(args: adsk.core.CommandEventArgs):
    inputs = args.command.commandInputs
    futil.log(f'{CMD_NAME} Command Execute Event')

    node_template_input = adsk.core.SelectionCommandInput.cast(inputs.itemById('node_template_input'))
    edge_template_input = adsk.core.SelectionCommandInput.cast(inputs.itemById('edge_template_input'))
    node_file_input = adsk.core.TextBoxCommandInput.cast(inputs.itemById('node_file_input')).text
    element_file_input = adsk.core.TextBoxCommandInput.cast(inputs.itemById('element_file_input')).text

    node_file_lines = open(node_file_input).readlines()[1:-1]
    element_file_lines = open(element_file_input).readlines()[1:-1]

    nodes = [
        tuple(map(lambda n: float(n), line.split()[1:]))
        for line in node_file_lines
    ]
    elements = [
        tuple(map(lambda p: int(p) - 1, line.split()[1:-1]))
        for line in element_file_lines
    ]
    edges = list(sorted({
        tuple(sorted(edge))
        for element in elements
        for edge in itertools.combinations(element, 2)
    }))

    node_template_body = adsk.fusion.BRepBody.cast(node_template_input.selection(0).entity)
    edge_template_body = adsk.fusion.BRepBody.cast(edge_template_input.selection(0).entity)

    active_component = adsk.fusion.Design.cast(app.activeProduct).activeComponent

    new_base_feature = active_component.features.baseFeatures.add()
    new_base_feature.name = "TetrahedralMesh"

    new_edges = [get_new_edge(edge_template_body, get_edge_transformation(edge, nodes)) for edge in edges]
    new_nodes = [get_new_node(node_template_body, node) for node in nodes]
    new_bodies = new_nodes + new_edges

    join_bodies_from_array(new_base_feature, new_bodies)

    _new_remove_feature = active_component.features.removeFeatures.add(edge_template_body)
    _new_remove_feature = active_component.features.removeFeatures.add(node_template_body)

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

def get_new_edge(template_body: adsk.fusion.BRepBody, transformation_matrix: adsk.core.Matrix3D):
    new_body = brep_manager.copy(template_body)
    brep_manager.transform(new_body, transformation_matrix)
    return new_body

def get_new_node(template_body: adsk.fusion.BRepBody, node: tuple[float]):
    new_body = brep_manager.copy(template_body)
    transformation_matrix = adsk.core.Matrix3D.create()
    transformation_matrix.setWithArray([
        1.0, 0.0, 0.0, node[0] - 10.0,
        0.0, 1.0, 0.0, node[1],
        0.0, 0.0, 1.0, node[2],
        0.0, 0.0, 0.0, 1.0,
    ])
    brep_manager.transform(new_body, transformation_matrix)
    return new_body

def get_edge_transformation(edge: tuple[int], nodes: list[tuple[float]]):
    raw_edge = (nodes[edge[0]], nodes[edge[1]])
    edge_points = (
        adsk.core.Point3D.create(raw_edge[0][0], raw_edge[0][1], raw_edge[0][2]),
        adsk.core.Point3D.create(raw_edge[1][0], raw_edge[1][1], raw_edge[1][2])
    )
    transformation_matrix = adsk.core.Matrix3D.create()
    transformation_operation = adsk.core.Matrix3D.create()

    transformation_operation.setCell(0, 0, edge_points[0].distanceTo(edge_points[1]) / 10)
    transformation_matrix.transformBy(transformation_operation)

    transformation_operation.setToRotateTo(
        adsk.core.Point3D.create(0.0, 0.0, 0.0).vectorTo(adsk.core.Point3D.create(10.0, 0.0, 0.0)),
        edge_points[0].vectorTo(edge_points[1])
    )
    transformation_matrix.transformBy(transformation_operation)

    transformation_operation.setWithArray([
        1.0, 0.0, 0.0, raw_edge[0][0],
        0.0, 1.0, 0.0, raw_edge[0][1],
        0.0, 0.0, 1.0, raw_edge[0][2],
        0.0, 0.0, 0.0, 1.0,
    ])
    transformation_matrix.transformBy(transformation_operation)

    return transformation_matrix

def add_bodies_from_array(target_feature: adsk.fusion.BaseFeature, bodies: list[adsk.fusion.BRepBody]):
    target_feature.startEdit()
    for body in bodies:
        _res = target_feature.parentComponent.bRepBodies.add(body, target_feature)
    target_feature.finishEdit()

def join_bodies_from_array(target_feature: adsk.fusion.BaseFeature, bodies: list[adsk.fusion.BRepBody]):
    target_feature.startEdit()
    target_body = bodies[0]
    for tool_body in bodies[1:]:
        _res = brep_manager.booleanOperation(target_body, tool_body, adsk.fusion.BooleanTypes.UnionBooleanType)
    target_feature.parentComponent.bRepBodies.add(bodies[0], target_feature)
    target_feature.finishEdit()
