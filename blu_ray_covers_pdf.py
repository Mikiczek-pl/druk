import streamlit as st
from PIL import Image
import os
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import mm

st.set_page_config(page_title="Stwórz okładkę Blu-ray", layout="wide")
st.markdown("""
    <h1 style='text-align: center;'>Stwórz okładkę Blu-ray</h1>
""", unsafe_allow_html=True)

if "covers" not in st.session_state:
    st.session_state.covers = []
if "quantities" not in st.session_state:
    st.session_state.quantities = {}

# --- Upload ---
with st.container():
    uploaded_files = st.file_uploader("Wgraj obrazy (JPG, PNG)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    for file in uploaded_files:
        name = file.name
        if name not in [c['name'] for c in st.session_state.covers]:
            image = Image.open(file).convert("RGB")
            st.session_state.covers.append({"name": name, "image": image})
            st.session_state.quantities[name] = 1

# --- Podgląd i edycja ---
st.markdown("---")
st.markdown("<h3 style='text-align: center;'>Wybrane okładki</h3>", unsafe_allow_html=True)

for cover in st.session_state.covers:
    st.image(cover["image"], use_column_width=True)
    qty = st.number_input(
        f"Ilość ({cover['name']})",
        min_value=1,
        step=1,
        value=st.session_state.quantities.get(cover['name'], 1),
        key=f"qty_{cover['name']}"
    )
    st.session_state.quantities[cover['name']] = qty

# --- Licznik ---
total_covers = sum(st.session_state.quantities.values())
missing_to_full = (3 - (total_covers % 3)) % 3

st.markdown("---")
st.markdown(f"<div style='text-align:center;font-size:24px;font-weight:bold;'>Liczba wszystkich okładek: {total_covers}</div>", unsafe_allow_html=True)
if missing_to_full > 0:
    st.markdown(f"<div style='text-align:center;color:red;'>Brakuje {missing_to_full} okładki, aby dopełnić pełny komplet (wielokrotność 3).</div>", unsafe_allow_html=True)
else:
    st.markdown("<div style='text-align:center;color:green;'>Liczba okładek to pełny komplet.</div>", unsafe_allow_html=True)

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

# --- Generowanie i automatyczne pobieranie ---
if total_covers >= 1:
    covers_to_print = [
        {"name": cover["name"], "image": cover["image"], "quantity": st.session_state.quantities[cover["name"]]}
        for cover in st.session_state.covers if st.session_state.quantities[cover["name"]] > 0
    ]
    with st.spinner("Generowanie PDF..."):
        pdf_buffer = generate_pdf(covers_to_print)
        st.success("PDF został wygenerowany.")
        st.download_button("Kliknij tutaj jeśli nie pobrało się automatycznie", data=pdf_buffer, file_name="okladki.pdf", mime="application/pdf")
        js = f"""
            <script>
            var link = document.createElement('a');
            link.href = window.URL.createObjectURL(new Blob([{pdf_buffer.getvalue()}], {{type: 'application/pdf'}}));
            link.download = 'okladki.pdf';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            </script>
        """
        st.components.v1.html(js, height=0)
