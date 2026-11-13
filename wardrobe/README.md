# Wardrobe

Editable Blender model based on `wardrobe-views.png`.

- `wardrobe.blend` — open-door scene with dark steel, two hanging numbered prison jumpsuits, a clear top, lighting, and a render camera.
- `preview.png` — three-quarter render.
- `preview_front.png`, `preview_back.png`, `preview_side.png`, `preview_top.png` — orthographic comparison views.
- `build_wardrobe.py` — source script to recreate the model and renders in Blender 5.x.
- `closed/wardrobe_closed.blend` — separate dark steel version with closed doors, solid front backing, and no clothing or red rust tone.

The open cabinet is approximately 0.91 m wide, 0.59 m deep, and 1.75 m high. Front faces negative Y. The two doors pivot from empty objects named `Left door | hinge pivot` and `Right door | hinge pivot`; rotate those to pose them. The source image has no stated dimensions, so these dimensions and hidden surfaces are inferred.

Rebuild in PowerShell:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --python build_wardrobe.py
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --background --python build_wardrobe.py -- --closed
```
