/* =====================================================================
   PROYECTO BASE DE DATOS - SISTEMA DE LEASING VEHICULAR (AutoLease Peru)
   Primera entrega: 8.1 DDL y 8.2 DML   |   Motor: SQL Server (SSMS)
   Ejecutar por bloques (seleccionar y F5) en el orden indicado.
   ===================================================================== */

/* =====================  8.1.1 CREATE  ===================== */
-- Creacion de la base de datos
CREATE DATABASE db_leasing_vehicular;
GO
-- Uso de la base de datos
USE db_leasing_vehicular;
GO

-- Tablas (primero las independientes, luego las que tienen FK)
CREATE TABLE sucursal (
    sucursal_id INT IDENTITY(1,1) NOT NULL,
    nombre      VARCHAR(60)  NOT NULL,
    direccion   VARCHAR(100) NOT NULL,
    ciudad      VARCHAR(40)  NOT NULL,
    telefono    VARCHAR(15)  NULL,
    CONSTRAINT pk_sucursal PRIMARY KEY (sucursal_id)
);

CREATE TABLE empleado (
    empleado_id       INT IDENTITY(1,1) NOT NULL,
    sucursal_id       INT NOT NULL,
    nombre            VARCHAR(80) NOT NULL,
    cargo             VARCHAR(40) NOT NULL,
    email             VARCHAR(80) NULL,
    telefono          VARCHAR(15) NULL,
    fecha_contratacion DATE NOT NULL,
    CONSTRAINT pk_empleado PRIMARY KEY (empleado_id),
    CONSTRAINT fk_empleado_sucursal FOREIGN KEY (sucursal_id) REFERENCES sucursal(sucursal_id)
);

CREATE TABLE cliente (
    cliente_id     INT IDENTITY(1,1) NOT NULL,
    nombre         VARCHAR(80) NOT NULL,
    email          VARCHAR(80) NULL,
    telefono       VARCHAR(15) NULL,
    direccion      VARCHAR(100) NULL,
    fecha_registro DATE NOT NULL,
    tipo_canal     VARCHAR(20) NOT NULL,
    conyuge_id     INT NULL,                      -- relacion 0..1 "esta_casado_con"
    CONSTRAINT pk_cliente PRIMARY KEY (cliente_id),
    CONSTRAINT fk_cliente_conyuge FOREIGN KEY (conyuge_id) REFERENCES cliente(cliente_id)
);

CREATE TABLE vehiculo (
    vehiculo_id      INT IDENTITY(1,1) NOT NULL,
    marca            VARCHAR(30) NOT NULL,
    modelo           VARCHAR(40) NOT NULL,
    anio             INT NOT NULL,
    precio           DECIMAL(10,2) NOT NULL,
    color            VARCHAR(20) NULL,
    kilometraje_actual INT NOT NULL,
    CONSTRAINT pk_vehiculo PRIMARY KEY (vehiculo_id)
);

CREATE TABLE proveedor (
    proveedor_id   INT IDENTITY(1,1) NOT NULL,
    nombre_empresa VARCHAR(80) NOT NULL,
    contacto       VARCHAR(60) NULL,
    telefono       VARCHAR(15) NULL,
    tipo_servicio  VARCHAR(40) NOT NULL,
    CONSTRAINT pk_proveedor PRIMARY KEY (proveedor_id)
);

CREATE TABLE contrato_leasing (
    contrato_id        INT IDENTITY(1,1) NOT NULL,
    cliente_id         INT NOT NULL,
    vehiculo_id        INT NOT NULL,
    empleado_id        INT NOT NULL,
    fecha_inicio       DATE NOT NULL,
    fecha_fin          DATE NOT NULL,
    cuota_mensual      DECIMAL(10,2) NOT NULL,
    kilometraje_permitido INT NOT NULL,
    CONSTRAINT pk_contrato PRIMARY KEY (contrato_id),
    CONSTRAINT fk_contrato_cliente  FOREIGN KEY (cliente_id)  REFERENCES cliente(cliente_id),
    CONSTRAINT fk_contrato_vehiculo FOREIGN KEY (vehiculo_id) REFERENCES vehiculo(vehiculo_id),
    CONSTRAINT fk_contrato_empleado FOREIGN KEY (empleado_id) REFERENCES empleado(empleado_id)
);

CREATE TABLE seguro (
    seguro_id          INT IDENTITY(1,1) NOT NULL,
    vehiculo_id        INT NOT NULL,
    compania_aseguradora VARCHAR(60) NOT NULL,
    numero_poliza      VARCHAR(20) NOT NULL,
    cobertura          VARCHAR(40) NOT NULL,
    prima_mensual      DECIMAL(10,2) NOT NULL,
    fecha_inicio       DATE NOT NULL,
    fecha_fin          DATE NOT NULL,
    CONSTRAINT pk_seguro PRIMARY KEY (seguro_id),
    CONSTRAINT uq_seguro_vehiculo UNIQUE (vehiculo_id),   -- relacion 1 a 1
    CONSTRAINT fk_seguro_vehiculo FOREIGN KEY (vehiculo_id) REFERENCES vehiculo(vehiculo_id)
);

