; instalador.iss — Inno Setup Script para Jarvis MK2

#define AppName      "J.A.R.V.I.S MK2"
#define AppVersion   "2.0.0"
#define AppPublisher "lcorb10"
#define AppExeName   "JarvisMK2.exe"
#define AppDir       "dist\JarvisMK2"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisherURL=https://github.com/lcorb10/Jarvis
AppSupportURL=https://github.com/lcorb10/Jarvis/issues
AppUpdatesURL=https://github.com/lcorb10/Jarvis/releases
DefaultDirName={autopf}\JarvisMK2
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=dist
OutputBaseFilename=JarvisMK2_Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64
MinVersion=10.0.19041

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon";   Description: "Crear icono en el escritorio";    GroupDescription: "Iconos adicionales:"
Name: "startupentry";  Description: "Iniciar con Windows";              GroupDescription: "Inicio automático:"; Flags: unchecked

[Files]
Source: "{#AppDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}";         Filename: "{app}\{#AppExeName}"
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}";   Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "JarvisMK2"; ValueData: """{app}\{#AppExeName}"""; Flags: uninsdeletevalue; Tasks: startupentry

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Iniciar {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\backups"
Type: files;          Name: "{app}\memoria_jarvis.json"
Type: files;          Name: "{app}\aprendizaje_estado.json"

[Code]
procedure InitializeWizard;
begin
  WizardForm.WelcomeLabel2.Caption :=
    'Este asistente instalará J.A.R.V.I.S MK2 en su equipo.' + #13#10 + #13#10 +
    'Se recomienda cerrar todas las aplicaciones antes de continuar.' + #13#10 + #13#10 +
    'Haga clic en Siguiente para continuar.';
end;
