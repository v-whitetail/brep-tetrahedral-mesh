import adsk.core, adsk.fusion
import os
from math import sqrt
from ...lib import fusionAddInUtils as futil
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface

CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_unit_tetrahedron'
CMD_NAME = 'Unit Tetrahedron'
CMD_Description = ('Creates a unit tetrahedron. A unit tetrahedron is a regular icosahedron whose points'
                   'may all be found on the surface of a sphere with a radius of 1')
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
    new_base_feature.name = "UnitTetrahedron"
    new_base_feature.startEdit()

    new_body_definition = defineUnitTetrahedron(adsk.fusion.BRepBodyDefinition.create())
    new_body = new_body_definition.createBody()

    active_component.bRepBodies.add(new_body, new_base_feature)
    new_base_feature.finishEdit()

def command_destroy(args: adsk.core.CommandEventArgs):
    global local_handlers
    local_handlers = []
    futil.log(f'{CMD_NAME} Command Destroy Event')

def defineUnitTetrahedron(brep_definition: adsk.fusion.BRepBodyDefinition):
    raw_tetrahedron = [
        sqrt(8 / 9), -sqrt(2 / 9), -sqrt(2 / 9), 0.0,
        0.0, -sqrt(2 / 3), sqrt(2 / 3), 0.0,
        -1 / 3, -1 / 3, -1 / 3, 1.0,
        1.0, 1.0, 1.0, 1.0,
    ]
    points = [
        adsk.core.Point3D.create(raw_tetrahedron[0], raw_tetrahedron[4], raw_tetrahedron[8]),
        adsk.core.Point3D.create(raw_tetrahedron[1], raw_tetrahedron[5], raw_tetrahedron[9]),
        adsk.core.Point3D.create(raw_tetrahedron[2], raw_tetrahedron[6], raw_tetrahedron[10]),
        adsk.core.Point3D.create(raw_tetrahedron[3], raw_tetrahedron[7], raw_tetrahedron[11]),
    ]
    vertices = [
        brep_definition.createVertexDefinition(points[0]),
        brep_definition.createVertexDefinition(points[1]),
        brep_definition.createVertexDefinition(points[2]),
        brep_definition.createVertexDefinition(points[3]),
    ]
    curves = [
        adsk.core.Line3D.create(points[0], points[1]),
        adsk.core.Line3D.create(points[1], points[2]),
        adsk.core.Line3D.create(points[2], points[0]),
        adsk.core.Line3D.create(points[0], points[3]),
        adsk.core.Line3D.create(points[1], points[3]),
        adsk.core.Line3D.create(points[2], points[3]),
    ]
    edges = [
        brep_definition.createEdgeDefinitionByCurve(vertices[0], vertices[1], curves[0]),
        brep_definition.createEdgeDefinitionByCurve(vertices[1], vertices[2], curves[1]),
        brep_definition.createEdgeDefinitionByCurve(vertices[2], vertices[0], curves[2]),
        brep_definition.createEdgeDefinitionByCurve(vertices[0], vertices[3], curves[3]),
        brep_definition.createEdgeDefinitionByCurve(vertices[1], vertices[3], curves[4]),
        brep_definition.createEdgeDefinitionByCurve(vertices[2], vertices[3], curves[5]),
    ]
    normals = [
        points[0].vectorTo(points[1]).crossProduct(points[1].vectorTo(points[3])),
        points[1].vectorTo(points[2]).crossProduct(points[2].vectorTo(points[3])),
        points[2].vectorTo(points[0]).crossProduct(points[0].vectorTo(points[3])),
        points[0].vectorTo(points[1]).crossProduct(points[1].vectorTo(points[2])),
    ]
    surfaces = [
        adsk.core.Plane.create(points[0], normals[0]),
        adsk.core.Plane.create(points[1], normals[1]),
        adsk.core.Plane.create(points[2], normals[2]),
        adsk.core.Plane.create(points[0], normals[3]),
    ]
    lump = brep_definition.lumpDefinitions.add()
    shell = lump.shellDefinitions.add()
    faces = [
        shell.faceDefinitions.add(surfaces[0], False),
        shell.faceDefinitions.add(surfaces[1], False),
        shell.faceDefinitions.add(surfaces[2], False),
        shell.faceDefinitions.add(surfaces[3], True),
    ]
    loops = [
        faces[0].loopDefinitions.add(),
        faces[1].loopDefinitions.add(),
        faces[2].loopDefinitions.add(),
        faces[3].loopDefinitions.add(),
    ]
    co_edges = [
        loops[0].bRepCoEdgeDefinitions.add(edges[0], False),
        loops[0].bRepCoEdgeDefinitions.add(edges[4], False),
        loops[0].bRepCoEdgeDefinitions.add(edges[3], True),
        loops[1].bRepCoEdgeDefinitions.add(edges[1], False),
        loops[1].bRepCoEdgeDefinitions.add(edges[5], False),
        loops[1].bRepCoEdgeDefinitions.add(edges[4], True),
        loops[2].bRepCoEdgeDefinitions.add(edges[2], False),
        loops[2].bRepCoEdgeDefinitions.add(edges[3], False),
        loops[2].bRepCoEdgeDefinitions.add(edges[5], True),
        loops[3].bRepCoEdgeDefinitions.add(edges[0], False),
        loops[3].bRepCoEdgeDefinitions.add(edges[1], False),
        loops[3].bRepCoEdgeDefinitions.add(edges[2], False),
    ]
    return brep_definition
