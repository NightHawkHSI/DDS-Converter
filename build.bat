@echo off
setlocal

set SCRIPT=%~dp0DDS.py
set ICON=%~dp0DDSIcon.ico
set BUILD_ROOT=%~dp0Build
set RELEASE_DIR=%BUILD_ROOT%\Release\DDS Converter
set GITHUB_DIR=%BUILD_ROOT%\GitHub
set LOG=%~dp0build_error.log

:: PyInstaller temp dirs — named with underscore prefix so they can NEVER
:: collide with Build\ on a case-insensitive Windows filesystem.
set PYI_WORK=%~dp0_pyi_work
set PYI_DIST=%~dp0_pyi_dist

:: Start fresh log
echo Build started: %DATE% %TIME% > "%LOG%"
echo. >> "%LOG%"

echo.
echo  ========================================
echo   DDS Converter ^— Build Script
echo  ========================================
echo.

:: ── Check Python ─────────────────────────────────────────────────
py --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found on PATH. Aborting.
    echo [FAIL] Python not found on PATH. >> "%LOG%"
    pause & exit /b 1
)
echo [OK] Python found. >> "%LOG%"

:: ── Check / install PyInstaller ──────────────────────────────────
py -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo  [!] PyInstaller not found. Installing...
    py -m pip install pyinstaller >> "%LOG%" 2>&1
    if errorlevel 1 (
        echo  [ERROR] Could not install PyInstaller. Aborting.
        pause & exit /b 1
    )
)
echo [OK] PyInstaller ready. >> "%LOG%"

:: ── Check / install Pillow ───────────────────────────────────────
py -c "import PIL" >nul 2>&1
if errorlevel 1 (
    echo  [!] Pillow not found. Installing...
    py -m pip install Pillow >> "%LOG%" 2>&1
    if errorlevel 1 (
        echo  [ERROR] Could not install Pillow. Aborting.
        pause & exit /b 1
    )
)
echo [OK] Pillow ready. >> "%LOG%"

:: ── Clean everything from a previous run ─────────────────────────
echo  [*] Cleaning previous output...
if exist "%BUILD_ROOT%"  rmdir /s /q "%BUILD_ROOT%"
if exist "%PYI_WORK%"    rmdir /s /q "%PYI_WORK%"
if exist "%PYI_DIST%"    rmdir /s /q "%PYI_DIST%"
if exist "%~dp0DDS.spec"              del /q "%~dp0DDS.spec"
if exist "%~dp0DDS Converter.spec"    del /q "%~dp0DDS Converter.spec"
echo [OK] Clean done. >> "%LOG%"

:: ── Auto-generate DDSIcon.ico if missing ─────────────────────────
if exist "%~dp0DDSIcon.png" (
    if not exist "%~dp0DDSIcon.ico" (
        echo  [*] Generating DDSIcon.ico from DDSIcon.png...
        py -c "from PIL import Image; img=Image.open(r'%~dp0DDSIcon.png').convert('RGBA'); img.save(r'%~dp0DDSIcon.ico', format='ICO', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])"
    )
)

:: ── Run PyInstaller ──────────────────────────────────────────────
echo  [*] Running PyInstaller...
echo [*] Running PyInstaller... >> "%LOG%"

set EXCLUDES=--exclude-module pygame --exclude-module numpy --exclude-module scipy --exclude-module matplotlib --exclude-module pandas

if exist "%ICON%" (
    py -m PyInstaller --noconfirm --onefile --windowed ^
        --icon="%ICON%" ^
        --name="DDS Converter" ^
        --distpath="%PYI_DIST%" ^
        --workpath="%PYI_WORK%" ^
        --collect-all PIL ^
        %EXCLUDES% ^
        "%SCRIPT%"
) else (
    py -m PyInstaller --noconfirm --onefile --windowed ^
        --name="DDS Converter" ^
        --distpath="%PYI_DIST%" ^
        --workpath="%PYI_WORK%" ^
        --collect-all PIL ^
        %EXCLUDES% ^
        "%SCRIPT%"
)

set PYINST_ERR=%ERRORLEVEL%

