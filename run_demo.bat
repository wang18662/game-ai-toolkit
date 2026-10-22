@echo off
REM ============================================================
REM  One-click demo launcher for game-ai-toolkit.
REM  Double-click to open the red-vs-blue AI battle window (loops by default).
REM  To change the AI matchup, edit the "bt utility" part on the last line
REM  to e.g. "fsm bt" or "utility utility".
REM ============================================================
cd /d "%~dp0"
python examples/run_skirmish.py tests/fixtures/maps/arena.json bt utility --loop
pause
