; Inno Setup Script for TREQSO Automation Tool v2.1
; Fully portable — bundles node.exe, no system Node.js required.

#define MyAppName      "TREQSO Automation Tool"
#define MyAppVersion   "1.0.2"
#define MyAppPublisher "Dejana Truck"
#define MyAppURL       "n/a"
#define MyAppExeName   "TREQSO_Automation.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installation directories
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Output settings
OutputDir=installer_output
OutputBaseFilename=TREQSO_Automation_Setup_v{#MyAppVersion}
SetupIconFile=icon.ico

; Compression
Compression=lzma2/ultra64
SolidCompression=yes

; Windows version requirements
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; Privileges — admin needed for Program Files; user can override to per-user
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; Visual appearance
WizardStyle=modern
DisableWelcomePage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; ---------------------------------------------------------------
; Main executable (Python + GUI bundled by PyInstaller)
; ---------------------------------------------------------------
Source: "dist\TREQSO_Automation.exe"; DestDir: "{app}"; Flags: ignoreversion

; ---------------------------------------------------------------
; Portable Node.js — node.exe only, no system Node.js required
; ---------------------------------------------------------------
Source: "node_portable\node.exe"; DestDir: "{app}\node_portable"; Flags: ignoreversion

; ---------------------------------------------------------------
; TypeScript compiled automation engine
; ---------------------------------------------------------------
Source: "dist\cli.js";                 DestDir: "{app}\dist"; Flags: ignoreversion
Source: "dist\treqso-automation.js";   DestDir: "{app}\dist"; Flags: ignoreversion
Source: "dist\*.js.map";               DestDir: "{app}\dist"; Flags: ignoreversion
Source: "dist\*.d.ts";                 DestDir: "{app}\dist"; Flags: ignoreversion

; ---------------------------------------------------------------
; Node.js dependencies (pre-built on developer machine)
; node_modules is bundled here — no npm install required at install time.
; ---------------------------------------------------------------
Source: "node_modules\*"; DestDir: "{app}\node_modules"; Flags: ignoreversion recursesubdirs createallsubdirs

; ---------------------------------------------------------------
; Node.js package manifests (needed so node can resolve module paths)
; ---------------------------------------------------------------
Source: "package.json";      DestDir: "{app}"; Flags: ignoreversion
Source: "package-lock.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "tsconfig.json";     DestDir: "{app}"; Flags: ignoreversion

; ---------------------------------------------------------------
; Configuration — only create .env if it does not already exist so
; reinstalls / upgrades preserve the user's settings.
; ---------------------------------------------------------------
Source: ".env.template"; DestDir: "{app}"; DestName: ".env"; Flags: onlyifdoesntexist uninsneveruninstall

; ---------------------------------------------------------------
; Sample data and templates
; ---------------------------------------------------------------
Source: "sample_parts.csv";   DestDir: "{app}"; Flags: ignoreversion
Source: "sample_bom.csv";     DestDir: "{app}"; Flags: ignoreversion
Source: "sample_edit_parts.csv";     DestDir: "{app}"; Flags: ignoreversion
Source: "Parts_Template.csv"; DestDir: "{app}"; Flags: ignoreversion
Source: "BOMs_Template.csv";  DestDir: "{app}"; Flags: ignoreversion
Source: "Edit_Parts_Template.csv"; DestDir: "{app}"; Flags: ignoreversion

; ---------------------------------------------------------------
; Documentation
; ---------------------------------------------------------------
Source: "README_USER.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\{#MyAppName}";                        Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}";  Filename: "{uninstallexe}"
Name: "{group}\User Guide";                           Filename: "{app}\GUIDE.md"
Name: "{group}\Sample Files\Sample Parts";            Filename: "{app}\sample_parts.csv"
Name: "{group}\Sample Files\Sample BOM";              Filename: "{app}\sample_bom.csv"
Name: "{group}\Sample Files\Sample Edit Parts";              Filename: "{app}\sample_edit_parts.csv"
Name: "{autodesktop}\{#MyAppName}";                   Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Offer to open .env for configuration right after install
Filename: "notepad.exe"; Parameters: "{app}\.env"; \
  Description: "Configure TREQSO connection settings (URL and Company)"; \
  Flags: postinstall shellexec skipifsilent nowait

; Offer to launch the application immediately
Filename: "{app}\{#MyAppExeName}"; \
  Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; \
  Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up directories that are created / populated at runtime
Type: filesandordirs; Name: "{app}\node_modules"
Type: filesandordirs; Name: "{app}\node_portable"
Type: filesandordirs; Name: "{app}\dist"
Type: files;          Name: "{app}\.env"
