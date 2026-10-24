from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps

# =========================
# PENGATURAN
# =========================
BASE_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
FOLDER_INPUT = BASE_DIR / "foto_input"
FOLDER_OUTPUT = BASE_DIR / "foto_hasil"
FILE_LOGO = BASE_DIR / "logo.png"

TEKS_WATERMARK = "© HUMASSKANSA"
OPACITY = 150                 # 0 = tidak terlihat, 255 = solid
LOGO_WIDTH_RATIO = 0.12       # lebar logo relatif terhadap lebar foto
TEXT_SIZE_RATIO = 0.035       # ukuran teks relatif terhadap lebar foto
GAP_RATIO = 0.025             # jarak antara logo dan teks
SHADOW = True
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def load_font(size: int):
    """Coba gunakan font yang umum tersedia, lalu fallback."""
    candidates = [
        Path("arial.ttf"),
        Path("DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(str(candidate), size)
        except OSError:
            continue
    return ImageFont.load_default()


def load_logo(path: Path):
    """Muat logo RGBA jika tersedia; jika tidak, lanjut tanpa logo."""
    if not path.is_file():
        print(f"[PERINGATAN] Logo tidak ditemukan: {path}. Watermark teks saja digunakan.")
        return None

    try:
        logo = Image.open(path).convert("RGBA")
        # Pangkas area transparan di sekeliling logo jika ada
        alpha = logo.getchannel("A")
        bbox = alpha.getbbox()
        if bbox:
            logo = logo.crop(bbox)
        return logo
    except Exception as exc:
        print(f"[PERINGATAN] Logo gagal dibaca ({exc}). Watermark teks saja digunakan.")
        return None


def add_watermark(image_path: Path, output_path: Path, logo_original):
    """Tambahkan logo dan teks dalam satu kelompok di tengah foto."""
    with Image.open(image_path) as source:
        photo = ImageOps.exif_transpose(source).convert("RGBA")

    width, height = photo.size
    short_side = min(width, height)

    # Ukuran logo dan teks disesuaikan dengan resolusi foto
    logo = None
    logo_w = logo_h = 0
    if logo_original is not None:
        target_logo_w = max(1, int(width * LOGO_WIDTH_RATIO))
        scale = target_logo_w / logo_original.width
        target_logo_h = max(1, int(logo_original.height * scale))
        # Cegah logo menjadi terlalu tinggi pada foto portrait
        max_logo_h = max(1, int(height * 0.25))
        if target_logo_h > max_logo_h:
            scale = max_logo_h / logo_original.height
            target_logo_w = max(1, int(logo_original.width * scale))
            target_logo_h = max_logo_h
        logo = logo_original.resize((target_logo_w, target_logo_h), Image.Resampling.LANCZOS)
        logo_w, logo_h = logo.size

        # Terapkan transparansi pada logo
        alpha = logo.getchannel("A").point(lambda value: int(value * OPACITY / 255))
        logo.putalpha(alpha)

    font_size = max(12, int(width * TEXT_SIZE_RATIO))
    font = load_font(font_size)
    text_bbox = font.getbbox(TEKS_WATERMARK)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]

    gap = max(6, int(short_side * GAP_RATIO)) if logo else 0
    group_w = logo_w + (gap if logo else 0) + text_w
    group_h = max(logo_h, text_h)

    # Seluruh kelompok logo + teks tepat di tengah bawah foto
    margin_bottom = int(height * 0.05)

    start_x = (width - group_w) // 2
    start_y = height - group_h - margin_bottom

    layer = Image.new("RGBA", photo.size, (0, 0, 0, 0))

    if logo:
        logo_y = start_y + (group_h - logo_h) // 2
        layer.alpha_composite(logo, (start_x, logo_y))

    text_x = start_x + logo_w + (gap if logo else 0)
    # Koreksi offset font agar posisi visual teks terpusat vertikal
    text_y = start_y + (group_h - text_h) // 2 - text_bbox[1]
    draw = ImageDraw.Draw(layer)

    text_alpha = max(0, min(255, OPACITY))
    if SHADOW:
        draw.text(
            (text_x + 2, text_y + 2),
            TEKS_WATERMARK,
            font=font,
            fill=(0, 0, 0, text_alpha),
            stroke_width=0,
        )

    draw.text(
        (text_x, text_y),
        TEKS_WATERMARK,
        font=font,
        fill=(255, 255, 255, text_alpha),
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
        print("Buat folder 'foto_input' lalu masukkan foto-foto yang ingin diproses.")
        return

    FOLDER_OUTPUT.mkdir(parents=True, exist_ok=True)
    logo = load_logo(FILE_LOGO)

    # Hanya memproses file foto di folder input, bukan subfolder.
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