CREATE TABLE mantenimiento (
    mantenimiento_id INT IDENTITY(1,1) NOT NULL,
    vehiculo_id      INT NOT NULL,
    proveedor_id     INT NOT NULL,
    fecha            DATE NOT NULL,
    tipo_servicio    VARCHAR(40) NOT NULL,
    costo            DECIMAL(10,2) NOT NULL,
    kilometraje      INT NOT NULL,
    estado           VARCHAR(20) NOT NULL,
    CONSTRAINT pk_mantenimiento PRIMARY KEY (mantenimiento_id),
    CONSTRAINT fk_mant_vehiculo  FOREIGN KEY (vehiculo_id)  REFERENCES vehiculo(vehiculo_id),
    CONSTRAINT fk_mant_proveedor FOREIGN KEY (proveedor_id) REFERENCES proveedor(proveedor_id)
);

CREATE TABLE pago (
    pago_id     INT IDENTITY(1,1) NOT NULL,
    contrato_id INT NOT NULL,
    monto       DECIMAL(10,2) NOT NULL,
    fecha_pago  DATE NOT NULL,
    metodo_pago VARCHAR(30) NOT NULL,
    estado      VARCHAR(20) NOT NULL,
    CONSTRAINT pk_pago PRIMARY KEY (pago_id),
    CONSTRAINT fk_pago_contrato FOREIGN KEY (contrato_id) REFERENCES contrato_leasing(contrato_id)
);

CREATE TABLE matricula (
    matricula_id  INT IDENTITY(1,1) NOT NULL,
    contrato_id   INT NOT NULL,
    numero_placa  VARCHAR(10) NOT NULL,
    fecha_emision DATE NOT NULL,
    estado        VARCHAR(20) NOT NULL,
    CONSTRAINT pk_matricula PRIMARY KEY (matricula_id),
    CONSTRAINT uq_matricula_contrato UNIQUE (contrato_id),  -- relacion 1 a 1
    CONSTRAINT fk_matricula_contrato FOREIGN KEY (contrato_id) REFERENCES contrato_leasing(contrato_id)
);
GO

/* =====================  8.2.1 INSERT  ===================== */
INSERT INTO sucursal (nombre, direccion, ciudad, telefono) VALUES
('Sede San Isidro', 'Av. Javier Prado 1250', 'Lima', '014567890'),
('Sede Miraflores', 'Av. Larco 800', 'Lima', '014561234'),
('Sede Arequipa',   'Av. Ejercito 450', 'Arequipa', '054223344');

INSERT INTO empleado (sucursal_id, nombre, cargo, email, telefono, fecha_contratacion) VALUES
(1, 'Luis Fernandez Rojas',  'Asesor comercial', 'lfernandez@autolease.pe', '987111001', '2024-02-10'),
(1, 'Marta Quispe Salas',    'Asesor comercial', 'mquispe@autolease.pe',    '987111002', '2024-05-15'),
(2, 'Jorge Paredes Diaz',    'Ejecutivo de ventas', 'jparedes@autolease.pe','987111003', '2023-11-01'),
(2, 'Carla Mendoza Luna',    'Gerente de sucursal', 'cmendoza@autolease.pe','987111004', '2022-08-20'),
(3, 'Diego Ramos Vega',      'Asesor comercial', 'dramos@autolease.pe',     '987111005', '2025-01-12'),
(3, 'Ana Torres Cruz',       'Ejecutivo de ventas', 'atorres@autolease.pe', '987111006', '2025-03-03');

INSERT INTO cliente (nombre, email, telefono, direccion, fecha_registro, tipo_canal) VALUES
('Carlos Gutierrez Perez',  'cgutierrez@mail.com', '999100001', 'Av. Arequipa 1020, Lima',  '2026-06-10', 'Web'),
('Rosa Medina Soto',        'rmedina@mail.com',    '999100002', 'Av. Arequipa 1020, Lima',  '2026-06-12', 'Presencial'),
('Pedro Villanueva Leon',   'pvillanueva@mail.com','999100003', 'Jr. Union 330, Lima',      '2026-06-20', 'Web'),
('Lucia Campos Rios',       'lcampos@mail.com',    '999100004', 'Av. Brasil 2100, Lima',    '2026-06-25', 'Redes sociales'),
('Miguel Huaman Torres',    'mhuaman@mail.com',    '999100005', 'Calle Mercaderes 55, Arequipa','2026-06-28','Presencial'),
('Elena Chavez Ruiz',       'echavez@mail.com',    '999100006', 'Calle Mercaderes 55, Arequipa','2026-06-28','Presencial'),
('Raul Salazar Vega',       'rsalazar@mail.com',   '999100007', 'Av. La Marina 900, Lima',  '2026-07-15', 'Web'),
('Sofia Delgado Mora',      'sdelgado@mail.com',   '999100008', 'Av. Pardo 450, Lima',      '2026-07-30', 'Redes sociales'),
('Andres Rivera Cano',      'arivera@mail.com',    '999100009', 'Av. Dolores 120, Arequipa','2026-08-20', 'Web'),
('Patricia Lopez Nunez',    'plopez@mail.com',     '999100010', 'Av. Benavides 1500, Lima', '2026-08-28', 'Presencial');

