; The name of the installer
Name "Guicavane"
OutFile "Guicavane-install.exe"
SetCompressor /SOLID lzma
InstallDir $PROGRAMFILES\Guicavane

; Registry key to check for directory (so if you install again, it will 
; overwrite the old one automatically)
InstallDirRegKey HKLM "Software\Guicavane" "Install_Dir"


; UI

!include "MUI.nsh"
!include "Sections.nsh"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "header.bmp"

!define MUI_ICON "../guicavane/images/logo.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

;Interface Settings
!define MUI_ABORTWARNING

XPStyle on
  !insertmacro MUI_DEFAULT MUI_WELCOMEFINISHPAGE_BITMAP "left.bmp"
  !insertmacro MUI_DEFAULT MUI_UNWELCOMEFINISHPAGE_BITMAP "left.bmp"
  !insertmacro MUI_PAGE_WELCOME


!define MUI_FINISHPAGE_RUN $INSTDIR\Guicavane.exe

!insertmacro MUI_RESERVEFILE_LANGDLL

; Pages 

!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

;installer languages
!insertmacro MUI_LANGUAGE "Spanish"
;--------------------------------

Section "Guicavane"

  SectionIn RO
  
  ; Set output path to the installation directory.
  SetOutPath $INSTDIR
    
  ; Put file there
  File /r build\*.*
  
  ; Write the installation path into the registry
  WriteRegStr HKLM SOFTWARE\Guicavane "Install_Dir" "$INSTDIR"
  
  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Guicavane" "DisplayName" "Guicavane"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Guicavane" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Guicavane" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Guicavane" "NoRepair" 1
  WriteUninstaller "uninstall.exe"
  
SectionEnd

; Optional section (can be disabled by the user)
Section "Start Menu Shortcuts"

  CreateDirectory "$SMPROGRAMS\Guicavane"
  CreateShortCut "$SMPROGRAMS\Guicavane\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
  CreateShortCut "$SMPROGRAMS\Guicavane\Guicavane.lnk" "$INSTDIR\Guicavane.exe" "" "$INSTDIR\Guicavane.exe" 0

  CreateShortCut "$SMPROGRAMS\Guicavane\Webpage.lnk" "http://www.github.com/j0hn/guicavane"
  
SectionEnd


;--------------------------------

; Uninstaller

Section "un.Uninstall"
  
  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Guicavane"
  DeleteRegKey HKLM SOFTWARE\Guicavane

  ; Remove files and uninstaller
  RMDir /r "$INSTDIR"
  ;Delete $INSTDIR\*.*
  
  ; Remove shortcuts, if any
  Delete "$SMPROGRAMS\Guicavane\*.*"

  ; Remove directories used
  RMDir "$SMPROGRAMS\Guicavane"
  RMDir "$INSTDIR"

SectionEnd


;--------------------------------

; Other
