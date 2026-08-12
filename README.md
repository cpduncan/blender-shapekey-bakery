# Blender ShapeKey Bakery

A Blender script that bakes **Geometry Node animations** and **mesh deformations** directly into **Shape Keys**.

Engines like Unity and Unreal cannot natively process Blender's procedural Geometry Nodes. 
This script converts your procedural vertex positions frame by frame into Shape Keys so that you can export these procedural animations in your chosen engine.

<img width="640" height="480" alt="2026-08-11 22-58-48 (online-video-cutter com)" src="https://github.com/user-attachments/assets/874c2c1d-8691-46ff-87f4-bb9fddcbb117" />

---

## 😢 Requirements

* **Constant Vertex Count:** Geometry Nodes **cannot** add or delete vertices/faces. Collapse unwanted verts into the mesh instead of deleting them or else this solution will not work.
* **Active Action:** Select the animation/action you are baking the animation for in the Action Editor / Dope Sheet.

---

## 🪱 Usage

1. Select target object
2. Paste and run the script from Blender's **Scripting** tab

*The original object and node setup can now be safely removed, the mesh you will export is this newly generated mesh with it's baked animation.*
