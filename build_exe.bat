@echo off
REM ============================================================
REM  Build a single standalone .exe (run ONCE on a machine that
REM  has Python + pygame + numpy installed, e.g. your anaconda PC).
REM  Output: dist\gameai-skirmish.exe
REM    - Double-click to run. The demo PC needs NO Python / pygame.
REM    - Map JSON is bundled inside the exe. Single file is enough.
REM  Usage: just double-click this file (runs in game-ai-toolkit root).
REM ============================================================
cd /d "%~dp0"

REM 1) Install the bundler (pygame/numpy already present -> "already satisfied")
python -m pip install pyinstaller

REM 2) Freeze into a single-file exe
REM    --onefile      : produce one gameai-skirmish.exe
REM    (no --noconsole on purpose: keep the console so any pygame/SDL error is
REM     visible on the demo PC. Once it runs fine, add --noconsole for a clean
REM     window-only look and rebuild.)
REM    --paths src    : let PyInstaller find the gameai package
REM    --add-data     : embed the map JSON inside the exe (Windows uses ; as separator)
python -m PyInstaller --onefile --clean --name gameai-skirmish ^
  --paths src ^
  --hidden-import pygame ^
  --add-data "tests/fixtures/maps;tests/fixtures/maps" ^
  examples/run_skirmish.py

echo.
echo ============================================================
echo  Build finished.
echo  Copy  dist\gameai-skirmish.exe  to any Windows PC, double-click to run.
echo  (Default: RED behavior-tree vs BLUE utility, looping demo, close window to exit)
echo.
echo  If double-click does nothing: run the exe from CMD to see the error,
echo  or remove the --noconsole flag above and rebuild to show a console.
echo ============================================================
pause
