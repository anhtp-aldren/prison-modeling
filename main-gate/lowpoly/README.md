# Low-poly main gate

This version is rebuilt from `../3d/build_gate.py` with simpler primitives. It keeps the same dimensions, three mesh objects (`Main Frame`, `Left Leaf`, `Right Leaf`), and leaf pivots. Small rivets, pin heads, and the top lights are omitted while the larger hinges and handles remain.
The model has 3,948 triangles, about 95% fewer than the detailed version's 77,836.

- `main_gate_lowpoly.blend`: editable Blender model.
- `main_gate_lowpoly.glb`: portable asset with embedded textures.
- `textures/`: six 512×512, reduced-palette color maps, including the wall trim map for `Main Frame`. Roughness and metalness are material constants; there are no normal maps.
- `preview.png`, `preview_front.png`, and `preview_side.png`: visual checks.

Regenerate with Pillow and Blender 5.x:

```powershell
python ..\3d\make_textures.py
python make_lowpoly_textures.py
blender --background --python build_lowpoly.py
```
