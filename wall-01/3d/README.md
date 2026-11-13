# Wall 01

Blender model built from `../2d/front.png`.

- `wall_01.blend` — editable Blender scene containing the textured wall mesh.
- `wall_01.glb` — portable textured glTF binary export.
- `fbx/wall_01.fbx` — FBX export with embedded texture.
- `fbx/textures/front.png` — separate texture copy for importers that need an external file.
- `wall_01_fbx.zip` — FBX and external texture together.
- `fbx_mobile/wall_01_mobile.fbx` — mobile FBX with an embedded 768 × 512 JPEG texture.
- `fbx_mobile/textures/front_mobile.jpg` — separate mobile texture copy.
- `wall_01_mobile_fbx.zip` — mobile FBX and texture together.
- `preview.png` — rendered three-quarter view.
- `preview_front.png` — straight-on view of the textured front.
- `preview_back.png` — three-quarter view of the textured rear.
- `preview_side.png` — side view of the cap and plinth depth.
- `build_wall.py` — source used to build and export the model.
- `export_fbx.py` — exports the saved Blender model to the FBX package.

Dimensions: 3 m wide × 6 m high × 1 m thick. The front faces negative Y and the origin is at the bottom center. The top steel cap and bottom plinth project beyond the brick on both front and back. Front, back, sides, top, and bottom are UV mapped to the packed source image. Blender opens in Material Preview.

Rebuild with Blender 5.x:

```powershell
blender --background --python build_wall.py
```

Export the FBX from the saved Blender project:

```powershell
blender --background wall_01.blend --python export_fbx.py
```
