@echo off
rem DSI Studio "Save matrix" ile kaydettiginiz .mat dosyasini bu dosyanin ustune surukleyip birakin.
rem Ayni klasorde <dosyaadi>_for_graph.mat olusur; Visualize Graph icin onu secin.
if "%~1"=="" (
  echo Kullanim: .mat dosyasini bu dosyanin ustune surukleyip birakin.
  pause
  exit /b 1
)
python "%~dp0scripts\connectome_tools.py" graphmat --mat "%~1" --out "%~dpn1_for_graph.mat"
pause
