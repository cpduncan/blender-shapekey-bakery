import bpy


# ============================================================
# SETTINGS
# ============================================================

SHAPE_KEY_PREFIX = "Frame_"
BAKED_SUFFIX = "_Baked"


# ============================================================
# GET SOURCE OBJECT
# ============================================================

source = bpy.context.active_object

if source is None:
    raise RuntimeError("No object selected.")

if source.type != 'MESH':
    raise RuntimeError("Selected object must be a mesh.")

if source.animation_data is None:
    raise RuntimeError(
        "Selected object has no animation data."
    )

if source.animation_data.action is None:
    raise RuntimeError(
        "Selected object does not have an active Action."
    )

action = source.animation_data.action

start_frame = int(action.frame_range[0])
end_frame = int(action.frame_range[1])

scene = bpy.context.scene
original_frame = scene.frame_current

print("========================================")
print("GEOMETRY NODES → SHAPE KEY BAKE")
print("WITH PARENT/BONE TRANSFORM")
print("========================================")
print("Source:", source.name)
print("Action:", action.name)
print("Frames:", start_frame, "→", end_frame)


# ============================================================
# CHECK GEOMETRY NODES
# ============================================================

gn_modifiers = [
    mod for mod in source.modifiers
    if mod.type == 'NODES'
]

if not gn_modifiers:
    raise RuntimeError(
        "No Geometry Nodes modifier found."
    )

print("Geometry Nodes modifiers:", len(gn_modifiers))


# ============================================================
# SAVE SOURCE PARENT INFORMATION
# ============================================================

source_parent = source.parent
source_parent_type = source.parent_type
source_parent_bone = source.parent_bone

source_matrix_parent_inverse = (
    source.matrix_parent_inverse.copy()
)

source_location = source.location.copy()
source_rotation_mode = source.rotation_mode
source_rotation_euler = source.rotation_euler.copy()
source_rotation_quaternion = source.rotation_quaternion.copy()
source_scale = source.scale.copy()


print("----------------------------------------")
print("Parent:", source_parent.name if source_parent else "None")
print("Parent type:", source_parent_type)

if source_parent_type == 'BONE':
    print("Parent bone:", source_parent_bone)

print("----------------------------------------")


# ============================================================
# EVALUATE FIRST FRAME
# ============================================================

scene.frame_set(start_frame)

bpy.context.view_layer.update()

depsgraph = bpy.context.evaluated_depsgraph_get()

evaluated = source.evaluated_get(depsgraph)


# ============================================================
# CREATE MESH FROM GN RESULT
# ============================================================

baked_mesh = bpy.data.meshes.new_from_object(
    evaluated,
    depsgraph=depsgraph
)

if baked_mesh is None:
    raise RuntimeError(
        "Could not create mesh from Geometry Nodes result."
    )

vertex_count = len(baked_mesh.vertices)

print("GN vertex count:", vertex_count)


# ============================================================
# CREATE BAKED OBJECT
# ============================================================

baked = bpy.data.objects.new(
    source.name + BAKED_SUFFIX,
    baked_mesh
)

bpy.context.collection.objects.link(baked)


# ============================================================
# COPY PARENT RELATIONSHIP
# ============================================================

baked.parent = source_parent

baked.parent_type = source_parent_type

if source_parent_type == 'BONE':
    baked.parent_bone = source_parent_bone


# ============================================================
# COPY PARENT INVERSE
# ============================================================

baked.matrix_parent_inverse = (
    source_matrix_parent_inverse.copy()
)


# ============================================================
# COPY LOCAL TRANSFORM
# ============================================================

baked.location = source_location.copy()

baked.rotation_mode = source_rotation_mode

if source_rotation_mode == 'QUATERNION':

    baked.rotation_quaternion = (
        source_rotation_quaternion.copy()
    )

elif source_rotation_mode == 'AXIS_ANGLE':

    baked.rotation_axis_angle = (
        source.rotation_axis_angle[:]
    )

