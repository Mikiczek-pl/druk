import streamlit as st
from PIL import Image
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

st.set_page_config(page_title="Stwórz okładkę Blu-ray", layout="centered")
st.title("Stwórz okładkę Blu-ray")

# Inicjalizacja sesji
if "covers" not in st.session_state:
    st.session_state.covers = []
if "quantities" not in st.session_state:
    st.session_state.quantities = {}

# Wgrywanie plików
uploaded_files = st.file_uploader("Prześlij okładki (JPG, PNG)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    for file in uploaded_files:
        name = file.name
        if name not in [c['name'] for c in st.session_state.covers]:
            image = Image.open(file).convert("RGB")
            st.session_state.covers.append({"name": name, "image": image})
            st.session_state.quantities[name] = 1

st.markdown("### Podgląd i ustawienia")
to_remove = []

for idx, cover in enumerate(st.session_state.covers):
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        st.image(cover["image"], width=100)
    with col2:
        st.write(f"**{cover['name']}**")
        qty = st.number_input(
            "Ilość kopii",
            min_value=0,
            step=1,
            key=f"qty_{cover['name']}",
            value=st.session_state.quantities.get(cover['name'], 1)
        )
        st.session_state.quantities[cover['name']] = qty
    with col3:
        if st.button("Usuń", key=f"del_{cover['name']}"):
            to_remove.append(idx)

if to_remove:
    for idx in sorted(to_remove, reverse=True):
        removed = st.session_state.covers.pop(idx)
        st.session_state.quantities.pop(removed['name'], None)

# Podsumowanie
st.markdown("---")
st.subheader("Podsumowanie")

total = sum(st.session_state.quantities.get(c['name'], 0) for c in st.session_state.covers)
missing = (3 - total % 3) % 3

st.markdown(f"**Liczba wszystkich okładek:** {total}")
if missing > 0:
    st.warning(f"Brakuje {missing} okładki, aby dopełnić komplet (wielokrotność 3).")
else:
    st.success("Liczba okładek to pełny komplet.")

def generate_pdf(cover_data):
    h_size = (270 * mm, 150 * mm)
    v_size = (150 * mm, 270 * mm)
    page_size = (450 * mm, 320 * mm)

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(page_size))

    def get_centered_positions():
        center_x = page_size[0] / 2
        center_y = page_size[1] / 2

        positions = [
            (center_x - h_size[0] - 5 * mm, center_y + h_size[1] / 2),
            (center_x - h_size[0] - 5 * mm, center_y - h_size[1] * 1.5 - 10 * mm),
            (center_x + 20 * mm, center_y - v_size[1] / 2),
        ]
        return positions

    images = []
    for item in cover_data:
        for _ in range(item["quantity"]):
            images.append(item["image"])

    while images:
        batch = images[:3]
        images = images[3:]
        positions = get_centered_positions()

        for idx, img in enumerate(batch):
            if idx == 2:
                img = img.rotate(90, expand=True)
                c.drawImage(ImageReader(img), positions[idx][0], positions[idx][1], v_size[0], v_size[1])
            else:
                c.drawImage(ImageReader(img), positions[idx][0], positions[idx][1], h_size[0], h_size[1])
        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer

# Generuj PDF
st.markdown("---")
if st.button("Stwórz PDF"):
    covers = [
        {"name": c["name"], "image": c["image"], "quantity": st.session_state.quantities[c["name"]]}
        for c in st.session_state.covers if st.session_state.quantities[c["name"]] > 0
    ]
    if not covers:
        st.warning("Brak okładek do wygenerowania.")
    else:
        with st.spinner("Generowanie PDF... proszę czekać"):
            pdf_file = generate_pdf(covers)
        st.download_button("Pobierz PDF", data=pdf_file, file_name="okladki_blu_ray.pdf", mime="application/pdf")