-- Relacion "esta_casado_con" (0..1) mediante UPDATE
UPDATE cliente SET conyuge_id = 2 WHERE cliente_id = 1;
UPDATE cliente SET conyuge_id = 1 WHERE cliente_id = 2;
UPDATE cliente SET conyuge_id = 6 WHERE cliente_id = 5;
UPDATE cliente SET conyuge_id = 5 WHERE cliente_id = 6;

INSERT INTO vehiculo (marca, modelo, anio, precio, color, kilometraje_actual) VALUES
('Toyota',  'Corolla',  2026, 22500.00, 'Blanco', 1200),
('Hyundai', 'Tucson',   2026, 28900.00, 'Gris',   2500),
('Kia',     'Rio',      2025, 16500.00, 'Rojo',   8000),
('Toyota',  'RAV4',     2026, 34500.00, 'Negro',  1500),
('Suzuki',  'Vitara',   2025, 21000.00, 'Azul',   6500),
('Nissan',  'Kicks',    2026, 24800.00, 'Blanco', 900),
('Mazda',   'CX-30',    2026, 23900.00, 'Plata',  600),
('Chevrolet','Tracker', 2026, 29900.00, 'Negro',  300),
('Kia',     'Sportage', 2025, 31500.00, 'Gris',   4000),
('Honda',   'HR-V',     2025, 27500.00, 'Rojo',   3500);

INSERT INTO proveedor (nombre_empresa, contacto, telefono, tipo_servicio) VALUES
('AutoService Peru SAC',  'Hector Salinas', '014001001', 'Mantenimiento preventivo'),
('Llantas y Frenos EIRL', 'Julia Vargas',   '014001002', 'Frenos y llantas'),
('Taller Motor Plus',     'Oscar Pinedo',   '014001003', 'Mecanica general'),
('Lubricantes Andinos',   'Rita Camacho',   '014001004', 'Cambio de aceite');

INSERT INTO contrato_leasing (cliente_id, vehiculo_id, empleado_id, fecha_inicio, fecha_fin, cuota_mensual, kilometraje_permitido) VALUES
(1, 1, 1, '2026-07-01', '2029-07-01', 520.00, 30000),
(3, 2, 2, '2026-07-05', '2029-07-05', 610.00, 30000),
(4, 3, 3, '2026-07-10', '2029-07-10', 480.00, 25000),
(5, 4, 1, '2026-07-20', '2029-07-20', 750.00, 36000),
(7, 5, 4, '2026-08-03', '2029-08-03', 560.00, 30000),
(8, 6, 5, '2026-08-15', '2029-08-15', 690.00, 30000),
(9, 7, 2, '2026-09-01', '2029-09-01', 430.00, 25000),
(10,8, 6, '2026-09-12', '2029-09-12', 820.00, 36000);

INSERT INTO seguro (vehiculo_id, compania_aseguradora, numero_poliza, cobertura, prima_mensual, fecha_inicio, fecha_fin) VALUES
(1,  'Rimac Seguros', 'POL-0001', 'Todo riesgo', 85.00,  '2026-07-01', '2027-07-01'),
(2,  'Pacifico Seguros','POL-0002','Todo riesgo', 98.00,  '2026-07-05', '2027-07-05'),
(3,  'La Positiva',   'POL-0003', 'Todo riesgo', 72.00,  '2026-07-10', '2027-07-10'),
(4,  'Rimac Seguros', 'POL-0004', 'Todo riesgo', 120.00, '2026-07-20', '2027-07-20'),
(5,  'Mapfre',        'POL-0005', 'Todo riesgo', 80.00,  '2026-08-03', '2027-08-03'),
(6,  'Pacifico Seguros','POL-0006','Todo riesgo', 92.00,  '2026-08-15', '2027-08-15'),
(7,  'La Positiva',   'POL-0007', 'Todo riesgo', 78.00,  '2026-09-01', '2027-09-01'),
(8,  'Rimac Seguros', 'POL-0008', 'Todo riesgo', 105.00, '2026-09-12', '2027-09-12'),
(9,  'Mapfre',        'POL-0009', 'Responsabilidad civil', 55.00, '2026-06-01', '2027-06-01'),
(10, 'Mapfre',        'POL-0010', 'Responsabilidad civil', 52.00, '2026-06-01', '2027-06-01');

