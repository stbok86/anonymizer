# Решение проблемы "Virtualization support not detected" для VDI

## �️ ВИРТУАЛЬНАЯ МАШИНА VDI

### 🔧 Настройки VirtualBox (если используется)

1. **Выключите виртуальную машину**
2. **Откройте VirtualBox Manager**
3. **Выберите вашу VM → Настройки → Система → Процессор**
4. **Включите**:
   - ✅ "Включить VT-x/AMD-V" 
   - ✅ "Включить Nested Paging"
5. **Перейдите в Система → Ускорение**
6. **Включите**:
   - ✅ "Включить VT-x/AMD-V"
   - ✅ "Включить Nested Paging" 
7. **Сохраните настройки и запустите VM**

### 🔧 Настройки VMware (если используется)

1. **Выключите виртуальную машину**
2. **Откройте настройки VM**
3. **Процессор → Возможности виртуализации**
4. **Включите**:
   - ✅ "Virtualize Intel VT-x/EPT or AMD-V/RVI"
   - ✅ "Virtualize CPU performance counters"
5. **Сохраните и запустите VM**

### 🔧 Альтернативные решения для VDI

#### 1. Docker без Hyper-V (рекомендуется для VDI)
```powershell
# Переключить Docker Desktop на Windows containers
# В трее Docker Desktop → Switch to Windows containers
```

#### 2. Использовать Docker Toolbox
- Скачать Docker Toolbox (старая версия Docker для VirtualBox)
- Работает без Hyper-V

#### 3. Использовать WSL без Docker Desktop
```powershell
# Установить Docker напрямую в WSL
wsl --install -d Ubuntu
# В Ubuntu: curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh
```

### 🎯 Рекомендуемое решение для VDI:
**Используйте Docker в режиме Windows containers** - это самый простой способ в виртуальной машине.

### 2. Включите компоненты Windows (от администратора)

Откройте **PowerShell от имени администратора** и выполните:

```powershell
# Включить Hyper-V
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All

# Включить контейнеры
Enable-WindowsOptionalFeature -Online -FeatureName Containers -All

# Включить подсистему Windows для Linux
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux

# Включить платформу виртуальных машин
Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform
```

### 3. Через GUI (Программы и компоненты)

1. `Win+R` → `appwiz.cpl`
2. "Включение или отключение компонентов Windows"
3. Включите:
   - ✅ Hyper-V
   - ✅ Контейнеры
   - ✅ Подсистема Windows для Linux
   - ✅ Платформа виртуальных машин

### 4. Проверка после изменений

```powershell
# Проверить виртуализацию
systeminfo | findstr /i "hyper"

# Проверить WSL
wsl --status

# Перезапустить Docker Desktop
```

### 5. Альтернатива: Docker без Hyper-V

Если виртуализация недоступна, используйте Docker Toolbox или переключите Docker Desktop в режим Windows containers.

## ⚠️ Важно
После включения компонентов **ОБЯЗАТЕЛЬНО ПЕРЕЗАГРУЗИТЕ** компьютер!

## 🎯 Последовательность действий
1. ✅ Проверить BIOS/UEFI
2. ✅ Включить компоненты Windows  
3. ✅ Перезагрузиться
4. ✅ Запустить Docker Desktop
5. ✅ Проверить проект