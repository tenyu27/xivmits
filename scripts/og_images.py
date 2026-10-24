"""Draw the static Open Graph images. Text and layout only: no game art.

Usage: python3 scripts/og_images.py

Pillow is a maintainer dependency for this script, not a site dependency.
The PNGs in apps/web/public/og/ are what the site ships.
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'apps/web/public/og'
FONT = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
FONT_BOLD = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')

# Dark theme tokens from apps/web/src/theme.ts. Hex lives here, in the
# generator, so the site stylesheet never hardcodes a color.
BG = (13, 17, 23)
TEXT = (232, 237, 244)
MUTED = (154, 166, 182)
ACCENT = (96, 165, 250)
WIDTH, HEIGHT = 1200, 630


def font(path, size):
    return ImageFont.truetype(path, size)


def card(eyebrow, title, subtitle):
    image = Image.new('RGB', (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 16, HEIGHT), fill=ACCENT)
    draw.text((72, 150), eyebrow, font=font(FONT_BOLD, 28), fill=ACCENT)
    draw.rectangle((72, 204, 168, 208), fill=ACCENT)
    draw.text((72, 236), title, font=font(FONT_BOLD, 84), fill=TEXT)
    draw.text((72, 360), subtitle, font=font(FONT, 36), fill=MUTED)
    draw.text((72, 540), 'xivmits.com', font=font(FONT, 24), fill=MUTED)
    return image.quantize(colors=16, method=Image.Quantize.MEDIANCUT)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pages = [('site', 'XIVMits', 'Mitigation sheets', 'Fight, role, job, and phase.')]
    for path in sorted((ROOT / 'packages/encounter-data/fights').glob('*/encounter.json')):
        fight = json.loads(path.read_text())
        short = fight.get('shortName') or fight['name']
        pages.append((fight['id'], 'XIVMits', short, fight['name']))
    for name, eyebrow, title, subtitle in pages:
        target = OUT / f'{name}.png'
        card(eyebrow, title, subtitle).save(target, optimize=True)
        print(f'{target.relative_to(ROOT)}  {target.stat().st_size} bytes')


if __name__ == '__main__':
    main()