if not exist "%PYI_DIST%\DDS Converter.exe" (
    echo  [ERROR] PyInstaller failed ^(exit %PYINST_ERR%^) - EXE not produced.
    echo [FAIL] EXE not found after PyInstaller run. >> "%LOG%"
    pause & exit /b 1
)
echo [OK] PyInstaller succeeded. >> "%LOG%"

:: ════════════════════════════════════════════════════════════════
::  RELEASE folder  — zip this for GitHub Releases
:: ════════════════════════════════════════════════════════════════
echo.
echo  [*] Building Release folder...
mkdir "%RELEASE_DIR%"

copy /y "%PYI_DIST%\DDS Converter.exe" "%RELEASE_DIR%\DDS Converter.exe" >> "%LOG%" 2>&1
if errorlevel 1 ( echo [FAIL] Could not copy EXE to Release. >> "%LOG%" )
if exist "%~dp0info.txt"    copy /y "%~dp0info.txt"    "%RELEASE_DIR%\info.txt"    >> "%LOG%" 2>&1
if exist "%~dp0DDSIcon.png" copy /y "%~dp0DDSIcon.png" "%RELEASE_DIR%\DDSIcon.png" >> "%LOG%" 2>&1

(
    echo DDS Converter - by DiccChops
    echo ==============================
    echo.
    echo HOW TO RUN
    echo   Just double-click "DDS Converter.exe"
    echo.
    echo REQUIREMENT - texconv.exe
    echo   texconv.exe is NOT included here ^(Microsoft's tool^).
    echo   Download it and place it in THIS folder:
    echo   https://github.com/microsoft/DirectXTex/releases
    echo.
    echo   Without texconv.exe the app will show an error when
    echo   you try to convert to DDS. PNG/JPG/etc still work.
) > "%RELEASE_DIR%\README.txt"

echo  [*] Release folder ready: %RELEASE_DIR%

:: ════════════════════════════════════════════════════════════════
::  GITHUB folder  — push these files to the repo
:: ════════════════════════════════════════════════════════════════
echo.
echo  [*] Building GitHub folder...
mkdir "%GITHUB_DIR%"

copy /y "%~dp0DDS.py"    "%GITHUB_DIR%\DDS.py"    >> "%LOG%" 2>&1
copy /y "%~dp0build.bat" "%GITHUB_DIR%\build.bat" >> "%LOG%" 2>&1
if exist "%~dp0info.txt"    copy /y "%~dp0info.txt"    "%GITHUB_DIR%\info.txt"    >> "%LOG%" 2>&1
if exist "%~dp0DDSIcon.png" copy /y "%~dp0DDSIcon.png" "%GITHUB_DIR%\DDSIcon.png" >> "%LOG%" 2>&1
if exist "%~dp0DDSIcon.ico" copy /y "%~dp0DDSIcon.ico" "%GITHUB_DIR%\DDSIcon.ico" >> "%LOG%" 2>&1
if exist "%~dp0README.md"   copy /y "%~dp0README.md"   "%GITHUB_DIR%\README.md"   >> "%LOG%" 2>&1
echo [OK] GitHub files copied. >> "%LOG%"

echo  [*] GitHub folder ready: %GITHUB_DIR%

:: ── Clean up PyInstaller temp folders only (NOT Build\) ──────────
echo.
echo  [*] Cleaning up PyInstaller temp files...
rmdir /s /q "%PYI_WORK%"
rmdir /s /q "%PYI_DIST%"
if exist "%~dp0DDS Converter.spec" del /q "%~dp0DDS Converter.spec" 2>nul
echo [OK] Cleanup done. >> "%LOG%"
echo. >> "%LOG%"
echo Build finished successfully: %DATE% %TIME% >> "%LOG%"

:: ── Done ─────────────────────────────────────────────────────────
echo.
echo  ========================================
echo   DONE!
echo.
echo   Build\Release\DDS Converter\  ^<-- zip this for GitHub Releases
echo   Build\GitHub\                ^<-- push these files to the repo
echo  ========================================
echo.

explorer "%BUILD_ROOT%"
pause
endlocal