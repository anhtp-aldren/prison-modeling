"""Generate PBR texture maps for the main gate (requires Pillow)."""
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageStat
from pathlib import Path
import random

OUT = Path(__file__).resolve().parent / 'textures'
OUT.mkdir(exist_ok=True)
SIZE = 1024

STYLES = {
    'steel': dict(base=(102, 93, 86), rust=(145, 84, 48), wear=(137, 128, 116), rustiness=.69, rough=176, scratch=80),
    'edge': dict(base=(70, 67, 64), rust=(123, 70, 40), wear=(135, 128, 116), rustiness=.70, rough=174, scratch=95),
    'door': dict(base=(67, 64, 62), rust=(108, 69, 43), wear=(105, 100, 92), rustiness=.73, rough=183, scratch=60),
    'panel': dict(base=(7, 8, 9), rust=(29, 26, 24), wear=(34, 35, 35), rustiness=.98, rough=205, scratch=10),
    'yellow': dict(base=(183, 117, 24), rust=(96, 65, 33), wear=(215, 159, 58), rustiness=.74, rough=178, scratch=85),
}
METALLIC = {'steel': 200, 'edge': 210, 'door': 95, 'panel': 0, 'yellow': 70}

def field(rng, cells):
    raw=bytes(rng.randrange(256) for _ in range(cells*cells))
    return Image.frombytes('L',(cells,cells),raw).resize((SIZE,SIZE),Image.Resampling.BICUBIC).tobytes()

def clamp(v):
    return max(0,min(255,int(v)))

for style_name, cfg in STYLES.items():
    rng=random.Random(61879+sum(ord(c) for c in style_name))
    broad=field(rng,14); medium=field(rng,70); fine=field(rng,256)
    drip=Image.new('L',(SIZE,SIZE)); dd=ImageDraw.Draw(drip)
    for _ in range(85 if style_name in ('steel','edge','door') else 18):
        x=rng.randrange(SIZE); y=rng.randrange(SIZE)
        length=rng.randrange(20,190); width=rng.choice((1,1,1,2))
        dd.line((x,y,x+rng.randrange(-4,5),min(SIZE-1,y+length)),fill=rng.randrange(18,75),width=width)
    drip=drip.filter(ImageFilter.GaussianBlur(.9)).tobytes()
    scratches=Image.new('L',(SIZE,SIZE)); sd=ImageDraw.Draw(scratches)
    for _ in range(cfg['scratch']):
        x=rng.randrange(SIZE); y=rng.randrange(SIZE)
        length=rng.randrange(8,120)
        sd.line((x,y,min(SIZE-1,x+length),y+rng.choice((-2,-1,0,1,2))),fill=rng.randrange(60,175),width=1)
    scratches=scratches.tobytes()

    rgb=bytearray(SIZE*SIZE*3); rough=bytearray(SIZE*SIZE); height=bytearray(SIZE*SIZE)
    for i in range(SIZE*SIZE):
        b=broad[i]; m=medium[i]; f=fine[i]
        noise=(.43*b+.37*m+.20*f)/255
        oxide=max(0.0,(noise-cfg['rustiness'])*3.0,drip[i]/255*.24)
        oxide=min(.45,oxide)
        scratch=scratches[i]/255
        grain=((f-127)*.10+(m-127)*.08+(b-127)*.045)
        grain*={'steel':.23,'edge':.20,'door':.18,'panel':.08,'yellow':.28}[style_name]
        for channel in range(3):
            value=cfg['base'][channel]+grain
            value=value*(1-oxide)+cfg['rust'][channel]*oxide
            value=value*(1-scratch*.65)+cfg['wear'][channel]*(scratch*.65)
            rgb[3*i+channel]=clamp(value)
        rough[i]=clamp(cfg['rough']+oxide*32-scratch*18+(f-127)*.035)
        height[i]=clamp(120+(m-127)*.055+(f-127)*.05+oxide*13-scratch*8)

    normals=bytearray(SIZE*SIZE*3)
    for y in range(SIZE):
        row=y*SIZE; prev=((y-1)%SIZE)*SIZE; nxt=((y+1)%SIZE)*SIZE
        for x in range(SIZE):
            i=row+x
            dx=height[row+(x+1)%SIZE]-height[row+(x-1)%SIZE]
            dy=height[nxt+x]-height[prev+x]
            normals[3*i]=clamp(128-dx*1.6)
            normals[3*i+1]=clamp(128+dy*1.6)
            normals[3*i+2]=240
    Image.frombytes('RGB',(SIZE,SIZE),bytes(rgb)).save(OUT / f'{style_name}_basecolor.png',optimize=True)
    Image.frombytes('L',(SIZE,SIZE),bytes(rough)).save(OUT / f'{style_name}_roughness.png',optimize=True)
    orm=bytearray(SIZE*SIZE*3)
    for i,value in enumerate(rough):
        orm[3*i:3*i+3]=bytes((255,value,METALLIC[style_name]))
    Image.frombytes('RGB',(SIZE,SIZE),bytes(orm)).save(OUT / f'{style_name}_orm.png',optimize=True)
    Image.frombytes('RGB',(SIZE,SIZE),bytes(normals)).save(OUT / f'{style_name}_normal.png',optimize=True)
    print(style_name, 'done')

