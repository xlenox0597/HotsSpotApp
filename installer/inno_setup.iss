; =========================================================================
; Inno Setup Script for Apple USB HotSpot Manager
; Bundles the application, UI, and WHQL-signed Apple network drivers
; =========================================================================

#define MyAppName "Apple USB HotSpot Manager"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "HotSpotApp"
#define MyAppExeName "HotSpotManager.exe"

[Setup]
AppId={{D37E84B2-1699-4A73-95A1-E7CF58DF4851}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputBaseFilename=HotSpotApp_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Dist files compiled by PyInstaller
Source: "..\dist\HotSpotManager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Drivers
Source: "..\drivers\*"; DestDir: "{app}\drivers"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Silently register Apple USB Driver
Filename: "pnputil.exe"; Parameters: "/add-driver ""{app}\drivers\appleusb\AppleUsb.inf"" /install"; StatusMsg: "Installing Apple USB Driver..."; Flags: runhidden
; Silently register Apple Mobile Device Ethernet Driver
Filename: "pnputil.exe"; Parameters: "/add-driver ""{app}\drivers\netaapl64\netaapl64.Inf"" /install"; StatusMsg: "Installing Apple Mobile Device Ethernet Driver..."; Flags: runhidden
; Post-install launch
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Optional uninstall clean-up
