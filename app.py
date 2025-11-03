import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io, random, os
from PIL import Image

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Final Poster • Arts & Advanced Big Data", layout="wide")

PALETTE_FILE = "palette.csv"

# ---------- LOAD OR CREATE PALETTE ----------
def load_palette():
    if not os.path.exists(PALETTE_FILE):
        df = pd.DataFrame({
            "name": ["pink", "mint", "sky", "lemon", "violet"],
            "r": [1.0, 0.8, 0.7, 1.0, 0.85],
            "g": [0.7, 1.0, 0.8, 1.0, 0.75],
            "b": [0.8, 0.8, 1.0, 0.6, 0.95]
        })
        df.to_csv(PALETTE_FILE, index=False)
    return pd.read_csv(PALETTE_FILE)

def save_palette(df):
    df.to_csv(PALETTE_FILE, index=False)

# ---------- COLOR EXTRACTION ----------
def extract_colors_from_image(img, n_colors=5):
    img = img.resize((150, 150))
    data = np.array(img).reshape((-1, 3))
    df = pd.DataFrame(data, columns=["r", "g", "b"]) / 255.0
    centers = df.sample(n=n_colors, random_state=42)
    centers["name"] = [f"color{i+1}" for i in range(n_colors)]
    centers = centers[["name", "r", "g", "b"]]
    return centers.reset_index(drop=True)

# ---------- GENERATIVE SHAPE ----------
def spiky_blob(cx, cy, radius=1.0, wobble=0.2, n=150):
    ang = np.linspace(0, 2*np.pi, n)
    rad = radius * (1 + wobble * np.random.randn(n))
    x = cx + rad * np.cos(ang)
    y = cy + rad * np.sin(ang)
    return x, y

# ---------- POSTER DRAW ----------
def generate_poster(df, layers=10, wobble=0.25, seed=0, edge=False, edge_color=(0, 0, 0, 0.35)):
    if seed:
        np.random.seed(seed)
        random.seed(seed)

    fig, ax = plt.subplots(figsize=(6, 8))
    ax.axis("off")

    colors = df[["r", "g", "b"]].values

    # ✅ 改进：分散有规律的布局（轻微随机的网格）
    grid_positions = []
    grid_x = np.linspace(-2.5, 2.5, int(np.sqrt(layers)) + 2)
    grid_y = np.linspace(-3, 3, int(np.sqrt(layers)) + 2)

    for gx in grid_x:
        for gy in grid_y:
            grid_positions.append((
                gx + random.uniform(-0.3, 0.3),
                gy + random.uniform(-0.3, 0.3)
            ))

    positions = random.sample(grid_positions, min(layers, len(grid_positions)))

    for (cx, cy) in positions:
        color = random.choice(colors)
        rgba = (*color, 0.35)
        r = random.uniform(1.3, 2.0)
        x, y = spiky_blob(cx, cy, r, wobble)
        ax.fill(x, y, color=rgba, ec=edge_color if edge else None, lw=0.8 if edge else 0)

    # ✅ 保留原标题风格
    ax.text(0, 3.8, "Final Poster", fontsize=22, weight="bold", ha="center")
    ax.text(0, 3.45, "Week • Arts & Advanced Big Data", fontsize=13, color="gray", ha="center")

    ax.set_xlim(-4, 4)
    ax.set_ylim(-4, 4)
    return fig

# ---------- SIDEBAR ----------
st.sidebar.header("⚙️ Controls")

palette_mode = st.sidebar.selectbox("Palette Mode", ["CSV"])
layers = st.sidebar.slider("Number of Layers", 5, 30, 15)
wobble = st.sidebar.slider("Wobble Intensity", 0.05, 0.6, 0.25)
seed = st.sidebar.number_input("Random Seed", min_value=0, value=0, step=1)

# Edge Settings
st.sidebar.subheader("🎨 Blob Edge Settings")
show_edges = st.sidebar.checkbox("Show Blob Edges", value=True)
edge_color = st.sidebar.color_picker("Edge Color", "#000000")

# Extract from image
st.sidebar.subheader("📸 Extract Colors from Image")
uploaded_img = st.sidebar.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])
if uploaded_img:
    img = Image.open(uploaded_img)
    extracted_df = extract_colors_from_image(img)
    save_palette(extracted_df)
    st.sidebar.success("Extracted new palette from image!")

# ---------- MAIN ----------
st.title("🎨 Generative Poster Studio")
st.write("Generate algorithmic art using CSV palettes or extracted image palettes!")

df = load_palette()

st.subheader("🎨 Current Palette Preview")
cols = st.columns(len(df))
for i, row in enumerate(df.iterrows(), start=1):
    _, r = row
    color = f"rgb({int(r.r*255)}, {int(r.g*255)}, {int(r.b*255)})"
    cols[i-1].markdown(
        f"<div style='background-color:{color}; height:80px; border-radius:4px; text-align:center; line-height:80px; color:black; font-weight:600;'>{i}</div>",
        unsafe_allow_html=True
    )

# ---------- Generate Poster ----------
if st.button("🎨 Generate Poster"):
    ec_rgba = tuple(int(edge_color.lstrip("#")[i:i+2], 16)/255 for i in (0, 2, 4)) + (0.35,)
    fig = generate_poster(df, layers, wobble, seed, show_edges, ec_rgba)
    st.pyplot(fig)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
    st.download_button("💾 Download Poster (PNG)", data=buf.getvalue(),
                       file_name="FinalPoster.png", mime="image/png")
else:
    st.info("Adjust sliders and click **Generate Poster** to create your artwork.")

# ---------- MANAGE PALETTE ----------
st.header("📁 Manage Palettes in Real Time")

tab1, tab2 = st.tabs(["🎨 palette.csv", "📸 reference.csv"])
with tab1:
    color_name = st.text_input("Color Name")
    picked = st.color_picker("Pick a Color", "#ffffff")
    if st.button("➕ Add Color"):
        r, g, b = tuple(int(picked.lstrip("#")[i:i+2], 16)/255 for i in (0, 2, 4))
        new_row = pd.DataFrame({"name": [color_name or "new"], "r": [r], "g": [g], "b": [b]})
        df = pd.concat([df, new_row], ignore_index=True)
        save_palette(df)
        st.success("Added new color to palette!")

    st.dataframe(df)

with tab2:
    st.write("Upload or compare with another color reference palette if needed.")