# Match the gate frame to the dark top and bottom trim in wall-01's front map.
wall_source = Path(__file__).resolve().parents[2] / 'wall-01' / '3d' / 'fbx_mobile' / 'textures' / 'front_mobile.jpg'
wall = Image.open(wall_source).convert('RGB')
band_height = 60
top = wall.crop((0, 7, wall.width, 30)).resize((wall.width, band_height), Image.Resampling.BICUBIC)
bottom = wall.crop((0, 450, wall.width, 510))
band = Image.blend(top, bottom, .55)
mean = tuple(round(value) for value in ImageStat.Stat(band).mean)
wall_trim = Image.new('RGB', (SIZE, SIZE), mean)
patch_size = 48
step = 32
feather = 12
mask = Image.new('L', (patch_size, patch_size))
mask_pixels = mask.load()
for y in range(patch_size):
    for x in range(patch_size):
        distance = min(x, y, patch_size-1-x, patch_size-1-y)
        mask_pixels[x,y] = clamp(255*min(1, (distance+1)/feather))
patch_rng = random.Random(8743)
for y in range(-16, SIZE, step):
    for x in range(-16, SIZE, step):
        sx = patch_rng.randrange(0, wall.width-patch_size)
        sy = patch_rng.randrange(0, band_height-patch_size)
        patch = band.crop((sx, sy, sx+patch_size, sy+patch_size))
        wall_trim.paste(patch, (x,y), mask)
wall_trim = wall_trim.filter(ImageFilter.GaussianBlur(.55))
wall_trim.save(OUT / 'wall_trim_basecolor.png', optimize=True)

gray = ImageOps.grayscale(wall_trim).filter(ImageFilter.GaussianBlur(1)).tobytes()
trim_orm = bytearray(SIZE*SIZE*3)
trim_normal = bytearray(SIZE*SIZE*3)
for y in range(SIZE):
    prev = ((y-1) % SIZE)*SIZE
    next_row = ((y+1) % SIZE)*SIZE
    for x in range(SIZE):
        i = y*SIZE+x
        trim_orm[3*i:3*i+3] = bytes((255, 204, 65))
        dx = gray[y*SIZE+(x+1)%SIZE] - gray[y*SIZE+(x-1)%SIZE]
        dy = gray[next_row+x] - gray[prev+x]
        trim_normal[3*i:3*i+3] = bytes((clamp(128-dx*.2), clamp(128+dy*.2), 250))
Image.frombytes('RGB', (SIZE,SIZE), bytes(trim_orm)).save(OUT / 'wall_trim_orm.png', optimize=True)
Image.frombytes('RGB', (SIZE,SIZE), bytes(trim_normal)).save(OUT / 'wall_trim_normal.png', optimize=True)
print('wall_trim done from', wall_source)
