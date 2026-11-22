"""Chat sencillo sobre la API del RAG.

Cada pregunta se responde por separado: el historial se muestra en pantalla,
pero no se envía al modelo.
"""

import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8020")
EJEMPLOS = [
    "¿Cada cuánto se realiza el mantenimiento preventivo?",
    "¿Cuál es el inventario de seguridad?",
    "¿Qué hacer ante una condición insegura?",
]


def preguntar(pregunta, top_k, temperatura):
    """Devuelve (datos, None) o (None, mensaje de error)."""
    try:
        respuesta = requests.post(
            f"{API_URL}/preguntar",
            json={"pregunta": pregunta, "top_k": top_k, "temperatura": temperatura},
            timeout=360,
        )
    except requests.RequestException:
        return None, "No pude conectar con la API. Revisa los servicios con `make status`."
    if not respuesta.ok:
        try:
            detalle = respuesta.json().get("detail")
        except ValueError:
            detalle = respuesta.text
        return None, f"La API respondió {respuesta.status_code}: {detalle}"
    return respuesta.json(), None


def mostrar_detalle(datos):
    st.caption(
        f"{datos['tokens_entrada']} tokens de entrada · {datos['tokens_salida']} de salida · "
        f"recuperación {datos['tiempo_recuperacion'] * 1000:.0f} ms · "
        f"modelo {datos['duracion_ollama']:.1f} s · "
        f"K={datos['top_k']} · T={datos['temperatura']}"
    )
    with st.expander(f"Fuentes ({len(datos['fuentes'])})"):
        for fuente in datos["fuentes"]:
            st.markdown(
                f"**{fuente['fuente']}** · fragmento {fuente['fragmento']} · "
                f"similitud {fuente['similitud']:.3f}"
            )
            st.text(fuente["texto"])


def mostrar_mensaje(mensaje):
    with st.chat_message(mensaje["rol"]):
        if mensaje.get("error"):
            st.error(mensaje["error"])
            return
        st.markdown(mensaje["texto"])
        if mensaje.get("datos"):
            mostrar_detalle(mensaje["datos"])


st.set_page_config(page_title="Asistente TecnoFábrica", page_icon="🏭")
st.title("Asistente TecnoFábrica")
st.caption("Pregunta por las políticas de mantenimiento, inventarios y seguridad.")

mensajes = st.session_state.setdefault("mensajes", [])

with st.sidebar:
    st.header("Parámetros")
    top_k = st.slider("Fragmentos a recuperar (top_k)", 1, 10, 3)
    temperatura = st.slider("Temperatura", 0.0, 2.0, 0.2, 0.1)
    st.caption("Cada pregunta es independiente: el modelo no recuerda las anteriores.")
    if st.button("Limpiar chat", width="stretch"):
        mensajes.clear()

for mensaje in mensajes:
    mostrar_mensaje(mensaje)

pregunta = st.chat_input("Escribe tu pregunta")
if not mensajes and not pregunta:
    ejemplos = st.empty()
    with ejemplos.container():
        for ejemplo in EJEMPLOS:
            if st.button(ejemplo, width="stretch"):
                pregunta = ejemplo
    if pregunta:
        ejemplos.empty()

if pregunta and pregunta.strip():
    mensajes.append({"rol": "user", "texto": pregunta})
    mostrar_mensaje(mensajes[-1])
    with st.spinner("Buscando en los documentos..."):
        datos, error = preguntar(pregunta, top_k, temperatura)
    mensajes.append({
        "rol": "assistant",
        "texto": datos["respuesta"].strip() if datos else "",
        "datos": datos,
        "error": error,
    })
    mostrar_mensaje(mensajes[-1])
