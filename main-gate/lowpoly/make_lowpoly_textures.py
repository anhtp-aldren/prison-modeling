"""Make 512 px, reduced-palette color textures from the main gate maps."""
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / '3d' / 'textures'
OUT = HERE / 'textures'
OUT.mkdir(exist_ok=True)

for style in ('steel', 'edge', 'door', 'panel', 'yellow', 'wall_trim'):
    source = Image.open(SOURCE / f'{style}_basecolor.png').convert('RGB')
    small = source.resize((512, 512), Image.Resampling.LANCZOS)
    colors = 48 if style in ('steel', 'edge', 'door', 'wall_trim') else 24
    small = small.quantize(colors=colors, method=Image.Quantize.MEDIANCUT).convert('RGB')
    small.save(OUT / f'{style}_basecolor.png', optimize=True)
    print(style, small.size, colors, 'colors')
