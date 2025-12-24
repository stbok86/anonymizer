; ============================================================================
; Document Anonymizer - Inno Setup Script
; ============================================================================
; Этот скрипт создает установщик для локального развертывания
; Document Anonymizer на компьютерах сотрудников
; ============================================================================

#define MyAppName "Document Anonymizer"
#define MyAppVersion "1.0"
#define MyAppPublisher "Your Company"
#define MyAppURL "http://localhost:8501"
#define MyAppExeName "start_all_services_unified.bat"
#define SourcePath "C:\Projects\Anonymizer"

[Setup]
; Основные настройки приложения
AppId={{A1B2C3D4-E5F6-4789-A1B2-C3D4E5F67890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Настройки установки
DefaultDirName={commonpf32}\DocumentAnonymizer
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; LicenseFile={#SourcePath}\LICENSE.txt
; InfoBeforeFile={#SourcePath}\README.txt
OutputDir={#SourcePath}\Output
OutputBaseFilename=AnonymizerSetup_v{#MyAppVersion}

; Настройки компрессии
Compression=lzma2/max
SolidCompression=yes

; Визуальные настройки
WizardStyle=modern
; SetupIconFile={#SourcePath}\icon.ico
; UninstallDisplayIcon={app}\icon.ico

; Права администратора не требуются
PrivilegesRequired=lowest

; Архитектура
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]

; Копируем все файлы проекта, кроме .venv и временных
Source: "{#SourcePath}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; \
  Excludes: "\Output,\*.pyc,\__pycache__,\.git,\.vscode,\.idea,\*.log,\test_docs,\venv_*,\.venv,\requirements.txt,\fix_venv_paths.py,\get-pip.py"

; Копируем portable Python
Source: "{#SourcePath}\python\python-3.11.0-embed-amd64\*"; DestDir: "{app}\python\python-3.11.0-embed-amd64"; Flags: ignoreversion recursesubdirs createallsubdirs

; Копируем документацию
Source: "{#SourcePath}\DEPLOYMENT_README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourcePath}\README.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
; Главное меню
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Comment: "Запустить Document Anonymizer (единое окно)"
Name: "{group}\{#MyAppName} (отдельные окна)"; Filename: "{app}\start_all_services.bat"; WorkingDir: "{app}"; Comment: "Запустить с отдельными окнами для каждого сервиса"
Name: "{group}\Остановить сервисы"; Filename: "{app}\stop_all_services.bat"; WorkingDir: "{app}"
Name: "{group}\Проверить статус"; Filename: "{app}\check_services_status.bat"; WorkingDir: "{app}"
Name: "{group}\Открыть в браузере"; Filename: "{#MyAppURL}"
Name: "{group}\Руководство по развертыванию"; Filename: "{app}\DEPLOYMENT_README.md"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Рабочий стол
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; WorkingDir: "{app}"

; Быстрый запуск
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon; WorkingDir: "{app}"

[Run]
; После установки предлагаем запустить приложение
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// ============================================================================
// Pascal Script для дополнительной логики
// ============================================================================


procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    // Останавливаем процессы перед удалением
    Exec('taskkill.exe', '/F /IM python.exe /T', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Exec('taskkill.exe', '/F /IM streamlit.exe /T', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Sleep(1000);
  end;
end;

function GetUninstallString(): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  sUnInstPath := ExpandConstant('Software\Microsoft\Windows\CurrentVersion\Uninstall\{#emit SetupSetting("AppId")}_is1');
  sUnInstallString := '';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString) then
    RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;

function IsUpgrade(): Boolean;
begin
  Result := (GetUninstallString() <> '');
end;

function UnInstallOldVersion(): Integer;
var
  sUnInstallString: String;
  iResultCode: Integer;
begin
  Result := 0;
  sUnInstallString := GetUninstallString();
  if sUnInstallString <> '' then begin
    sUnInstallString := RemoveQuotes(sUnInstallString);
    if Exec(sUnInstallString, '/SILENT /NORESTART /SUPPRESSMSGBOXES','', SW_HIDE, ewWaitUntilTerminated, iResultCode) then
      Result := 3
    else
      Result := 2;
  end else
    Result := 1;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if (CurPageID = wpSelectDir) and IsUpgrade() then
  begin
    if MsgBox('Обнаружена предыдущая версия приложения.' + #13#10 + 
              'Удалить её перед установкой новой версии?', 
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      UnInstallOldVersion();
    end;
  end;
end;

[Messages]
WelcomeLabel1=Добро пожаловать в мастер установки [name]
WelcomeLabel2=Программа установит [name/ver] на ваш компьютер.%n%nРекомендуется закрыть все работающие приложения перед продолжением.
FinishedLabel=Установка [name] завершена.%n%nПриложение готово к использованию. Запустите его через ярлык на рабочем столе или в меню "Пуск".

[CustomMessages]
russian.LaunchProgram=Запустить %1
english.LaunchProgram=Launch %1

; ============================================================================
; ПРИМЕЧАНИЯ ПО ИСПОЛЬЗОВАНИЮ:
; ============================================================================
; 1. Перед компиляцией создайте файлы (опционально):
;    - LICENSE.txt в корне проекта
;    - icon.ico (иконка приложения)
;
; 2. Размер установщика будет примерно 200-300 MB после компрессии
;
; 3. Исключения настроены так, чтобы не копировать:
;    - .pyc файлы и __pycache__
;    - .git, .vscode, .idea
;    - Логи и временные файлы
;    - Тестовые документы
;    - Старые venv_* папки
;
; 4. Установщик требует около 600-800 MB свободного места
;
; 5. Для компиляции:
;    - Откройте этот файл в Inno Setup Compiler
;    - Build → Compile
;    - Готовый установщик будет в папке Output/
; ============================================================================
