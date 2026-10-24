from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps

# =========================
# PENGATURAN WATERMARK
# =========================
BASE_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
FOLDER_INPUT = BASE_DIR / "foto_input"
FOLDER_OUTPUT = BASE_DIR / "foto_hasil"
FILE_LOGO = BASE_DIR / "logo.png"

TEKS_WATERMARK = "HUMASSMKN1STABAT"
OPACITY = 51                  # 20% dari 255
LOGO_WIDTH_RATIO = 0.08       # logo lebih kecil: 8% lebar foto
TEXT_SIZE = 10                # ukuran font sesuai permintaan
GAP_RATIO = 0.008             # jarak vertikal logo ke tulisan
SHADOW = False
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def load_font(size: int):
    """Gunakan Anton jika file font tersedia; selain itu coba font umum."""
    candidates = [
        BASE_DIR / "Anton-Regular.ttf",
        Path("Anton-Regular.ttf"),
        Path("C:/Windows/Fonts/Anton-Regular.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("DejaVuSans-Bold.ttf"),
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(str(candidate), size)
        except OSError:
            continue
    print("[PERINGATAN] Font Anton tidak ditemukan. Menggunakan font bawaan.")
    return ImageFont.load_default()


def load_logo(path: Path):
    """Muat logo dengan transparansi jika file logo tersedia."""
    if not path.is_file():
        print(f"[PERINGATAN] Logo tidak ditemukan: {path}. Watermark teks saja digunakan.")
        return None

    try:
        logo = Image.open(path).convert("RGBA")
        bbox = logo.getchannel("A").getbbox()
        if bbox:
            logo = logo.crop(bbox)
        return logo
    except Exception as exc:
        print(f"[PERINGATAN] Logo gagal dibaca ({exc}). Watermark teks saja digunakan.")
        return None


def add_watermark(image_path: Path, output_path: Path, logo_original):
    """Tambahkan logo di atas teks, sebagai satu kelompok di tengah bawah foto."""
    with Image.open(image_path) as source:
        photo = ImageOps.exif_transpose(source).convert("RGBA")

    width, height = photo.size
    short_side = min(width, height)

    logo = None
    logo_w = logo_h = 0
    if logo_original is not None:
        target_logo_w = max(1, int(width * LOGO_WIDTH_RATIO))
        scale = target_logo_w / logo_original.width
        target_logo_h = max(1, int(logo_original.height * scale))

        # Batasi tinggi logo agar tidak terlalu besar pada foto portrait.
        max_logo_h = max(1, int(height * 0.15))
        if target_logo_h > max_logo_h:
            scale = max_logo_h / logo_original.height
            target_logo_w = max(1, int(logo_original.width * scale))
            target_logo_h = max_logo_h

        logo = logo_original.resize(
            (target_logo_w, target_logo_h), Image.Resampling.LANCZOS
        )
        alpha = logo.getchannel("A").point(lambda value: int(value * OPACITY / 255))
        logo.putalpha(alpha)
        logo_w, logo_h = logo.size

    font = load_font(TEXT_SIZE)
    text_bbox = font.getbbox(TEKS_WATERMARK)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]

    # Logo berada tepat di atas tulisan; kelompok tetap di tengah bawah.
    gap = max(1, int(short_side * GAP_RATIO)) if logo else 0
    group_h = logo_h + gap + text_h if logo else text_h
    margin_bottom = int(height * 0.05)
    start_y = height - group_h - margin_bottom

    layer = Image.new("RGBA", photo.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    if logo:
        logo_x = (width - logo_w) // 2
        logo_y = start_y
        layer.alpha_composite(logo, (logo_x, logo_y))
        text_y = logo_y + logo_h + gap - text_bbox[1]
    else:
        text_y = start_y - text_bbox[1]

    text_x = (width - text_w) // 2 - text_bbox[0]
    draw.text(
        (text_x, text_y),
        TEKS_WATERMARK,
        font=font,
        fill=(255, 255, 255, OPACITY),
        stroke_width=0,
    )

    result = Image.alpha_composite(photo, layer)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = output_path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        result.convert("RGB").save(output_path, quality=95, optimize=True)
    elif suffix == ".webp":
        result.save(output_path, quality=95, method=6)
    else:
        result.save(output_path)

    print(f"[OK] {image_path.name} -> {output_path}")


def main():
    if not FOLDER_INPUT.is_dir():
        print(f"Folder input tidak ditemukan: {FOLDER_INPUT.resolve()}")
        print("Buat folder 'foto_input' di samping program lalu masukkan foto-foto ke sana.")
        return

    FOLDER_OUTPUT.mkdir(parents=True, exist_ok=True)
    logo = load_logo(FILE_LOGO)

    files = sorted(
        path for path in FOLDER_INPUT.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not files:
        print(f"Tidak ada foto JPG, JPEG, PNG, atau WebP di {FOLDER_INPUT.resolve()}")
        return

    success = 0
    failed = 0
    for image_path in files:
        output_path = FOLDER_OUTPUT / f"{image_path.stem}_watermark{image_path.suffix.lower()}"
        try:
            add_watermark(image_path, output_path, logo)
            success += 1
        except Exception as exc:
            print(f"[GAGAL] {image_path.name}: {exc}")
            failed += 1

    print("\n=== SELESAI ===")
    print(f"Berhasil: {success}")
    print(f"Gagal:    {failed}")
    print(f"Hasil:    {FOLDER_OUTPUT.resolve()}")


if __name__ == "__main__":
    main()
