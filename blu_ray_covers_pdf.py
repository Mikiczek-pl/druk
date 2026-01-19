import streamlit as st
from PIL import Image
import os
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import mm

st.set_page_config(page_title="Kreator PDF Okładek Blu-ray", layout="wide")
st.title("📀 Kreator PDF Okładek Blu-ray")

if "covers" not in st.session_state:
    st.session_state.covers = []
if "quantities" not in st.session_state:
    st.session_state.quantities = {}

uploaded_files = st.file_uploader("Wgraj obrazy (JPG, PNG)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    for file in uploaded_files:
        name = file.name
        if name not in [c['name'] for c in st.session_state.covers]:
            image = Image.open(file).convert("RGB")
            st.session_state.covers.append({"name": name, "image": image})
            st.session_state.quantities[name] = 1

st.markdown("---")
st.subheader("Wybrane okładki")

cols = st.columns(5)

remove_index = None

for idx, cover in enumerate(st.session_state.covers):
    with cols[idx % 5]:
        st.image(cover["image"], caption=cover["name"], width=200)
        qty = st.number_input(f"Ilość: {cover['name']}", min_value=0, step=1,
                              key=f"qty_{cover['name']}", value=st.session_state.quantities.get(cover['name'], 1))
        st.session_state.quantities[cover['name']] = qty
        if st.button(f"Usuń {cover['name']}", key=f"del_{cover['name']}"):
            remove_index = idx

if remove_index is not None:
    removed_name = st.session_state.covers[remove_index]['name']
    st.session_state.covers = [c for c in st.session_state.covers if c['name'] != removed_name]
    st.session_state.quantities.pop(removed_name, None)

# Liczenie brakujących do kompletu
st.markdown("---")

st.markdown("## 📦 Podsumowanie")
total_covers = sum(st.session_state.quantities.values())
missing_to_full = (3 - (total_covers % 3)) % 3
st.markdown(f"### 🧮 Liczba wszystkich okładek: **{total_covers}**")
if missing_to_full > 0:
    st.warning(f"⚠️ Brakuje {missing_to_full} okładki, aby dopełnić pełny komplet (wielokrotność 3).")
else:
    st.success("✅ Liczba okładek to pełny komplet.")

st.markdown("---")

# Generowanie PDF
def generate_pdf(cover_data):
    from reportlab.lib.utils import ImageReader

    horizontal_size = (270 * mm, 150 * mm)
    vertical_size = (150 * mm, 270 * mm)
    page_size = (450 * mm, 320 * mm)

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(page_size))

    positions = [
    (0, (page_size[1] - 2 * horizontal_size[1] - 5 * mm) / 2 + horizontal_size[1] + 2.5 * mm),  # top
    (0, (page_size[1] - 2 * horizontal_size[1] - 5 * mm) / 2),  # bottom
    (horizontal_size[0] + 5 * mm, (page_size[1] - vertical_size[1]) / 2)  # right, centered vertically
]

# Adjust X to center entire group
left_group_width = horizontal_size[0] + 5 * mm + vertical_size[0]
offset_x = (page_size[0] - left_group_width) / 2
positions = [(x + offset_x, y) for x, y in positions] - horizontal_size[1] - 15 * mm),
        (15 * mm, page_size[1] - 2 * horizontal_size[1] - 20 * mm),
        (horizontal_size[0] + 20 * mm, (page_size[1] - vertical_size[1]) / 2)
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
                        c.drawImage(
                            img_reader,
                            positions[idx][0],
                            positions[idx][1],
                            vertical_size[0],
                            vertical_size[1]
                        )
                    else:
                        img_reader = ImageReader(img)
                        c.drawImage(
                            img_reader,
                            positions[idx][0],
                            positions[idx][1],
                            horizontal_size[0],
                            horizontal_size[1]
                        )

                c.showPage()
                current_batch = []

    if current_batch:
        for idx, img in enumerate(current_batch):
            if idx == 2:
                img = img.rotate(90, expand=True)
                img_reader = ImageReader(img)
                c.drawImage(
                    img_reader,
                    positions[idx][0],
                    positions[idx][1],
                    vertical_size[0],
                    vertical_size[1]
                )
            else:
                img_reader = ImageReader(img)
                c.drawImage(
                    img_reader,
                    positions[idx][0],
                    positions[idx][1],
                    horizontal_size[0],
                    horizontal_size[1]
                )

        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer

if st.button("🔽 Stwórz PDF"):
    if total_covers == 0:
        st.warning("Nie dodano żadnych okładek.")
    else:
        covers_to_print = [
            {"name": cover["name"], "image": cover["image"], "quantity": st.session_state.quantities[cover["name"]]}
            for cover in st.session_state.covers if st.session_state.quantities[cover["name"]] > 0
        ]
        pdf_buffer = generate_pdf(covers_to_print)
        with st.expander("📄 Podgląd PDF", expanded=True):
    st.download_button(
        "📥 Pobierz PDF",
        data=pdf_buffer,
        file_name="okladki.pdf",
        mime="application/pdf"
    )
    st.download_button(
        "💾 Zapisz PDF jako plik",
        data=pdf_buffer,
        file_name="okladki_zapisane.pdf",
        mime="application/pdf"
    )
    st.components.v1.iframe("data:application/pdf;base64," + pdf_buffer.read().encode("base64").decode(), height=600)
    pdf_buffer.seek(0)
