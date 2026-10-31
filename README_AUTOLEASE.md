# AutoLease Peru - aplicación de escritorio

## Estructura

```text
autolease_app/
  __init__.py
  app.py
  config.py
  database.py
  ui.py
requirements.txt
.env.example
```

## Requisitos

1. SQL Server Express con la instancia `.\SQLEXPRESS`.
2. Base de datos `db_leasing_vehicular` creada ejecutando
   `db_leasing_vehicular.sql`.
3. Microsoft ODBC Driver 17 for SQL Server (o ajustar
   `AUTOLEASE_DB_DRIVER` al controlador instalado).
4. Python 3.10 o superior.

Instalar las dependencias:

```powershell
py -m pip install -r requirements.txt
```

## Configuración

La aplicación usa autenticación SQL por defecto para validar el formulario
de inicio de sesión directamente contra SQL Server. El script del proyecto
crea el usuario de demostración `estudiante1` con contraseña
`Password123!`. Para producción se debe cambiar esa contraseña.

La pantalla de inicio también incluye la opción **Usar Windows Authentication**.
Al seleccionarla, la aplicación comprueba la conexión usando la cuenta de
Windows actualmente iniciada, igual que `sqlcmd -S .\SQLEXPRESS -E -C`.

Las variables de configuración se pueden definir en PowerShell:

```powershell
$env:AUTOLEASE_DB_SERVER = '.\SQLEXPRESS'
$env:AUTOLEASE_DB_NAME = 'db_leasing_vehicular'
$env:AUTOLEASE_DB_AUTH = 'sql'
$env:AUTOLEASE_DB_DRIVER = 'ODBC Driver 17 for SQL Server'
```

Para usar Windows Authentication en la capa de datos, configure
`AUTOLEASE_DB_AUTH=windows`. El formulario de login está diseñado para
validar credenciales SQL, aunque también permite la autenticación integrada
de Windows.

Si SQL Server devuelve el error 18456 para `estudiante1`, compruebe que
la autenticación mixta esté habilitada y que el login tenga la contraseña
esperada. Desde una sesión administrativa de `sqlcmd` se puede corregir
con:

```sql
ALTER LOGIN estudiante1 WITH PASSWORD = 'Password123!';
```

## Ejecución

Siga estos pasos para ejecutar el programa desde cero.

### 1. Comprobar SQL Server Express

Verifique que el servicio de SQL Server Express esté iniciado. Desde
PowerShell se puede comprobar con:

```powershell
Get-Service 'MSSQL$SQLEXPRESS'
```

Si está detenido, inícielo desde **SQL Server Configuration Manager** o con
permisos administrativos:

```powershell
Start-Service 'MSSQL$SQLEXPRESS'
```

Compruebe también que la instancia responda:

```powershell
sqlcmd -S '.\SQLEXPRESS' -E -C -Q "SELECT @@SERVERNAME, DB_NAME()"
```

### 2. Crear o actualizar la base de datos

Si la base de datos todavía no existe, ejecute el script principal desde la
carpeta del proyecto:

```powershell
sqlcmd -S '.\SQLEXPRESS' -E -C -i '.\db_leasing_vehicular.sql'
```

El script crea `db_leasing_vehicular`, sus tablas, procedimientos y vistas.
La cuenta utilizada debe tener permisos suficientes para crear la base de
datos. Si el script ya fue ejecutado, no lo ejecute nuevamente sobre una
instalación con datos que desea conservar.

### 3. Abrir la carpeta en VS Code

Abra **Visual Studio Code**, seleccione **File > Open Folder** y elija la
carpeta del proyecto:

```text
C:\Projects\uni\basededatos\Nueva carpeta
```

Abra una terminal integrada con **Terminal > New Terminal**. Los comandos
de las siguientes secciones deben ejecutarse desde esa carpeta, es decir,
desde el directorio que contiene `autolease_app`, `requirements.txt` y
`db_leasing_vehicular.sql`.

### 4. Crear un entorno virtual (recomendado)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Si PowerShell impide activar el entorno por la política de ejecución,
puede ejecutar el programa usando directamente el intérprete del entorno:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 5. Instalar las dependencias

Con el entorno virtual activado:

```powershell
python -m pip install -r requirements.txt
```

