import bpy

from math           import pi
from bpy.types      import Operator

from .seut_ot_recreateCollections   import SEUT_OT_RecreateCollections
from .seut_errors                   import errorCollection, isCollectionExcluded
from .seut_utils                    import getParentCollection, toRadians

class SEUT_OT_IconRender(Operator):
    """Handles functionality regarding icon rendering"""
    bl_idname = "scene.icon_render"
    bl_label = "Icon Render"
    bl_options = {'REGISTER', 'UNDO'}


    def execute(self, context):

        scene = context.scene

        if scene.seut.renderToggle == 'on':
            if scene.seut.mirroringToggle == 'on' or scene.seut.mountpointToggle == 'on':
                scene.seut.mirroringToggle = 'off'
                scene.seut.mountpointToggle == 'off'
            result = SEUT_OT_IconRender.renderSetup(self, context)

        elif scene.seut.renderToggle == 'off':
            result = SEUT_OT_IconRender.cleanRenderSetup(self, context)

        return result
    

    def renderSetup(self, context):
        """Sets up render utilities"""

        scene = context.scene
        collections = SEUT_OT_RecreateCollections.getCollections(scene)
        allCurrentViewLayerCollections = context.window.view_layer.layer_collection.children

        if bpy.context.object is not None and bpy.context.object.mode is not 'OBJECT':
            currentMode = bpy.context.object.mode
            bpy.ops.object.mode_set(mode='OBJECT')

        if collections['seut'] is None:
            print("SEUT Warning: Collection 'SEUT (" + scene.name + ")' not found. Action not possible. (002)")
            scene.seut.renderToggle = 'off'
            return {'CANCELLED'}

        isExcluded = isCollectionExcluded(collections['seut'].name, allCurrentViewLayerCollections)
        if isExcluded or isExcluded is None:
            print("SEUT Warning: Collection 'SEUT " + scene.name + "' excluded from view layer. Action not possible. (019)")
            scene.seut.renderToggle = 'off'
            return {'CANCELLED'}
            
        if scene.seut.subtypeId == "":
            scene.seut.subtypeId = scene.name
        tag = ' (' + scene.seut.subtypeId + ')'

        # Create collection if it doesn't exist already
        if not 'Render' + tag in bpy.data.collections:
            collection = bpy.data.collections.new('Render' + tag)
            collections['seut'].children.link(collection)
        else:
            collection = bpy.data.collections['Render' + tag]
            try:
                collections['seut'].children.link(collection)
            except:
                pass


        # Spawn holder empty
        bpy.ops.object.add(type='EMPTY')
        empty = bpy.context.view_layer.objects.active
        empty.name = 'Icon Render'
        empty.empty_display_type = 'SPHERE'
        
        # Spawn camera
        bpy.ops.object.camera_add(location=(6.92579, 7.35889, 4.95831), rotation=(toRadians(63.5593), 0.0, toRadians(136.692)))
        camera = bpy.context.view_layer.objects.active
        camera.parent = empty
        scene.camera = camera
        camera.name = 'ICON'
        camera.data.lens = 70.0

        # Spawn lights
        bpy.ops.object.light_add(type='POINT', location=(15.0, 0.0, 10.0))
        keyLight = bpy.context.view_layer.objects.active
        keyLight.parent = empty
        keyLight.name = 'Key Light'
        keyLight.data.energy = 7500.0
        
        bpy.ops.object.light_add(type='POINT', location=(0.0, 15.0, 0.75))
        fillLight = bpy.context.view_layer.objects.active
        fillLight.parent = empty
        fillLight.name = 'Fill Light'
        fillLight.data.energy = 5000.0
        
        bpy.ops.object.light_add(type='SPOT', location=(-6.72737, -6.72737, -3.07979), rotation=(toRadians(107.937), 0.0, toRadians(-45.0)))
        rimLight = bpy.context.view_layer.objects.active
        rimLight.parent = empty
        rimLight.name = 'Rim Light'
        rimLight.data.energy = 10000.0
        
        parentCollection = getParentCollection(context, empty)
        if parentCollection != collection:
            collection.objects.link(empty)
            collection.objects.link(camera)
            collection.objects.link(keyLight)
            collection.objects.link(fillLight)
            collection.objects.link(rimLight)

            if parentCollection is None:
                scene.collection.objects.unlink(empty)
                scene.collection.objects.unlink(camera)
                scene.collection.objects.unlink(keyLight)
                scene.collection.objects.unlink(fillLight)
                scene.collection.objects.unlink(rimLight)
            else:
                parentCollection.objects.unlink(empty)
                parentCollection.objects.unlink(camera)
                parentCollection.objects.unlink(keyLight)
                parentCollection.objects.unlink(fillLight)
                parentCollection.objects.unlink(rimLight)

        # Spawn compositor node tree

        # Render settings
        scene.render.resolution_x = 128
        scene.render.resolution_y = 128
    
        return {'FINISHED'}


    def cleanRenderSetup(self, context):
        """Clean up render utilities"""

        scene = context.scene

        # If mode is not object mode, export fails horribly.
        if bpy.context.object is not None and bpy.context.object.mode is not 'OBJECT':
            currentMode = bpy.context.object.mode
            bpy.ops.object.mode_set(mode='OBJECT')

        if scene.seut.subtypeId == "":
            scene.seut.subtypeId = scene.name
        tag = ' (' + scene.seut.subtypeId + ')'

        # Delete objects
        for obj in scene.objects:
            if obj is not None and obj.type == 'EMPTY':
                if obj.name == 'Icon Render':
                    for child in obj.children:
                        if child.data is not None:
                            if child.type == 'CAMERA':
                                bpy.data.cameras.remove(child.data)
                            elif child.type == 'LIGHT':
                                bpy.data.lights.remove(child.data)

                    obj.select_set(state=False, view_layer=context.window.view_layer)
                    bpy.data.objects.remove(obj)
    
        # Delete collection
        if 'Render' + tag in bpy.data.collections:
            bpy.data.collections.remove(bpy.data.collections['Render' + tag])
            
        # Reset interaction mode
        try:
            if bpy.context.object is not None and currentMode is not None:
                bpy.ops.object.mode_set(mode=currentMode)
        except:
            pass


        return {'FINISHED'}