INSERT INTO mantenimiento (vehiculo_id, proveedor_id, fecha, tipo_servicio, costo, kilometraje, estado) VALUES
(1, 1, '2026-08-20', 'Revision general',   120.00, 3000, 'Finalizado'),
(3, 4, '2026-08-25', 'Cambio de aceite',    60.00, 9500, 'Finalizado'),
(2, 2, '2026-09-05', 'Cambio de frenos',   210.00, 5000, 'Finalizado'),
(4, 1, '2026-09-18', 'Revision general',   130.00, 3500, 'Finalizado'),
(5, 3, '2026-09-25', 'Alineamiento',        90.00, 8000, 'En proceso'),
(6, 4, '2026-09-30', 'Cambio de aceite',    65.00, 2500, 'Programado');

INSERT INTO pago (contrato_id, monto, fecha_pago, metodo_pago, estado) VALUES
(1, 520.00, '2026-07-01', 'Transferencia', 'Pagado'),
(1, 520.00, '2026-08-01', 'Transferencia', 'Pagado'),
(1, 520.00, '2026-09-01', 'Transferencia', 'Pagado'),
(2, 610.00, '2026-07-05', 'Tarjeta', 'Pagado'),
(2, 610.00, '2026-08-05', 'Tarjeta', 'Pagado'),
(2, 610.00, '2026-09-05', 'Tarjeta', 'Pagado'),
(3, 480.00, '2026-07-10', 'Debito automatico', 'Pagado'),
(3, 480.00, '2026-08-10', 'Debito automatico', 'Pagado'),
(3, 480.00, '2026-09-10', 'Debito automatico', 'Pendiente'),
(4, 750.00, '2026-07-20', 'Transferencia', 'Pagado'),
(4, 750.00, '2026-08-20', 'Transferencia', 'Pagado'),
(4, 750.00, '2026-09-20', 'Transferencia', 'Atrasado'),
(5, 560.00, '2026-08-03', 'Tarjeta', 'Pagado'),
(5, 560.00, '2026-09-03', 'Tarjeta', 'Pagado'),
(6, 690.00, '2026-08-15', 'Transferencia', 'Pagado'),
(6, 690.00, '2026-09-15', 'Transferencia', 'Pagado'),
(7, 430.00, '2026-09-01', 'Debito automatico', 'Pagado'),
(8, 820.00, '2026-09-12', 'Tarjeta', 'Pagado');

INSERT INTO matricula (contrato_id, numero_placa, fecha_emision, estado) VALUES
(1, 'BKA-123', '2026-07-08', 'Vigente'),
(2, 'BKB-456', '2026-07-12', 'Vigente'),
(3, 'BKC-789', '2026-07-17', 'Vigente'),
(4, 'BKD-321', '2026-07-27', 'Vigente'),
(5, 'BKE-654', '2026-08-10', 'Vigente'),
(6, 'BKF-987', '2026-08-22', 'Vigente'),
(7, 'BKG-147', '2026-09-08', 'Vigente'),
(8, 'BKH-258', '2026-09-19', 'En tramite');
GO

-- Verificacion
SELECT * FROM cliente;
SELECT * FROM contrato_leasing;
GO

/* =====================  8.1.3 ALTER  ===================== */
-- ADD columna
ALTER TABLE cliente ADD dni VARCHAR(8) NULL;
-- ALTER COLUMN (cambiar tipo / nulabilidad)
ALTER TABLE cliente ALTER COLUMN dni CHAR(8) NULL;
GO
UPDATE cliente SET dni = RIGHT('00000000' + CAST(70000000 + cliente_id AS VARCHAR(8)), 8);
GO
ALTER TABLE cliente ALTER COLUMN dni CHAR(8) NOT NULL;
-- ADD CONSTRAINT: unique, check, default, foreign key (ya existe), primary key
ALTER TABLE cliente  ADD CONSTRAINT uq_cliente_dni UNIQUE (dni);
ALTER TABLE vehiculo ADD CONSTRAINT ck_vehiculo_precio CHECK (precio > 0);
ALTER TABLE pago     ADD CONSTRAINT df_pago_estado DEFAULT 'Pendiente' FOR estado;
ALTER TABLE contrato_leasing ADD CONSTRAINT ck_contrato_fechas CHECK (fecha_fin > fecha_inicio);
ALTER TABLE contrato_leasing ADD CONSTRAINT ck_contrato_cuota CHECK (cuota_mensual > 0);
GO
-- Ejemplo de PRIMARY KEY y FOREIGN KEY con ALTER sobre tabla de prueba
CREATE TABLE tabla_prueba (id INT NOT NULL, descripcion VARCHAR(50), sucursal_id INT);
ALTER TABLE tabla_prueba ADD CONSTRAINT pk_prueba PRIMARY KEY (id);
ALTER TABLE tabla_prueba ADD CONSTRAINT fk_prueba_sucursal FOREIGN KEY (sucursal_id) REFERENCES sucursal(sucursal_id);
-- DROP CONSTRAINT
ALTER TABLE tabla_prueba DROP CONSTRAINT fk_prueba_sucursal;
-- DROP COLUMN
ALTER TABLE tabla_prueba DROP COLUMN descripcion;
GO

