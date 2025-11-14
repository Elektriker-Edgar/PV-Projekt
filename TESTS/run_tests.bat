@echo off
REM ============================================================
REM Automatisierte Precheck-Tests ausführen
REM ============================================================

cd /d "%~dp0"

echo.
echo ============================================================
echo   EDGARD ELEKTRO - PRECHECK TEST-SUITE
echo ============================================================
echo.

:MENU
echo Wähle einen Test:
echo.
echo [1] Browser-Test (sichtbar, langsam)
echo [2] Browser-Test (Hintergrund, schnell)
echo [3] Django-Test (ohne Browser)
echo [4] Alle Tests nacheinander
echo [0] Beenden
echo.

set /p choice="Deine Wahl (0-4): "

if "%choice%"=="1" goto BROWSER_SLOW
if "%choice%"=="2" goto BROWSER_FAST
if "%choice%"=="3" goto DJANGO_TEST
if "%choice%"=="4" goto ALL_TESTS
if "%choice%"=="0" goto END

echo Ungültige Wahl!
goto MENU

:BROWSER_SLOW
echo.
echo Starte Browser-Test (sichtbar, langsam)...
python test_precheck_automated.py
pause
goto MENU

:BROWSER_FAST
echo.
echo Starte Browser-Test (Hintergrund, schnell)...
python test_precheck_automated.py --headless --fast
pause
goto MENU

:DJANGO_TEST
echo.
echo Starte Django-Test...
cd ..
python manage.py test TESTS.test_precheck_django
pause
cd TESTS
goto MENU

:ALL_TESTS
echo.
echo ============================================================
echo   ALLE TESTS AUSFÜHREN
echo ============================================================
echo.

echo [1/2] Django-Test...
cd ..
python manage.py test TESTS.test_precheck_django
cd TESTS

echo.
echo [2/2] Browser-Test (schnell)...
python test_precheck_automated.py --headless --fast

echo.
echo ============================================================
echo   ALLE TESTS ABGESCHLOSSEN
echo ============================================================
pause
goto MENU

:END
echo.
echo Auf Wiedersehen!
exit /b 0
