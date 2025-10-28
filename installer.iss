; Inno Setup インストーラースクリプト
; 拾得物管理システム用インストーラー

#define MyAppName "拾得物管理システム"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "拾得物管理システム開発チーム"
#define MyAppURL "https://example.com/"
#define MyAppExeName "flet_app.exe"

[Setup]
; 基本情報
AppId={{3A4B5C6D-7E8F-9A0B-C1D2-E3F4A5B6C7D8}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; デフォルトインストール先
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes

; 権限設定
PrivilegesRequired=admin
OutputDir=installer
OutputBaseFilename=拾得物管理システム_Setup_{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; 日本語UI
LicenseFile=
InfoBeforeFile=
InfoAfterFile=

; アーキテクチャ（64ビット）
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; メイン実行ファイル（PyInstallerでビルド済み）
Source: "dist\flet_app.exe"; DestDir: "{app}"; Flags: ignoreversion

; データベース初期化
Source: "lostitem.db"; DestDir: "{commonappdata}\{#MyAppName}\data\database"; Flags: ignoreversion onlyifdoesntexist; DestName: "lostitem.db"

; 設定ファイル
Source: "data\config\paths.py"; DestDir: "{commonappdata}\{#MyAppName}\data\config"; Flags: ignoreversion

[Dirs]
; データディレクトリ構造を作成
Name: "{commonappdata}\{#MyAppName}\data"
Name: "{commonappdata}\{#MyAppName}\data\backups"
Name: "{commonappdata}\{#MyAppName}\data\backups\database"
Name: "{commonappdata}\{#MyAppName}\data\backups\images"
Name: "{commonappdata}\{#MyAppName}\data\config"
Name: "{commonappdata}\{#MyAppName}\data\database"
Name: "{commonappdata}\{#MyAppName}\data\images"
Name: "{commonappdata}\{#MyAppName}\data\images\bundle"
Name: "{commonappdata}\{#MyAppName}\data\images\main"
Name: "{commonappdata}\{#MyAppName}\data\images\sub"
Name: "{commonappdata}\{#MyAppName}\data\logs"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait skipifsilent

[Code]
// インストール後にデータディレクトリのパスを環境変数に設定するカスタムコード
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // 必要な初期化処理があればここに記述
  end;
end;

// データディレクトリのパスを取得する関数
function GetDataDir: String;
begin
  Result := ExpandConstant('{commonappdata}') + '\' + '{#MyAppName}\data';
end;

