python ..\setup.py py2exe
rmdir /s /q ..\build
xcopy "etc" "build\etc" /D /E /C /R /I /K /Y
xcopy "lib" "build\lib" /D /E /C /R /I /K /Y
python fix_paths.py
"%programfiles%\NSIS\makensis.exe" guicavane.nsi
cd ..
echo [DONE] Windows build can be found in windows/build and the installer in windows/Guicavane.exe