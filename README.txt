CARA MEMBUAT EXE (Windows)
==========================

1. Ekstrak folder/proyek ini.
2. Pastikan Python 3.10+ terpasang di Windows dan opsi "Add Python to PATH" diaktifkan.
3. Klik dua kali build_exe.bat.
4. Setelah selesai, EXE berada di:
   dist\Watermark_HUMASSKANSA.exe

CARA MENJALANKAN
================
Letakkan Watermark_HUMASSKANSA.exe di folder kerja. Di lokasi yang sama:
- Buat folder foto_input, lalu masukkan foto JPG/JPEG/PNG/WebP.
- (Opsional) Letakkan logo.png untuk watermark logo.
- Jalankan EXE.
- Foto hasil ada di folder foto_hasil.

Teks watermark saat ini: © HUMASSKANSA
Konfigurasi ukuran, transparansi, dan teks bisa diubah di watermark.py sebelum build.

Catatan:
File EXE Windows tidak bisa dibuat langsung di lingkungan Linux tempat proyek ini disiapkan.
Jalankan build_exe.bat pada komputer Windows untuk menghasilkan EXE.