else:

    baked.rotation_euler = (
        source_rotation_euler.copy()
    )

baked.scale = source_scale.copy()


# ============================================================
# CREATE BASIS SHAPE KEY
# ============================================================

basis = baked.shape_key_add(
    name="Basis"
)

basis.relative_key = basis


# ============================================================
# BAKE EVERY FRAME
# ============================================================

baked_keys = []

total_frames = end_frame - start_frame + 1

print("----------------------------------------")
print("BAKING")
print("----------------------------------------")

for index, frame in enumerate(
    range(start_frame, end_frame + 1)
):

    print(
        f"Baking frame {frame} "
        f"({index + 1}/{total_frames})"
    )

    # Set animation frame
    scene.frame_set(frame)

    bpy.context.view_layer.update()

    depsgraph.update()

    # Get evaluated source
    evaluated = source.evaluated_get(
        depsgraph
    )

    # Get evaluated mesh
    mesh = evaluated.to_mesh(
        preserve_all_data_layers=True,
        depsgraph=depsgraph
    )

    try:

        # ----------------------------------------------------
        # CHECK TOPOLOGY
        # ----------------------------------------------------

        current_vertex_count = len(mesh.vertices)

        if current_vertex_count != vertex_count:

            raise RuntimeError(
                f"\nTopology changed at frame {frame}!\n"
                f"Expected vertices: {vertex_count}\n"
                f"Actual vertices:   {current_vertex_count}\n"
            )


        # ----------------------------------------------------
        # CREATE SHAPE KEY
        # ----------------------------------------------------

        key_name = (
            f"{SHAPE_KEY_PREFIX}{frame:04d}"
        )

        key = baked.shape_key_add(
            name=key_name
        )


        # ----------------------------------------------------
        # COPY VERTEX POSITIONS
        # ----------------------------------------------------

        for i, vertex in enumerate(mesh.vertices):

            key.data[i].co = vertex.co


        baked_keys.append(key)


    finally:

        evaluated.to_mesh_clear()


# ============================================================
# CREATE SHAPE KEY ANIMATION
# ============================================================

print("----------------------------------------")
print("CREATING SHAPE KEY ANIMATION")
print("----------------------------------------")

shape_keys = baked.data.shape_keys

for key in baked_keys:

    key.value = 0.0


for index, key in enumerate(baked_keys):

    frame = start_frame + index


    # --------------------------------------------------------
    # OFF BEFORE THIS FRAME
    # --------------------------------------------------------

    if frame > start_frame:

        key.value = 0.0

        key.keyframe_insert(
            data_path="value",
            frame=frame - 1
        )


    # --------------------------------------------------------
    # ON AT THIS FRAME
    # --------------------------------------------------------

    key.value = 1.0

    key.keyframe_insert(
        data_path="value",
        frame=frame
    )


    # --------------------------------------------------------
    # OFF AT NEXT FRAME
    # --------------------------------------------------------

    if frame < end_frame:

        key.value = 0.0

        key.keyframe_insert(
            data_path="value",
            frame=frame + 1
        )


# ============================================================
# SELECT BAKED OBJECT
# ============================================================

bpy.ops.object.select_all(
    action='DESELECT'
)

baked.select_set(True)

bpy.context.view_layer.objects.active = baked


# ============================================================
# RESTORE ORIGINAL FRAME
# ============================================================

scene.frame_set(original_frame)

bpy.context.view_layer.update()


# ============================================================
# DONE
# ============================================================

print("")
print("========================================")
print("BAKE COMPLETE")
print("========================================")
print("Original object:", source.name)
print("Baked object:   ", baked.name)
print("Vertices:       ", vertex_count)
print("Shape keys:     ", len(baked_keys))
print("Frames:          ", start_frame, "→", end_frame)
print("Parent:         ",
      source_parent.name if source_parent else "None")
print("Parent type:    ", source_parent_type)

if source_parent_type == 'BONE':
    print("Parent bone:    ", source_parent_bone)

print("========================================")
