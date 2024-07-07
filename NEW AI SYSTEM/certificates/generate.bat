@echo off
REM Get the directory of the script
set SCRIPT_DIR=%~dp0

REM Change to the script directory
cd /d "%SCRIPT_DIR%"

REM Generate SSL certificate and key in the script directory
openssl req -nodes -new -x509 -keyout server.key -out server.cert

REM Check if the certificate generation was successful
IF %ERRORLEVEL% EQU 0 (
    echo SSL certificate and key have been generated successfully.
    echo Certificate: %SCRIPT_DIR%server.cert
    echo Key: %SCRIPT_DIR%server.key
) ELSE (
    echo Failed to generate SSL certificate.
)

pause