/* =====================  8.1.2 TRUNCATE  ===================== */
INSERT INTO tabla_prueba (id, sucursal_id) VALUES (1, 1), (2, 2), (3, 3);
SELECT * FROM tabla_prueba;
TRUNCATE TABLE tabla_prueba;          -- elimina todos los registros, conserva la estructura
SELECT * FROM tabla_prueba;
GO

/* =====================  8.1.4 DROP  ===================== */
DROP TABLE tabla_prueba;              -- elimina la tabla completa (estructura y datos)
GO

/* =====================  8.2.2 DELETE  ===================== */
-- Registro de prueba para eliminarlo sin afectar el historial
INSERT INTO proveedor (nombre_empresa, contacto, telefono, tipo_servicio)
VALUES ('Proveedor Prueba SAC', 'Contacto Prueba', '000000000', 'Pruebas');
DELETE FROM proveedor WHERE nombre_empresa = 'Proveedor Prueba SAC';
GO

/* =====================  8.2.3 UPDATE  ===================== */
-- Corregir un correo erroneo
UPDATE cliente SET email = 'carlos.gutierrez@mail.com' WHERE cliente_id = 1;
-- Actualizar el estado de un pago pendiente
UPDATE pago SET estado = 'Pagado' WHERE contrato_id = 3 AND fecha_pago = '2026-09-10';
-- Aumentar 5% el costo de mantenimientos programados (operador aritmetico)
UPDATE mantenimiento SET costo = costo * 1.05 WHERE estado = 'Programado';
GO

/* =====================  8.2.4 SELECT  ===================== */
/* ---- 8.2.4.1 Consultas simples (operadores aritmeticos, relacionales, logicos) ---- */
-- 1) Vehiculos del 2026 con precio mayor a 25000, ordenados de mayor a menor
SELECT vehiculo_id, marca, modelo, precio
FROM vehiculo
WHERE anio = 2026 AND precio > 25000
ORDER BY precio DESC;

-- 2) Cuota mensual con IGV (18%) de contratos con cuota entre 500 y 800
SELECT contrato_id, cuota_mensual, cuota_mensual * 1.18 AS cuota_con_igv
FROM contrato_leasing
WHERE cuota_mensual BETWEEN 500 AND 800 OR kilometraje_permitido >= 36000
ORDER BY cuota_mensual;

/* ---- 8.2.4.2 Subconsultas mono registro ---- */
-- 1) Vehiculo mas caro
SELECT marca, modelo, precio FROM vehiculo
WHERE precio = (SELECT MAX(precio) FROM vehiculo);

-- 2) Contratos con cuota superior al promedio
SELECT contrato_id, cuota_mensual FROM contrato_leasing
WHERE cuota_mensual > (SELECT AVG(cuota_mensual) FROM contrato_leasing);

-- 3) Pagos de monto menor al maximo pago registrado y mayor al minimo
SELECT pago_id, monto FROM pago
WHERE monto < (SELECT MAX(monto) FROM pago) AND monto > (SELECT MIN(monto) FROM pago);

/* ---- 8.2.4.3 Subconsultas multi registro (IN, ANY, ALL, EXISTS) ---- */
-- 1) Clientes que tienen contrato de leasing
SELECT cliente_id, nombre FROM cliente
WHERE cliente_id IN (SELECT cliente_id FROM contrato_leasing);

-- 2) Vehiculos que aun no estan en ningun contrato (disponibles)
SELECT vehiculo_id, marca, modelo FROM vehiculo
WHERE vehiculo_id NOT IN (SELECT vehiculo_id FROM contrato_leasing);

-- 3) Vehiculos con precio mayor a todos los vehiculos Kia
SELECT marca, modelo, precio FROM vehiculo
WHERE precio > ALL (SELECT precio FROM vehiculo WHERE marca = 'Kia');

/* ---- 8.2.4.4 Subconsultas multi columna ---- */
-- 1) Contratos con la misma cuota y km permitido que el contrato 1 o 5 (par de columnas)
SELECT contrato_id, cuota_mensual, kilometraje_permitido FROM contrato_leasing
WHERE EXISTS (SELECT 1 FROM contrato_leasing c2
              WHERE c2.contrato_id IN (1,5)
              AND c2.cuota_mensual = contrato_leasing.cuota_mensual
              AND c2.kilometraje_permitido = contrato_leasing.kilometraje_permitido);

-- 2) Empleado y sucursal de los empleados de cargo Asesor comercial (tabla derivada)
SELECT t.empleado_id, t.nombre, t.sucursal_id
FROM (SELECT empleado_id, nombre, sucursal_id FROM empleado WHERE cargo = 'Asesor comercial') AS t
WHERE t.sucursal_id IN (1, 3);

