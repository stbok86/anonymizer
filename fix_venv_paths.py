"""
Fix hardcoded paths in virtual environment after installation to a new location.
This script updates all .exe and script files in .venv to use the correct Python path.
"""
import os
import sys
import re
from pathlib import Path

def fix_venv_paths(venv_root):
    """Fix all hardcoded paths in venv Scripts directory"""
    scripts_dir = Path(venv_root) / 'Scripts'
    
    if not scripts_dir.exists():
        print(f"[ERROR] Scripts directory not found: {scripts_dir}")
        return False
    
    # New python.exe path - use forward slashes for regex compatibility
    new_python = str((Path(venv_root) / 'Scripts' / 'python.exe').resolve()).replace('\\', '/')
    new_python_w = str((Path(venv_root) / 'Scripts' / 'pythonw.exe').resolve()).replace('\\', '/')
    
    # For Windows paths in files, we'll need backslashes
    new_python_win = str((Path(venv_root) / 'Scripts' / 'python.exe').resolve())
    new_python_w_win = str((Path(venv_root) / 'Scripts' / 'pythonw.exe').resolve())
    
    print(f"[INFO] Fixing venv paths...")
    print(f"[INFO] New Python path: {new_python_win}")
    
    fixed_count = 0
    
    # Fix all script files (bat, ps1, and executable wrappers)
    for script_file in scripts_dir.glob('*'):
        if script_file.suffix in ['.exe', '.exe~']:
            continue  # Skip actual executables
            
        if script_file.is_file():
            try:
                # Read file as binary first to detect encoding
                with open(script_file, 'rb') as f:
                    content_bytes = f.read()
                
                # Try to decode as text
                try:
                    content = content_bytes.decode('utf-8')
                    encoding = 'utf-8'
                except UnicodeDecodeError:
                    try:
                        content = content_bytes.decode('cp1252')
                        encoding = 'cp1252'
                    except:
                        continue  # Skip binary files
                
                # Replace old paths with new
                original_content = content
                
                # Replace any absolute paths to python.exe with new path
                # Match patterns like: #!C:/... or #!C:\... or VIRTUAL_ENV=...
                content = re.sub(
                    r'#![^\n]*?python\.exe',
                    f'#!{new_python}',
                    content,
                    flags=re.IGNORECASE
                )
                content = re.sub(
                    r'#![^\n]*?pythonw\.exe',
                    f'#!{new_python_w}',
                    content,
                    flags=re.IGNORECASE
                )
                
                # Fix VIRTUAL_ENV paths in activate scripts
                content = re.sub(
                    r'(VIRTUAL_ENV\s*=\s*)[\'"]?[^\'";\n]+[\'"]?',
                    lambda m: f'{m.group(1)}"{Path(venv_root).resolve()}"',
                    content
                )
                
                # Fix paths in batch files (using backslashes)
                if script_file.suffix in ['.bat', '.cmd']:
                    content = re.sub(
                        r'set\s+"VIRTUAL_ENV=[^"]*"',
                        f'set "VIRTUAL_ENV={new_python_win.rsplit(chr(92), 2)[0]}"',
                        content,
                        flags=re.IGNORECASE
                    )
                
                if content != original_content:
                    with open(script_file, 'w', encoding=encoding, newline='') as f:
                        f.write(content)
                    fixed_count += 1
                    print(f"[OK] Fixed: {script_file.name}")
                    
            except Exception as e:
                print(f"[WARN] Could not fix {script_file.name}: {e}")
    
    # Fix pyvenv.cfg
    pyvenv_cfg = Path(venv_root) / 'pyvenv.cfg'
    if pyvenv_cfg.exists():
        try:
            content = pyvenv_cfg.read_text()
            # Update home path to point to current Scripts directory
            content = re.sub(
                r'home\s*=\s*.*',
                f'home = {str(scripts_dir.resolve())}',
                content,
                flags=re.IGNORECASE
            )
            pyvenv_cfg.write_text(content)
            print(f"[OK] Fixed: pyvenv.cfg")
            fixed_count += 1
        except Exception as e:
            print(f"[WARN] Could not fix pyvenv.cfg: {e}")
    
    print(f"[SUCCESS] Fixed {fixed_count} files in venv")
    return True

if __name__ == '__main__':
    # Get venv path from command line or use default
    if len(sys.argv) > 1:
        venv_path = sys.argv[1]
    else:
        # Assume script is in project root, venv is .venv
        venv_path = Path(__file__).parent / '.venv'
    
    if not Path(venv_path).exists():
        print(f"[ERROR] Virtual environment not found: {venv_path}")
        sys.exit(1)
    
    success = fix_venv_paths(venv_path)
    sys.exit(0 if success else 1)
