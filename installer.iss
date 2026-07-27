#define MyAppName "AI Trading Desktop"
#define MyAppVersion "1.2.4"
#define MyAppPublisher "AI Trading Desktop"
#define MyAppExeName "AITradingDesktop.exe"

[Setup]
AppId={{D971865D-7E88-49C4-95A2-1ADAD0184AF8}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\AITradingDesktop
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=installer_output
OutputBaseFilename=AITradingDesktop-Setup-{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
CloseApplications=yes
RestartApplications=no
SetupLogging=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Buat shortcut di Desktop"; GroupDescription: "Shortcut:"; Flags: unchecked

[Files]
Source: "AITradingDesktop.exe"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{localappdata}\AITradingDesktop\Data"; Permissions: users-full

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Jalankan {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\desktop.stop"
Type: files; Name: "{app}\desktop_output.log"

[Code]
function InitializeUninstall(): Boolean;
begin
  Result := True;
end;
