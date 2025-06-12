
import streamlit as st
import pandas as pd
import datetime
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# --- CARGAR VARIABLES DE ENTORNO ---
load_dotenv()

# --- CONFIGURACIÓN ---
SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQyl_p631ZurF6GoT3zP1Ir1-46x5kqDFKRMBnqFOfoHcvyaEJul4alywGjfzkWkfspOYLERsd-Cxis/"
    "pub?output=csv&gid=0"
)
EMAIL_SENDER = "alertasmercurio@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# --- LÓGICA DE FECHAS ---
def fecha_vencimiento(fecha_inicio, dias_habiles=15):
    fecha = fecha_inicio
    cuenta = 0
    while cuenta < dias_habiles:
        fecha += datetime.timedelta(days=1)
        if fecha.weekday() < 5:
            cuenta += 1
    return fecha

def dias_habiles_restantes(fecha_venc):
    hoy = datetime.datetime.now()
    delta = fecha_venc - hoy
    dias = 0
    for i in range(delta.days + 1):
        if (hoy + datetime.timedelta(days=i)).weekday() < 5:
            dias += 1
    return dias - 1

# --- ENVÍO DE CORREO ---
def enviar_alerta(destino, nombre, num_tarea, fecha_limite):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = destino
    msg["Subject"] = f"⚠️ Alerta: Tarea #{num_tarea} casi vence"
    texto = f"""Estimado/a {nombre},

Le recordamos que la tarea #{num_tarea} está próxima a vencer (fecha límite: {fecha_limite}).
Por favor entréguela a la brevedad.

Saludos cordiales,
Sistema de Alertas Automáticas
"""
    msg.attach(MIMEText(texto, "plain"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as serv:
        serv.starttls()
        serv.login(EMAIL_SENDER, EMAIL_PASSWORD)
        serv.send_message(msg)

# --- PROCESAMIENTO ---
def revisar_y_alertar():
    df = pd.read_csv(SHEET_URL)
    df["fecha de asignación"] = pd.to_datetime(df["fecha de asignación"])
    enviados = []

    for _, fila in df.iterrows():
        if str(fila.entregada).strip().upper() == "NO":
            fv = fecha_vencimiento(fila["fecha de asignación"])
            dias_rest = dias_habiles_restantes(fv)
            if dias_rest <= 2:
                enviar_alerta(
                    fila["correo"],
                    fila["responsable"],
                    fila["# de tarea"],
                    fv.date()
                )
                enviados.append(f"Tarea #{fila['# de tarea']} a {fila['responsable']}")

    return enviados

# --- INTERFAZ STREAMLIT ---
st.title("📩 Sistema de Alertas por Correo")

ejecutar = False
hora_actual = datetime.datetime.now().time()
if hora_actual.hour == 8 and hora_actual.minute == 0:
    ejecutar = True

if st.button("🔔 Enviar alertas ahora"):
    ejecutar = True

if ejecutar:
    resultado = revisar_y_alertar()
    if resultado:
        st.success("✅ Alertas enviadas:")
        for r in resultado:
            st.write("•", r)
    else:
        st.info("No hay tareas por alertar.")
