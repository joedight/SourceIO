import math
from pathlib import Path

import bpy

from .bpy_utilities.utils import get_or_create_collection, get_new_unique_collection
from .source1.mdl.import_mdl import import_model, import_materials, put_into_collections
from .source2.resouce_types.valve_model import ValveCompiledModel
from .source_shared.content_manager import ContentManager
from .utilities.path_utilities import backwalk_file_resolver, find_vtx_cm


def get_parent(collection):
    for pcoll in bpy.data.collections:
        if collection.name in pcoll.children:
            return pcoll
    return bpy.context.scene.collection


class LoadEntity_OT_operator(bpy.types.Operator):
    bl_idname = "source_io.load_placeholder"
    bl_label = "Load Entity"
    bl_options = {'UNDO'}

    def execute(self, context):
        content_manager = ContentManager()
        content_manager.deserialize(bpy.context.scene.get('content_manager_data', {}))

        for obj in context.selected_objects:
            print(f'Loading {obj.name}')
            if obj.get("entity_data", None):
                custom_prop_data = obj['entity_data']
                if 'prop_path' not in custom_prop_data:
                    continue
                model_type = Path(custom_prop_data['prop_path']).suffix
                parent = get_parent(obj.users_collection[0])
                collection = get_or_create_collection(custom_prop_data['type'], parent)

                if model_type in ['.vmdl_c', '.vmdl_c']:
                    mld_file = content_manager.find_file(custom_prop_data['prop_path'])
                    if mld_file:
                        skin = custom_prop_data.get('skin', None)
                        model = ValveCompiledModel(mld_file)
                        model.load_mesh(True, parent_collection=collection)
                        for ob in model.objects:  # type:bpy.types.Object
                            ob.location = obj.location
                            ob.rotation_mode = "XYZ"
                            ob.rotation_euler = obj.rotation_euler
                            ob.scale = obj.scale

                            # if skin:
                            #     if str(skin) in ob['skin_groups']:
                            #         skin = str(skin)
                            #         skin_materials = ob['skin_groups'][skin]
                            #         current_materials = ob['skin_groups'][ob['active_skin']]
                            #         print(skin_materials, current_materials)
                            #         for skin_material, current_material in zip(skin_materials, current_materials):
                            #             swap_materials(ob, skin_material[-63:], current_material[-63:])
                            #         ob['active_skin'] = skin
                            #     else:
                            #         print(f'Skin {skin} not found')
                        bpy.data.objects.remove(obj)
                    else:
                        self.report({'INFO'}, f"Model '{custom_prop_data['prop_path']}_c' not found!")
                elif model_type == '.mdl':
                    prop_path = Path(custom_prop_data['prop_path'])
                    mld_file = content_manager.find_file(prop_path)
                    if mld_file:
                        vvd_file = content_manager.find_file(prop_path.with_suffix('.vvd'))
                        vtx_file = find_vtx_cm(prop_path, content_manager)
                        model_container = import_model(mld_file, vvd_file, vtx_file, 1.0, False, True)

                        entity_data_holder = bpy.data.objects.new(model_container.mdl.header.name, None)
                        entity_data_holder['entity_data'] = {}
                        entity_data_holder['entity_data']['entity'] = obj['entity_data']['entity']

                        master_collection = put_into_collections(model_container, prop_path.stem, collection, False)
                        master_collection.objects.link(entity_data_holder)

                        if model_container.armature is not None:
                            armature = model_container.armature
                            armature.rotation_mode = "XYZ"
                            entity_data_holder.parent = armature

                            bpy.context.view_layer.update()
                            armature.parent = obj.parent
                            armature.matrix_world = obj.matrix_world.copy()
                            armature.rotation_euler[2] += math.radians(90)
                        else:
                            if model_container.objects:
                                entity_data_holder.parent = model_container.objects[0]
                            else:
                                entity_data_holder.location = obj.location
                                entity_data_holder.rotation_euler = obj.rotation_euler
                                entity_data_holder.scale = obj.scale
                            for mesh_obj in model_container.objects:
                                mesh_obj.rotation_mode = "XYZ"
                                bpy.context.view_layer.update()
                                mesh_obj.parent = obj.parent
                                mesh_obj.matrix_world = obj.matrix_world.copy()
                        import_materials(model_container.mdl)
                        skin = custom_prop_data.get('skin', None)
                        if skin:
                            for model in model_container.objects:
                                if str(skin) in model['skin_groups']:
                                    skin = str(skin)
                                    skin_materials = model['skin_groups'][skin]
                                    current_materials = model['skin_groups'][model['active_skin']]
                                    print(skin_materials, current_materials)
                                    for skin_material, current_material in zip(skin_materials, current_materials):
                                        swap_materials(model, skin_material[-63:], current_material[-63:])
                                    model['active_skin'] = skin
                                else:
                                    print(f'Skin {skin} not found')

                        bpy.data.objects.remove(obj)
        return {'FINISHED'}


