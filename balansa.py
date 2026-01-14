import serial
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector

# ================= SERIAL =================
PUERTO = "COM3"
BAUDIOS = 9600

# ================= MYSQL =================
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = ""
DB_NAME = "bascula_db_v2"

# ================= VARIABLES =================
arduino = None
usuario_id = None

peso_actual = 0.0
raw_actual = 0
tara_actual = 0
altura_actual = 0.0  # cm (última válida)

# ================= MYSQL =================
db = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASS
)
cursor = db.cursor()

cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
db.database = DB_NAME

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios(
 id INT AUTO_INCREMENT PRIMARY KEY,
 nombre VARCHAR(100),
 edad INT,
 telefono VARCHAR(20),
 sexo ENUM('Hombre','Mujer'),
 alergias ENUM('Sí','No') DEFAULT 'No',
 alergias_detalle VARCHAR(255)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS mediciones(
 id INT AUTO_INCREMENT PRIMARY KEY,
 usuario_id INT,
 raw BIGINT,
 tara BIGINT,
 peso FLOAT,
 estatura_cm FLOAT,
 imc FLOAT,
 clasificacion VARCHAR(50),
 dieta TEXT,
 fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

db.commit()

# ================= DIETA =================
def dieta_recomendada(imc, alergias, detalle):
    if imc < 18.5:
        dieta = "Alta en calorías y proteínas"
    elif imc < 25:
        dieta = "Balanceada"
    elif imc < 30:
        dieta = "Reducir grasas y carbohidratos"
    else:
        dieta = "Déficit calórico y ejercicio"

    if alergias == "Sí":
        dieta += f". Evitar: {detalle}"

    return dieta

# ================= SERIAL =================
def iniciar_serial():
    global arduino
    try:
        arduino = serial.Serial(PUERTO, BAUDIOS, timeout=1)
        time.sleep(3)
    except:
        messagebox.showerror("Error", "No se pudo abrir el puerto serial")

def leer_serial():
    global peso_actual, raw_actual, tara_actual, altura_actual

    while True:
        if arduino and arduino.in_waiting:
            linea = arduino.readline().decode(errors="ignore").strip()

            try:
                partes = linea.split("|")

                for p in partes:
                    p = p.strip()

                    if p.startswith("ALTURA:") and "cm" in p:
                        h = float(p.replace("ALTURA:", "").replace("cm", "").strip())
                        if 50 <= h <= 250:
                            altura_actual = h

                    elif p.startswith("RAW:"):
                        raw_actual = int(p.replace("RAW:", "").strip())

                    elif p.startswith("TARA:"):
                        tara_actual = int(p.replace("TARA:", "").strip())

                    elif p.startswith("PESO:") and "kg" in p:
                        w = float(p.replace("PESO:", "").replace("kg", "").strip())
                        if w >= 0:
                            peso_actual = w
            except:
                pass

# ================= FUNCIONES =================
def mostrar_alergias(event=None):
    if alergia_var.get() == "Sí":
        lbl_cual.grid(row=5, column=0)
        e_alergias.grid(row=5, column=1)
    else:
        lbl_cual.grid_remove()
        e_alergias.grid_remove()

def guardar_usuario():
    global usuario_id

    if not e_nombre.get():
        messagebox.showerror("Error", "Nombre obligatorio")
        return

    detalle = e_alergias.get() if alergia_var.get() == "Sí" else ""

    cursor.execute("""
        INSERT INTO usuarios(nombre,edad,telefono,sexo,alergias,alergias_detalle)
        VALUES(%s,%s,%s,%s,%s,%s)
    """, (
        e_nombre.get(),
        e_edad.get(),
        e_tel.get(),
        sexo_var.get(),
        alergia_var.get(),
        detalle
    ))
    db.commit()
    usuario_id = cursor.lastrowid
    messagebox.showinfo("OK", "Usuario guardado")

def guardar_medicion():
    if usuario_id is None:
        messagebox.showerror("Error", "Guarda primero el usuario")
        return

    if altura_actual < 50 or peso_actual <= 0:
        messagebox.showerror("Error", "Lecturas inválidas")
        return

    altura_m = altura_actual / 100
    imc = peso_actual / (altura_m ** 2)

    if imc < 18.5:
        clas = "Bajo peso"
    elif imc < 25:
        clas = "Normal"
    elif imc < 30:
        clas = "Sobrepeso"
    else:
        clas = "Obesidad"

    cursor.execute(
        "SELECT alergias, alergias_detalle FROM usuarios WHERE id=%s",
        (usuario_id,)
    )
    al, det = cursor.fetchone()

    dieta = dieta_recomendada(imc, al, det)

    cursor.execute("""
        INSERT INTO mediciones(
            usuario_id, raw, tara, peso, estatura_cm,
            imc, clasificacion, dieta
        )
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        usuario_id,
        raw_actual,
        tara_actual,
        peso_actual,
        altura_actual,
        imc,
        clas,
        dieta
    ))
    db.commit()

    lbl_imc.config(text=f"IMC: {imc:.2f}")
    lbl_estado.config(text=f"Estado: {clas}")
    lbl_dieta.config(text=f"Dieta: {dieta}")

def refrescar():
    lbl_raw.config(text=f"RAW: {raw_actual}")
    lbl_tara.config(text=f"TARA: {tara_actual}")
    lbl_peso.config(text=f"PESO: {peso_actual:.2f} kg")
    lbl_altura.config(text=f"ALTURA: {altura_actual:.1f} cm")
    root.after(300, refrescar)

# ================= UI =================
root = tk.Tk()
root.title("BÁSCULA PESO + ALTURA")
root.geometry("900x480")

frame_user = tk.LabelFrame(root, text="Usuario")
frame_user.place(x=10, y=10, width=380, height=300)

frame_data = tk.LabelFrame(root, text="Lecturas")
frame_data.place(x=400, y=10, width=480, height=300)

tk.Label(frame_user, text="Nombre").grid(row=0, column=0)
e_nombre = tk.Entry(frame_user); e_nombre.grid(row=0, column=1)

tk.Label(frame_user, text="Edad").grid(row=1, column=0)
e_edad = tk.Entry(frame_user); e_edad.grid(row=1, column=1)

tk.Label(frame_user, text="Teléfono").grid(row=2, column=0)
e_tel = tk.Entry(frame_user); e_tel.grid(row=2, column=1)

tk.Label(frame_user, text="Sexo").grid(row=3, column=0)
sexo_var = tk.StringVar(value="Hombre")
ttk.Combobox(frame_user, textvariable=sexo_var,
             values=["Hombre","Mujer"], state="readonly").grid(row=3, column=1)

tk.Label(frame_user, text="¿Alergias?").grid(row=4, column=0)
alergia_var = tk.StringVar(value="No")
cb = ttk.Combobox(frame_user, textvariable=alergia_var,
                  values=["Sí","No"], state="readonly")
cb.grid(row=4, column=1)
cb.bind("<<ComboboxSelected>>", mostrar_alergias)

lbl_cual = tk.Label(frame_user, text="¿Cuáles?")
e_alergias = tk.Entry(frame_user)

tk.Button(frame_user, text="Guardar Usuario",
          command=guardar_usuario).grid(row=6, column=0, columnspan=2, pady=10)

lbl_raw = tk.Label(frame_data, font=("Consolas",12)); lbl_raw.pack(anchor="w")
lbl_tara = tk.Label(frame_data, font=("Consolas",12)); lbl_tara.pack(anchor="w")
lbl_peso = tk.Label(frame_data, font=("Arial",26,"bold")); lbl_peso.pack(pady=10)
lbl_altura = tk.Label(frame_data, font=("Arial",18)); lbl_altura.pack()
lbl_imc = tk.Label(frame_data); lbl_imc.pack(anchor="w")
lbl_estado = tk.Label(frame_data); lbl_estado.pack(anchor="w")
lbl_dieta = tk.Label(frame_data, wraplength=450); lbl_dieta.pack()

tk.Button(frame_data, text="Guardar Medición",
          width=25, command=guardar_medicion).pack(pady=15)

# ================= INICIO =================
iniciar_serial()
threading.Thread(target=leer_serial, daemon=True).start()
refrescar()
root.mainloop()
