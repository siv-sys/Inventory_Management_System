$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = "C:\Program Files\PostgreSQL\18\pgAdmin 4\python\python.exe"
$DepsPath = Join-Path $env:TEMP "inventory_app_site3"
$AppPath = Join-Path $ProjectRoot "app.py"

& $PythonExe -c "import sys, runpy; sys.path = [p for p in sys.path if 'pgAdmin 4\\python\\Lib\\site-packages' not in p]; sys.path.insert(0, r'$DepsPath'); sys.path.insert(0, r'$ProjectRoot'); runpy.run_path(r'$AppPath', run_name='__main__')"
