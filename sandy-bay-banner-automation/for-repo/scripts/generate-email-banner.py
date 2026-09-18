#!/usr/bin/env python3
"""
Regenerates images/email-banner.png from data/caravans.json + images/logo.png.
Run from the repo root: python3 scripts/generate-email-banner.py

Designed to be triggered automatically by the GitHub Action whenever
AI Ray pushes an update to data/caravans.json, so the banner used in
the Gmail signature (loaded via its stable URL, not uploaded as a file)
always reflects whatever is currently for sale.
"""
import json
import os
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "data", "caravans.json")
LOGO_PATH = os.path.join(ROOT, "images", "logo.png")
OUT_PATH = os.path.join(ROOT, "images", "email-banner.png")
SITE_URL = "sandybaycaravanpark.co.uk"

NAVY = (22, 38, 46)
NAVY_DEEP = (13, 26, 32)
FOAM = (243, 237, 224)
GORSE = (224, 163, 57)

W = 640
HEADER_H = 58
PHOTO_Y = 70
PHOTO_H = 130
CAP_Y = PHOTO_H + PHOTO_Y + 4
FOOTER_H = 28
H = CAP_Y + 20 + FOOTER_H

F_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

def find_font(size, bold=True):
    candidates = [
        F_BOLD,
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()

def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, size[0]-1, size[1]-1], radius=radius, fill=255)
    return m

def money(n):
    return f"£{n:,.0f}"

def main():
    with open(DATA_PATH) as f:
        data = json.load(f)
    caravans = [c for c in data.get("caravans", []) if c.get("status") == "for-sale"]
    featured = caravans[:3]

    canvas = Image.new("RGB", (W, H), FOAM)
    draw = ImageDraw.Draw(canvas)

    # Header
    draw.rectangle([0, 0, W, HEADER_H], fill=NAVY)
    if os.path.exists(LOGO_PATH):
        logo = Image.open(LOGO_PATH).convert("RGBA")
        logo_h = 44
        logo_w = int(logo.width * (logo_h / logo.height))
        logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
        canvas.paste(logo, (14, (HEADER_H - logo_h)//2), logo)

    headline = "CARAVANS FOR SALE" if featured else "SANDY BAY CARAVAN PARK"
    f_headline = find_font(21)
    bbox = draw.textbbox((0, 0), headline, font=f_headline)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    draw.text((W - 20 - tw, (HEADER_H - th)//2 - bbox[1]), headline, font=f_headline, fill=GORSE)

    if featured:
        n = len(featured)
        margin = 25
        gap = 15
        photo_w = (W - 2*margin - (n-1)*gap) // n
        f_name = find_font(12)

        x = margin
        for c in featured:
            photos = c.get("photos") or []
            img = None
            if photos:
                p = os.path.join(ROOT, photos[0])
                if os.path.exists(p):
                    img = Image.open(p).convert("RGB")
            if img is None:
                img = Image.new("RGB", (photo_w, PHOTO_H), (200, 200, 200))

            im_fit = ImageOps.fit(img, (photo_w, PHOTO_H), method=Image.LANCZOS, centering=(0.5, 0.42))
            mask = rounded_mask((photo_w, PHOTO_H), 8)
            canvas.paste(im_fit, (x, PHOTO_Y), mask)
            draw.rounded_rectangle([x, PHOTO_Y, x+photo_w-1, PHOTO_Y+PHOTO_H-1], radius=8, outline=NAVY, width=1)

            name_txt = f"{c.get('name','Caravan')}  ·  "
            price_txt = money(c.get("price", 0))
            nb = draw.textbbox((0, 0), name_txt, font=f_name)
            nw = nb[2]-nb[0]
            full_w = nw + draw.textbbox((0, 0), price_txt, font=f_name)[2]
            start_x = x + (photo_w - full_w)//2
            draw.text((start_x, CAP_Y), name_txt, font=f_name, fill=NAVY)
            draw.text((start_x + nw, CAP_Y), price_txt, font=f_name, fill=(180, 120, 20))

            x += photo_w + gap
    else:
        f_msg = find_font(15)
        msg = "New arrivals coming soon — check back shortly"
        bbox = draw.textbbox((0, 0), msg, font=f_msg)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        draw.text(((W-tw)//2, PHOTO_Y + 40), msg, font=f_msg, fill=NAVY)

    # Footer CTA
    footer_y = H - FOOTER_H
    draw.rectangle([0, footer_y, W, H], fill=GORSE)
    if featured:
        cta = f"VIEW ALL CARAVANS FOR SALE  —  {SITE_URL}/#for-sale"
    else:
        cta = f"{SITE_URL}  —  get in touch about upcoming stock"
    f_cta = find_font(13)
    bbox = draw.textbbox((0, 0), cta, font=f_cta)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    draw.text(((W-tw)//2, footer_y + (FOOTER_H-th)//2 - bbox[1]), cta, font=f_cta, fill=NAVY_DEEP)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    canvas.save(OUT_PATH, "PNG", optimize=True)
    print(f"Wrote {OUT_PATH} ({len(featured)} caravans featured)")

if __name__ == "__main__":
    main()
