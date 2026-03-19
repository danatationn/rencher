!include "MUI.nsh"
!include "nsDialogs.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"
!define NAME "Rencher"
!define APPFILE "rencher.exe"
!define VERSION "1.2.0.0"
!define PUBLISHER "danatationn"
!define MUI_ICON "..\assets\rencher-inst.ico"
!define MUI_UNICON "..\assets\rencher-deinst.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "..\assets\header_img.bmp"
!define MUI_HEADERIMAGE_BITMAP_RTL "..\assets\header_img_rtl.bmp"
!define MUI_WELCOMEFINISHPAGE_BITMAP "..\assets\welcome_img.bmp"
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_FUNCTION RunAppAfterInstall
!define MUI_FINISHPAGE_RUN_TEXT "Launch ${NAME}"

Name "${NAME}"
OutFile "..\build\RencherInstaller.exe"
InstallDir "$PROGRAMFILES\${NAME}"

RequestExecutionLevel admin
VIProductVersion "${VERSION}"
VIAddVersionKey "ProductName" "${NAME}"
VIAddVersionKey "CompanyName" "${PUBLISHER}"
VIAddVersionKey "LegalCopyright" "© 2025 ${PUBLISHER}"
VIAddVersionKey "FileDescription" "${NAME} Installer"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "ProductVersion" "${VERSION}"

ShowInstDetails show
ShowUninstDetails show

Var CHECK_DESKTOP
Var CHECK_STARTMENU

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
Page custom CustomOptionsPage CustomOptionsPageLeave
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

Function CustomOptionsPage
    nsDialogs::Create 1018
    Pop $0
    ${If} $0 == error
        Abort
    ${EndIf}

    ${NSD_CreateCheckbox} 10u 10u 200u 10u "Create desktop shortcut"
    Pop $CHECK_DESKTOP
    ${NSD_SetState} $CHECK_DESKTOP ${BST_CHECKED}

    ${NSD_CreateCheckbox} 10u 25u 200u 10u "Create Start Menu shortcut"
    Pop $CHECK_STARTMENU
    ${NSD_SetState} $CHECK_STARTMENU ${BST_CHECKED}

    nsDialogs::Show
FunctionEnd

Function CustomOptionsPageLeave
    ${NSD_GetState} $CHECK_DESKTOP $CHECK_DESKTOP
    ${NSD_GetState} $CHECK_STARTMENU $CHECK_STARTMENU
FunctionEnd

Section "Install"
	SetShellVarContext all

	SetOutPath $INSTDIR
	File /r "..\build\exe.mingw_x86_64_ucrt_gnu-3.12\*.*"
	WriteUninstaller "$INSTDIR\uninstaller.exe"
	WriteRegStr HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}" "DisplayName" "${NAME}"
	WriteRegStr HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}" "DisplayVersion" "${VERSION}"
	WriteRegStr HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}" "Publisher" "${PUBLISHER}"
	WriteRegStr HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}" "UninstallString" "$INSTDIR\uninstaller.exe"
	WriteRegStr HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}" "DisplayIcon" "$INSTDIR\${APPFILE}"
	WriteRegStr HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}" "InstallLocation" "$INSTDIR"
	WriteRegDWORD HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}" "NoModify" 1
	WriteRegDWORD HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}" "NoRepair" 1

    ${If} $CHECK_DESKTOP == ${BST_CHECKED}
        CreateShortcut "$DESKTOP\${NAME}.lnk" "$INSTDIR\${APPFILE}"
    ${EndIf}

    ${If} $CHECK_STARTMENU == ${BST_CHECKED}
        CreateDirectory "$SMPROGRAMS\${NAME}"
        CreateShortcut "$SMPROGRAMS\${NAME}\${NAME}.lnk" "$INSTDIR\${APPFILE}"
        CreateShortcut "$SMPROGRAMS\${NAME}\${NAME} Uninstaller.lnk" "$INSTDIR\uninstaller.exe"
    ${EndIf}
SectionEnd

Function RunAppAfterInstall
	Exec "$INSTDIR\${APPFILE}"
FunctionEnd

Section "Uninstall"
	SetShellVarContext all
	
    MessageBox MB_ICONQUESTION|MB_YESNO "Are you sure you want to uninstall ${NAME}?" IDYES +2
    Quit

    Delete "$INSTDIR\uninstaller.exe"
    Delete "$INSTDIR\${NAME}.exe"
    RMDir /r "$INSTDIR"
    DeleteRegKey HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}"

    Delete "$DESKTOP\${NAME}.lnk"
    Delete "$SMPROGRAMS\${NAME}\${NAME}.lnk"
    Delete "$SMPROGRAMS\${NAME}\${NAME} Uninstaller.lnk"
    RMDir "$SMPROGRAMS\${NAME}"
SectionEnd