# Pillar 01

Pillar using a texture derived directly from its approved 2D front image.

- Dimensions: 1.5 m wide × 6 m high × 1.5 m deep.
- Main shaft: 1.25 m square. The cap and base project 0.125 m beyond each side.
- Origin: bottom center. Front faces negative Y.
- Two 512 × 512 PNG textures are cropped directly from `../2d/front.png`: one holds the two continuous halves of the shaft, and one holds the cap and base. They are darkened and sharpened for the mobile model, then packed into the Blender file. The shaft halves meet at the same source-image row without a visible seam.

Files: `pillar_01.blend`, `pillar_01.glb`, `pillar_01_fbx.zip`, and `preview.png`. The FBX package includes external copies of both textures as well as embedded textures.

Rebuild:

```powershell
python make_textures.py
blender --background --python build_pillar.py
```
