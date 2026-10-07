; WEED desktop installer for Windows.
;
; Compile it from the repository root, after running tools/build_release.py:
;
;   iscc /DMyAppVersion=2.1.3 packaging\windows\WEED.iss
;
; The bundle built by PyInstaller (release\bundle) is packaged as-is, so the
; wallet and the miner can still find the node they run in the background.

#ifndef MyAppVersion
  #error "Define MyAppVersion, e.g. /DMyAppVersion=2.1.3"
#endif

#define MyAppName "WEED"
#define MyAppPublisher "Alessio Della Santa"
#define MyAppURL "https://github.com/alessio-ds/WEED"

[Setup]
; The script lives in packaging/windows; make paths like release\bundle
; resolve from the repository root.
SourceDir=..\..
AppId={{9D6447AD-B4F8-4D36-B5AD-31F27A991CCF}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\WEED
DefaultGroupName=WEED
DisableProgramGroupPage=yes
OutputDir=release
OutputBaseFilename=WEED-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\weed-wallet-gui.exe

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"

[Files]
Source: "release\bundle\*"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName} Wallet"; Filename: "{app}\weed-wallet-gui.exe"
Name: "{autoprograms}\{#MyAppName} Miner"; Filename: "{app}\weed-miner-gui.exe"
Name: "{autodesktop}\{#MyAppName} Wallet"; Filename: "{app}\weed-wallet-gui.exe"; Tasks: desktopicon
Name: "{autodesktop}\{#MyAppName} Miner"; Filename: "{app}\weed-miner-gui.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\weed-wallet-gui.exe"; Description: "Launch the {#MyAppName} wallet"; Flags: nowait postinstall skipifsilent
