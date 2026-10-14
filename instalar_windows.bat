@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ================================================
echo   MERCADO WEB - INSTALADOR PARA WINDOWS
echo ================================================
echo.
where py >nul 2>nul
if %errorlevel%==0 (
  set PYTHON=py
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Python nao foi encontrado.
    echo Instale o Python 3.11 ou superior em https://www.python.org/downloads/windows/
    echo Marque a opcao "Add Python to PATH" durante a instalacao.
    pause
    exit /b 1
  )
  set PYTHON=python
)
echo [1/3] Criando ambiente virtual...
%PYTHON% -m venv .venv
if errorlevel 1 goto erro
 echo [2/3] Instalando dependencias...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto erro
echo.
echo [3/3] Instalacao concluida!
echo Usuario inicial: admin
echo Senha inicial: Mercado@2026!
echo Altere a senha e mantenha o arquivo .env privado antes de publicar na internet.
echo.
echo O site sera aberto no navegador ao executar iniciar_windows.bat.
pause
exit /b 0
:erro
echo.
echo Ocorreu um erro durante a instalacao. Confira se o Python esta instalado e tente novamente.
pause
exit /b 1
