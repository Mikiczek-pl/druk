import streamlit as st
from PIL import Image
import os
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import mm

st.set_page_config(page_title="Stwórz okładkę Blu-ray", layout="wide")
st.title("🎬 Stwórz okładkę Blu-ray")

if "covers" not in st.session_state:
    st.session_state.covers = []
if "quantities" not in st.session_state:
    st.session_state.quantities = {}

# --- Oblicz i pokaż liczbę okładek ---
st.markdown("---")
total_covers = sum(st.session_state.quantities.get(cover["name"], 1) for cover in st.session_state.covers)
missing_to_full = (3 - (total_covers % 3)) % 3

highlight_style = "font-size:24px; font-weight:bold; margin-bottom:10px;"
st.markdown(f"<div style='{highlight_style}'>🧮 Liczba wszystkich okładek: {total_covers}</div>", unsafe_allow_html=True)
if missing_to_full > 0:
    st.warning(f"Brakuje {missing_to_full} okładki, aby dopełnić pełny komplet (wielokrotność 3).")
else:
    st.success("Liczba okładek to pełny komplet.")

# --- Upload ---
uploaded_files = st.file_uploader("Wgraj obrazy (JPG, PNG)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    for file in uploaded_files:
        name = file.name
        if name not in [c['name'] for c in st.session_state.covers]:
            image = Image.open(file).convert("RGB")
            st.session_state.covers.append({"name": name, "image": image})
            st.session_state.quantities[name] = 1

# --- Podgląd ---
st.markdown("---")
st.markdown("## 📂 Wybrane okładki")

for cover in st.session_state.covers:
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image(cover["image"], use_column_width=True)
    with col2:
        qty = st.number_input(f"Ilość kopii ({cover['name']}):", min_value=1, step=1, value=st.session_state.quantities.get(cover['name'], 1), key=f"qty_{cover['name']}")
        st.session_state.quantities[cover['name']] = qty

# --- Generowanie PDF ---
def generate_pdf(cover_data):
    from reportlab.lib.utils import ImageReader
    horizontal_size = (270 * mm, 150 * mm)
    vertical_size = (150 * mm, 270 * mm)
    page_width, page_height = landscape((450 * mm, 320 * mm))

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

    h1_y = page_height / 2 + 5 * mm
    h2_y = page_height / 2 - horizontal_size[1] - 5 * mm
    v_x = horizontal_size[0] + 20 * mm
    v_y = (page_height - vertical_size[1]) / 2

    positions = [
        (15 * mm, h1_y),
        (15 * mm, h2_y),
        (v_x, v_y)
    ]

    current_batch = []
    for item in cover_data:
        for _ in range(item["quantity"]):
            current_batch.append(item["image"])
            if len(current_batch) == 3:
                for idx, img in enumerate(current_batch):
                    if idx == 2:
                        img = img.rotate(90, expand=True)
                        img_reader = ImageReader(img)
                        c.drawImage(img_reader, *positions[idx], vertical_size[0], vertical_size[1])
                    else:
                        img_reader = ImageReader(img)
                        c.drawImage(img_reader, *positions[idx], horizontal_size[0], horizontal_size[1])
                c.showPage()
                current_batch = []

    if current_batch:
        for idx, img in enumerate(current_batch):
            if idx == 2:
                img = img.rotate(90, expand=True)
                img_reader = ImageReader(img)
                c.drawImage(img_reader, *positions[idx], vertical_size[0], vertical_size[1])
            else:
                img_reader = ImageReader(img)
                c.drawImage(img_reader, *positions[idx], horizontal_size[0], horizontal_size[1])
        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer

# --- PDF button ---
st.markdown("---")
if st.button("📄 Stwórz PDF"):
    if total_covers == 0:
        st.warning("Nie dodano żadnych okładek.")
    else:
        with st.spinner("Generowanie PDF... Proszę czekać"):
            covers_to_print = [
                {"name": cover["name"], "image": cover["image"], "quantity": st.session_state.quantities[cover["name"]]}
                for cover in st.session_state.covers if st.session_state.quantities[cover["name"]] > 0
            ]
            pdf_buffer = generate_pdf(covers_to_print)
            st.download_button("📥 Pobierz PDF", data=pdf_buffer, file_name="okladki.pdf", mime="application/pdf")
