@echo off
REM Daily market-research run, called by Windows Task Scheduler at 06:00.
REM
REM The previous version was: python main.py
REM No log, no exit code check. When Reddit started returning 403 the pipeline
REM collected nothing, exited zero, and Task Scheduler reported success every
REM morning for seven weeks. This version keeps a log and passes the real exit
REM code back, so a silent failure becomes a visible one.

cd /d C:\DevProjects\solosolutions-spider

if not exist logs mkdir logs
for /f "tokens=1-3 delims=/ " %%a in ("%date%") do set STAMP=%%c-%%a-%%b
set LOG=logs\spider-%STAMP%.log

echo ================================================= >> "%LOG%"
echo Run started %date% %time% >> "%LOG%"

python main.py >> "%LOG%" 2>&1
set RC=%ERRORLEVEL%

echo Run finished %date% %time% with exit code %RC% >> "%LOG%"

if %RC% NEQ 0 (
  echo FAILED with exit code %RC%. See %LOG%
) else (
  echo OK. See %LOG%
)

exit /b %RC%