-- 3) Ultimo pago (fecha y monto) por contrato
SELECT p.contrato_id, p.fecha_pago, p.monto
FROM pago p
WHERE p.fecha_pago = (SELECT MAX(p2.fecha_pago) FROM pago p2 WHERE p2.contrato_id = p.contrato_id)
ORDER BY p.contrato_id;

/* ---- 8.2.4.5 Consultas combinadas INNER JOIN ---- */
-- 1) Contrato con cliente
SELECT c.contrato_id, cl.nombre AS cliente, c.fecha_inicio, c.cuota_mensual
FROM contrato_leasing c
INNER JOIN cliente cl ON c.cliente_id = cl.cliente_id;

-- 2) Contrato con vehiculo y cliente
SELECT c.contrato_id, cl.nombre AS cliente, v.marca, v.modelo, c.cuota_mensual
FROM contrato_leasing c
INNER JOIN cliente cl ON c.cliente_id = cl.cliente_id
INNER JOIN vehiculo v ON c.vehiculo_id = v.vehiculo_id
ORDER BY c.contrato_id;

-- 3) Empleado, sucursal y contratos gestionados
SELECT e.nombre AS empleado, s.nombre AS sucursal, c.contrato_id
FROM empleado e
INNER JOIN sucursal s ON e.sucursal_id = s.sucursal_id
INNER JOIN contrato_leasing c ON c.empleado_id = e.empleado_id;

-- 4) Pagos con contrato y cliente
SELECT p.pago_id, cl.nombre AS cliente, p.monto, p.fecha_pago, p.estado
FROM pago p
INNER JOIN contrato_leasing c ON p.contrato_id = c.contrato_id
INNER JOIN cliente cl ON c.cliente_id = cl.cliente_id
WHERE p.estado <> 'Pagado';

-- 5) Mantenimientos con vehiculo y proveedor
SELECT m.mantenimiento_id, v.marca, v.modelo, pr.nombre_empresa, m.tipo_servicio, m.costo
FROM mantenimiento m
INNER JOIN vehiculo v ON m.vehiculo_id = v.vehiculo_id
INNER JOIN proveedor pr ON m.proveedor_id = pr.proveedor_id
ORDER BY m.fecha;

-- 6) Vehiculo, seguro, matricula y cliente
SELECT cl.nombre AS cliente, v.marca, v.modelo, m.numero_placa, s.compania_aseguradora, s.numero_poliza
FROM contrato_leasing c
INNER JOIN cliente cl   ON c.cliente_id = cl.cliente_id
INNER JOIN vehiculo v   ON c.vehiculo_id = v.vehiculo_id
INNER JOIN matricula m  ON m.contrato_id = c.contrato_id
INNER JOIN seguro s     ON s.vehiculo_id = v.vehiculo_id;

/* =====================  8.2.5 Funciones de columna  ===================== */
SELECT COUNT(*)                     AS total_contratos      FROM contrato_leasing;
SELECT COUNT(DISTINCT tipo_canal)   AS canales_distintos    FROM cliente;
SELECT SUM(monto)                   AS recaudado_total      FROM pago WHERE estado = 'Pagado';
SELECT AVG(precio)                  AS precio_promedio      FROM vehiculo;
SELECT MIN(cuota_mensual) AS cuota_minima, MAX(cuota_mensual) AS cuota_maxima FROM contrato_leasing;
-- GROUP BY + HAVING
SELECT c.contrato_id, SUM(p.monto) AS total_pagado
FROM pago p INNER JOIN contrato_leasing c ON p.contrato_id = c.contrato_id
WHERE p.estado = 'Pagado'
GROUP BY c.contrato_id
HAVING SUM(p.monto) > 1000;

/* =====================  8.2.6 Funciones de fecha  ===================== */
SELECT GETDATE() AS fecha_actual;
SELECT contrato_id, YEAR(fecha_inicio) AS anio, MONTH(fecha_inicio) AS mes, DAY(fecha_inicio) AS dia FROM contrato_leasing;
SELECT contrato_id, DATEDIFF(MONTH, fecha_inicio, fecha_fin) AS duracion_meses FROM contrato_leasing;
SELECT contrato_id, DATEADD(MONTH, 1, fecha_inicio) AS primera_renovacion FROM contrato_leasing;
SELECT DATENAME(MONTH, fecha_pago) AS mes, COUNT(*) AS cantidad_pagos, SUM(monto) AS total
FROM pago GROUP BY DATENAME(MONTH, fecha_pago), MONTH(fecha_pago) ORDER BY MONTH(fecha_pago);
SELECT FORMAT(fecha_pago, 'dd/MM/yyyy') AS fecha_formato FROM pago;
GO

/* =====================  8.3 DCL ===================== */
/* Usuario de demostracion para los ejemplos DCL.
   Ejecutar esta parte con permisos de administrador de SQL Server. */
USE master;
GO

IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = 'estudiante1')
BEGIN
    CREATE LOGIN estudiante1
    WITH PASSWORD = 'Password123!';
