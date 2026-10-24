@echo off
setlocal
cd /d "%~dp0"
echo ==========================================
echo Build Watermark HUMASSKANSA menjadi EXE
echo ==========================================
py -m pip install --upgrade pip
if errorlevel 1 goto error
py -m pip install -r requirements.txt
if errorlevel 1 goto error
py -m PyInstaller --noconfirm --clean --onefile --console --name Watermark_HUMASSKANSA watermark.py
if errorlevel 1 goto error
echo.
echo BERHASIL! File EXE ada di folder dist\Watermark_HUMASSKANSA.exe
echo Salin EXE ke folder kerja, lalu buat folder foto_input di sebelah EXE.
pause
exit /b 0
:error
echo.
echo GAGAL. Pastikan Python terpasang dan perintah py bisa dijalankan.
pause
exit /b 1