Este comando instala `customtkinter` y `pyodbc`. El controlador ODBC de
Microsoft debe instalarse por separado; no se instala mediante `pip`.

### 6. Configurar la conexión

Para usar el usuario SQL creado por el script:

```powershell
$env:AUTOLEASE_DB_SERVER = '.\SQLEXPRESS'
$env:AUTOLEASE_DB_NAME = 'db_leasing_vehicular'
$env:AUTOLEASE_DB_AUTH = 'sql'
$env:AUTOLEASE_DB_DRIVER = 'ODBC Driver 17 for SQL Server'
$env:AUTOLEASE_TRUST_CERT = 'yes'
```

La aplicación solicita las credenciales en la pantalla de login. Como
ejemplo académico, el script crea `estudiante1` con `Password123!`.
Para una instalación real, cambie esta contraseña y no la incluya en
archivos públicos.

También se puede usar Windows Authentication desde la propia pantalla de
login seleccionando **Usar Windows Authentication**. Esta opción utiliza
la cuenta actual de Windows, equivalente a `sqlcmd -E`.

### 7. Ejecutar el programa

Con el entorno virtual activado, ejecute:

```powershell
python -m autolease_app.app
```

Si no utiliza un entorno virtual:

```powershell
py -m autolease_app.app
```

Se abrirá la ventana de inicio de sesión. Introduzca las credenciales SQL
o seleccione **Usar Windows Authentication**. Después del acceso se mostrará
el dashboard con las opciones Clientes, Vehículos, Contratos, Pagos,
Mantenimientos y Reportes.

### 8. Ejecutar desde el depurador de VS Code

Abra [app.py](./autolease_app/app.py) y pulse **Run Python File**. También
puede crear una configuración de depuración seleccionando **Run and Debug**
en VS Code y eligiendo Python. El módulo que debe ejecutarse es:

```text
autolease_app.app
```

Ejecutar el módulo, en lugar de abrir directamente un archivo aislado,
mantiene correctas las importaciones relativas de la aplicación.

### 9. Flujo de uso

1. Inicie sesión.
2. Seleccione una sección en el menú lateral.
3. Use **Nuevo** o los formularios para introducir información.
4. Seleccione una fila de la tabla para actualizarla o eliminarla.
5. Pulse **Buscar** o **Actualizar** para recargar los datos.
6. Abra **Reportes** y seleccione una de las vistas disponibles.

El inicio de sesión valida el usuario y la contraseña contra
`db_leasing_vehicular`. Después se muestran las pantallas de clientes,
vehículos, contratos, pagos, mantenimientos y reportes. Las operaciones
CRUD usan consultas parametrizadas (`?`) y la capa `DatabaseManager`
centraliza conexiones, SELECT, INSERT, UPDATE y DELETE.

## Solución de problemas

- **`No module named customtkinter` o `No module named pyodbc`:** active
  `.venv` y ejecute `python -m pip install -r requirements.txt`.
- **`Data source name not found` o error de driver:** instale Microsoft
  ODBC Driver 17 for SQL Server o cambie `AUTOLEASE_DB_DRIVER` al nombre
  exacto mostrado en la configuración ODBC.
- **Error 18456 al iniciar sesión:** confirme que el login SQL exista,
  que la autenticación mixta esté habilitada y que la contraseña sea
  correcta. Como administrador puede ejecutar:

  ```sql
  ALTER LOGIN estudiante1 WITH PASSWORD = 'Password123!';
  ```

- **Error de conexión a `.\SQLEXPRESS`:** compruebe el servicio
  `MSSQL$SQLEXPRESS` y pruebe primero `sqlcmd -S '.\SQLEXPRESS' -E -C`.
- **La tabla aparece vacía:** confirme que la aplicación está conectada a
  `db_leasing_vehicular` y que el script principal se ejecutó correctamente.

## Pantallas para el informe 8.6.2

La aplicación genera pantallas funcionales para capturar screenshots:

- Inicio de sesión.
- Clientes.
- Vehículos.
- Contratos.
- Pagos.
- Mantenimientos.
- Reportes basados en las vistas `vw_clientes_contratos`,
  `vw_vehiculos_seguros`, `vw_historial_mantenimiento` y
  `vw_resumen_pagos`.