END;
GO

USE db_leasing_vehicular;
GO

IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'estudiante1')
BEGIN
    CREATE USER estudiante1 FOR LOGIN estudiante1;
END;
GO

/* =====================  8.3.1 REVOKE ===================== */
-- Primero se concede UPDATE para poder demostrar su eliminacion.
GRANT UPDATE ON dbo.pago TO estudiante1;
GO

-- REVOKE elimina un permiso existente del usuario.
REVOKE UPDATE ON dbo.pago FROM estudiante1;
GO

/* =====================  8.3.2 GRANT ===================== */
-- GRANT da acceso a un objeto de la base de datos.
GRANT SELECT ON dbo.cliente TO estudiante1;
GO

/* =====================  8.3.3 DENY ===================== */
-- DENY bloquea explicitamente el acceso del usuario al objeto indicado.
DENY DELETE ON dbo.contrato_leasing TO estudiante1;
GO

/* =====================  8.4 Procedimientos almacenados ===================== */

/* 8.4.1 Registrar un nuevo cliente */
CREATE PROCEDURE dbo.usp_registrar_cliente
    @nombre         VARCHAR(80),
    @email          VARCHAR(80),
    @telefono       VARCHAR(15),
    @direccion      VARCHAR(100),
    @fecha_registro DATE,
    @tipo_canal     VARCHAR(20),
    @dni            CHAR(8)
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO dbo.cliente
        (nombre, email, telefono, direccion, fecha_registro, tipo_canal, dni)
    VALUES
        (@nombre, @email, @telefono, @direccion, @fecha_registro, @tipo_canal, @dni);
END;
GO

-- Ejemplo: registrar un cliente nuevo.
EXEC dbo.usp_registrar_cliente
    @nombre = 'Ana Torres Mendoza',
    @email = 'ana.torres@mail.com',
    @telefono = '987555444',
    @direccion = 'Av. Arequipa 1500',
    @fecha_registro = '2026-10-30',
    @tipo_canal = 'Web',
    @dni = '71234567';
GO

/* 8.4.2 Buscar contratos de un cliente */
CREATE PROCEDURE dbo.usp_buscar_contratos_cliente
    @cliente_id INT
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        c.contrato_id,
        cl.nombre AS cliente,
        c.fecha_inicio,
        c.fecha_fin,
        c.cuota_mensual,
        c.kilometraje_permitido
    FROM dbo.contrato_leasing AS c
    INNER JOIN dbo.cliente AS cl
        ON cl.cliente_id = c.cliente_id
    WHERE c.cliente_id = @cliente_id;
END;
GO

-- Ejemplo: consultar los contratos del cliente con ID 1.
EXEC dbo.usp_buscar_contratos_cliente @cliente_id = 1;
GO

/* 8.4.3 Listar pagos de un contrato */
CREATE PROCEDURE dbo.usp_listar_pagos_contrato
    @contrato_id INT
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        pago_id,
        contrato_id,
        monto,
        fecha_pago,
        metodo_pago,
        estado
    FROM dbo.pago
    WHERE contrato_id = @contrato_id
    ORDER BY fecha_pago;
END;
GO

-- Ejemplo: listar los pagos del contrato con ID 1.
EXEC dbo.usp_listar_pagos_contrato @contrato_id = 1;
GO

/* 8.4.4 Calcular el total pagado de un contrato */
CREATE PROCEDURE dbo.usp_calcular_total_pagado
    @contrato_id INT
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        @contrato_id AS contrato_id,
        COALESCE(SUM(monto), 0) AS total_pagado
    FROM dbo.pago
    WHERE contrato_id = @contrato_id
      AND estado = 'Pagado';
END;
GO

-- Ejemplo: calcular el total pagado del contrato con ID 1.
EXEC dbo.usp_calcular_total_pagado @contrato_id = 1;
GO

/* =====================  8.5 Vistas (SQL Server) ===================== */
USE db_leasing_vehicular;
GO

/* 8.5.1 Clientes y sus contratos */
CREATE VIEW dbo.vw_clientes_contratos
AS
SELECT
    cl.nombre AS cliente,
    c.contrato_id,
    c.fecha_inicio,
    c.fecha_fin,
    c.cuota_mensual
FROM dbo.cliente AS cl
INNER JOIN dbo.contrato_leasing AS c
    ON c.cliente_id = cl.cliente_id;
GO

-- Ejemplo de consulta de la vista de clientes y contratos.
SELECT * FROM dbo.vw_clientes_contratos;
GO

/* 8.5.2 Vehiculos y su informacion de seguro */
CREATE VIEW dbo.vw_vehiculos_seguros
AS
SELECT
    v.marca,
    v.modelo,
    s.compania_aseguradora AS aseguradora,
    s.numero_poliza,
    s.cobertura
FROM dbo.vehiculo AS v
INNER JOIN dbo.seguro AS s
    ON s.vehiculo_id = v.vehiculo_id;
