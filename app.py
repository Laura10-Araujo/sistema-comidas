
import streamlit as st
import sqlite3
from datetime import date

conn = sqlite3.connect('comidas.db', check_same_thread=False)
c = conn.cursor()

def crear_tablas():
    c.execute('''CREATE TABLE IF NOT EXISTS Cliente (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS Producto (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        tipo TEXT,
        precio REAL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS Venta (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        fecha TEXT,
        tipo_cuenta TEXT,
        total REAL,
        abonado REAL,
        FOREIGN KEY (cliente_id) REFERENCES Cliente(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS DetalleVenta (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venta_id INTEGER,
        producto_id INTEGER,
        cantidad INTEGER,
        subtotal REAL,
        FOREIGN KEY (venta_id) REFERENCES Venta(id),
        FOREIGN KEY (producto_id) REFERENCES Producto(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS Abono (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venta_id INTEGER,
        fecha TEXT,
        monto REAL,
        FOREIGN KEY (venta_id) REFERENCES Venta(id)
    )''')
    conn.commit()

crear_tablas()

def obtener_clientes():
    return c.execute("SELECT id, nombre FROM Cliente").fetchall()

def obtener_productos(tipo):
    return c.execute("SELECT id, nombre, precio FROM Producto WHERE tipo = ?", (tipo,)).fetchall()

def registrar_cliente(nombre):
    c.execute("INSERT INTO Cliente (nombre) VALUES (?)", (nombre,))
    conn.commit()

def registrar_venta(cliente_id, tipo_cuenta, productos, fecha):
    total = sum(cant * precio for _, _, precio, cant in productos)
    c.execute("INSERT INTO Venta (cliente_id, fecha, tipo_cuenta, total, abonado) VALUES (?, ?, ?, ?, ?)",
              (cliente_id, fecha, tipo_cuenta, total, 0))
    venta_id = c.lastrowid
    for prod_id, _, precio, cantidad in productos:
        subtotal = cantidad * precio
        c.execute("INSERT INTO DetalleVenta (venta_id, producto_id, cantidad, subtotal) VALUES (?, ?, ?, ?)",
                  (venta_id, prod_id, cantidad, subtotal))
    conn.commit()

def obtener_deudas(cliente_id):
    ventas = c.execute("SELECT id, fecha, tipo_cuenta, total, abonado FROM Venta WHERE cliente_id = ?", (cliente_id,)).fetchall()
    pendientes = []
    for v in ventas:
        deuda = v[3] - v[4]
        if deuda > 0:
            pendientes.append((v[1], v[2], deuda))
    return pendientes

st.title("🍽️ Sistema Local de Comidas")

opcion = st.sidebar.selectbox("Acción", ["Registrar Venta", "Consultar Deuda", "Registrar Cliente", "Registrar Producto"])

if opcion == "Registrar Cliente":
    nombre = st.text_input("Nombre del cliente")
    if st.button("Registrar"):
        registrar_cliente(nombre)
        st.success("Cliente registrado.")

elif opcion == "Registrar Producto":
    nombre = st.text_input("Nombre del producto")
    tipo = st.selectbox("Tipo", ["frito", "bebida", "almuerzo", "otro"])
    precio = st.number_input("Precio", min_value=0.0)
    if st.button("Guardar producto"):
        c.execute("INSERT INTO Producto (nombre, tipo, precio) VALUES (?, ?, ?)", (nombre, tipo, precio))
        conn.commit()
        st.success("Producto guardado.")

elif opcion == "Registrar Venta":
    clientes = obtener_clientes()
    if not clientes:
        st.warning("Primero registra clientes.")
    else:
        cliente = st.selectbox("Cliente", clientes, format_func=lambda x: x[1])
        tipo_cuenta = st.radio("Tipo de cuenta", ["fritos_bebidas", "almuerzo"])
        productos = obtener_productos(tipo_cuenta.split("_")[0])
        seleccion = []
        for prod in productos:
            cantidad = st.number_input(f"{prod[1]} (${prod[2]})", min_value=0, key=prod[0])
            if cantidad > 0:
                seleccion.append((prod[0], prod[1], prod[2], cantidad))
        if st.button("Registrar Venta"):
            registrar_venta(cliente[0], tipo_cuenta, seleccion, str(date.today()))
            st.success("Venta registrada.")

elif opcion == "Consultar Deuda":
    clientes = obtener_clientes()
    cliente = st.selectbox("Cliente", clientes, format_func=lambda x: x[1])
    deudas = obtener_deudas(cliente[0])
    if deudas:
        for fecha, tipo, deuda in deudas:
            st.write(f"📅 {fecha} | 🧾 {tipo} | 💰 Debe: ${deuda:.2f}")
    else:
        st.success("No tiene deudas.")