class ChangeSkin_OT_operator(bpy.types.Operator):
    bl_idname = "source_io.select_skin"
    bl_label = "Change skin"
    bl_options = {'UNDO'}

    skin_name: bpy.props.StringProperty(name="skin_name", default="default")

    def execute(self, context):
        obj = context.active_object
        if obj.get('model_type', False):
            model_type = obj['model_type']
            if model_type == 's1':
                self.handle_s1(obj)
            elif model_type == 's2':
                self.handle_s2(obj)
            else:
                self.handle_s2(obj)

        obj['active_skin'] = self.skin_name

        return {'FINISHED'}

    def handle_s1(self, obj):
        skin_materials = obj['skin_groups'][self.skin_name]
        current_materials = obj['skin_groups'][obj['active_skin']]
        for skin_material, current_material in zip(skin_materials, current_materials):
            swap_materials(obj, skin_material[-63:], current_material[-63:])

    def handle_s2(self, obj):
        skin_material = obj['skin_groups'][self.skin_name]
        current_material = obj['skin_groups'][obj['active_skin']]

        mat_name = Path(skin_material).stem
        current_mat_name = Path(current_material).stem
        swap_materials(obj, mat_name, current_mat_name)


def swap_materials(obj, new_material_name, target_name):
    mat = bpy.data.materials.get(new_material_name, None) or bpy.data.materials.new(name=new_material_name)
    print(f'Swapping {target_name} with {new_material_name}')
    for n, obj_mat in enumerate(obj.data.materials):
        print(target_name, obj_mat.name)
        if obj_mat.name == target_name:
            print(obj_mat.name, "->", mat.name)
            obj.data.materials[n] = mat
            break


class UITools:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "SourceIO"


class SourceIOUtils_PT_panel(UITools, bpy.types.Panel):
    bl_label = "SourceIO utils"
    bl_idname = "source_io.utils"

    def draw(self, context):
        pass
        # self.layout.label(text="SourceIO Utils")


class Placeholders_PT_panel(UITools, bpy.types.Panel):
    bl_label = 'Placeholders loading'
    bl_idname = 'source_io.placeholders'
    bl_parent_id = "source_io.utils"

    @classmethod
    def poll(cls, context):
        obj = context.active_object  # type:bpy.types.Object
        return obj and obj.get("entity_data", None) is not None

    def draw(self, context):
        self.layout.label(text="Entity loading")
        obj = context.active_object  # type:bpy.types.Object
        if obj.get("entity_data", None):
            entiry_data = obj['entity_data']
            entity_raw_data = entiry_data.get('entity', {})
            row = self.layout.row()
            row.label(text=f'Total selected entities:')
            row.label(text=str(len([obj for obj in context.selected_objects if 'entity_data' in obj])))
            if entiry_data.get('prop_path', False):
                box = self.layout.box()
                box.operator('source_io.load_placeholder')
            box = self.layout.box()
            for k, v in entity_raw_data.items():
                row = box.row()
                row.label(text=f'{k}:')
                row.label(text=str(v))


class SkinChanger_PT_panel(UITools, bpy.types.Panel):
    bl_label = 'Model skins'
    bl_idname = 'source_io.skin_changer'
    bl_parent_id = "source_io.utils"

    @classmethod
    def poll(cls, context):
        obj = context.active_object  # type:bpy.types.Object
        return obj and obj.get("skin_groups", None) is not None

    def draw(self, context):
        self.layout.label(text="Model skins")
        obj = context.active_object  # type:bpy.types.Object
        if obj.get("skin_groups", None):
            self.layout.label(text="Skins")
            box = self.layout.box()
            for skin, _ in obj['skin_groups'].items():
                row = box.row()
                op = row.operator('source_io.select_skin', text=skin)
                op.skin_name = skin
                if skin == obj['active_skin']:
                    row.enabled = False