GO

-- Ejemplo de consulta de la vista de vehiculos y seguros.
SELECT * FROM dbo.vw_vehiculos_seguros;
GO

/* 8.5.3 Historial de mantenimiento */
CREATE VIEW dbo.vw_historial_mantenimiento
AS
SELECT
    CONCAT(v.marca, ' ', v.modelo) AS vehiculo,
    pr.nombre_empresa AS proveedor,
    m.tipo_servicio,
    m.fecha,
    m.costo,
    m.estado
FROM dbo.mantenimiento AS m
INNER JOIN dbo.vehiculo AS v
    ON v.vehiculo_id = m.vehiculo_id
INNER JOIN dbo.proveedor AS pr
    ON pr.proveedor_id = m.proveedor_id;
GO

-- Ejemplo de consulta de la vista de mantenimiento.
SELECT * FROM dbo.vw_historial_mantenimiento;
GO

/* 8.5.4 Resumen de pagos por contrato */
CREATE VIEW dbo.vw_resumen_pagos
AS
SELECT
    c.contrato_id,
    COUNT(p.pago_id) AS cantidad_pagos,
    COALESCE(SUM(CASE WHEN p.estado = 'Pagado' THEN p.monto ELSE 0 END), 0) AS total_pagado
FROM dbo.contrato_leasing AS c
LEFT JOIN dbo.pago AS p
    ON p.contrato_id = c.contrato_id
GROUP BY c.contrato_id;
GO

-- Ejemplo de consulta del resumen de pagos.
SELECT * FROM dbo.vw_resumen_pagos;
GO

/* =====================  8.6.1 Conexión a IDE =====================

La base de datos db_leasing_vehicular puede administrarse y consultarse
desde Visual Studio Code, utilizado como entorno de desarrollo integrado
(IDE). Para ello, primero se debe instalar SQL Server Express en el equipo.
Durante la instalación se habilita la instancia local SQLEXPRESS, que
funciona como el motor de base de datos para este proyecto. El servicio
correspondiente debe estar iniciado antes de intentar establecer la conexión.

En Visual Studio Code se instala y habilita la extensión oficial
"SQL Server (mssql)". Esta extensión permite crear perfiles de conexión,
abrir editores SQL, ejecutar instrucciones y consultar los resultados
directamente desde el IDE. Después de instalarla, se abre la paleta de
comandos con Ctrl+Shift+P y se selecciona "MS SQL: Connect" o la opción
equivalente para crear un nuevo perfil de conexión.

Para este proyecto, el nombre del servidor es .\SQLEXPRESS. Esta notacion
identifica la instancia SQLEXPRESS instalada en el equipo local. En el
perfil se selecciona Windows Authentication (autenticacion de Windows).
Con este metodo se utilizan las credenciales de la cuenta actual de
Windows, por lo que no es necesario escribir un usuario y contraseña de
SQL Server. Si el IDE solicita confiar en el certificado del servidor
local, se habilita la opcion "Trust Server Certificate", ya que la
instancia de desarrollo puede utilizar un certificado local no reconocido
por una entidad certificadora publica.

Una vez establecida la conexion, se selecciona db_leasing_vehicular como
base de datos activa. El archivo db_leasing_vehicular.sql se puede abrir
desde el explorador de VS Code. Para ejecutarlo, el archivo debe estar
abierto como editor SQL y el cursor debe encontrarse dentro del editor.
Luego se selecciona una parte del script o se ejecuta todo el archivo
mediante el boton de ejecucion, la opcion "Execute Query", la tecla F5 o
el comando "MS SQL: Execute Query". Las instrucciones separadas por GO
se ejecutan como lotes independientes, lo que permite crear tablas,
procedimientos y vistas en el orden establecido.

Otra alternativa es utilizar sqlcmd desde una terminal de Windows. Con
autenticacion integrada se puede ejecutar el script indicando la instancia
local mediante el comando conceptual "sqlcmd -S .\SQLEXPRESS -E -C".
El parametro -S identifica el servidor, -E utiliza Windows Authentication
y -C acepta el certificado del servidor local. Para ejecutar un archivo
completo, se puede indicar su ruta con la opcion -i. La cuenta utilizada
debe tener permisos suficientes para crear la base de datos y sus objetos.

Finalmente, la base de datos puede consultarse desde el editor SQL de
VS Code o desde sqlcmd mediante instrucciones SQL. Por ejemplo, una
consulta SELECT sobre dbo.cliente permite revisar los clientes registrados,
mientras que un JOIN entre dbo.contrato_leasing y dbo.cliente permite
obtener los contratos asociados a cada cliente. Tambien se pueden ejecutar
los procedimientos almacenados con EXEC y consultar las vistas creadas
en la seccion 8.5. De esta manera, VS Code proporciona una interfaz para
desarrollar y verificar el sistema, mientras SQL Server Express procesa
las instrucciones y administra la informacion almacenada.
====================================================================== */