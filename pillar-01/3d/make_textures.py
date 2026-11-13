"""Make two compact, sharp textures directly from the pillar's 2D image."""

from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter


root = Path(__file__).resolve().parent
source = root.parent / '2d' / 'front.png'
texture_dir = root / 'textures'
texture_dir.mkdir(parents=True, exist_ok=True)


def make_atlas(reference, regions, filename):
    atlas = Image.new('RGB', (512, 512), (40, 39, 37))
    for source_rect, atlas_rect in regions.values():
        left, top, right, bottom = atlas_rect
        patch = reference.crop(source_rect)
        patch = patch.resize((right - left, bottom - top), Image.Resampling.LANCZOS)
        patch = ImageEnhance.Brightness(patch).enhance(0.70)
        patch = ImageEnhance.Contrast(patch).enhance(1.10)
        patch = patch.filter(ImageFilter.UnsharpMask(radius=0.8, percent=95, threshold=3))
        atlas.paste(patch, (left, top))
    target = texture_dir / filename
    atlas.save(target, 'PNG', optimize=True)
    print(target)


with Image.open(source) as image:
    image = image.convert('RGB')
    make_atlas(image, {
        'shaft_upper': ((190, 287, 578, 999), (16, 16, 240, 432)),
        'shaft_lower': ((190, 999, 578, 1710), (272, 16, 496, 432)),
    }, 'pillar_shaft.png')
    make_atlas(image, {
        'cap': ((150, 122, 618, 282), (16, 16, 496, 192)),
        'base': ((150, 1716, 618, 1938), (16, 224, 496, 480)),
    }, 'pillar_trim.png')
