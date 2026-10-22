
import os
import base64
import streamlit as st
from google import genai
from PIL import Image
import io

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="PixelAI - Image Generator",
    page_icon="🎨",
    layout="wide"
)

# ==========================================
# CUSTOM DESIGN
# ==========================================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0b1020, #191532);
    color: #e2e8f0;
}
h1, h2, h3 {
    color: #c4b5fd !important;
}
p, label, li, .stMarkdown {
    color: #dbeafe;
}
.pixel-title {
    text-align: center;
    font-size: 42px;
    font-weight: 800;
    background: linear-gradient(90deg, #a78bfa, #67e8f9);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.pixel-subtitle {
    text-align: center;
    color: #a5b4fc !important;
    margin-bottom: 28px;
}
.stTextArea textarea,
.stTextInput input {
    background-color: #20243b !important;
    color: #f0f9ff !important;
    -webkit-text-fill-color: #f0f9ff !important;
    border: 1px solid #6366f1 !important;
    border-radius: 10px;
}
.stTextArea textarea::placeholder,
.stTextInput input::placeholder {
    color: #a5b4c8 !important;
    -webkit-text-fill-color: #a5b4c8 !important;
}
.stButton > button,
.stDownloadButton > button,
.stFormSubmitButton > button {
    background: linear-gradient(90deg, #7c3aed, #4f46e5);
    color: white !important;
    border: none;
    border-radius: 10px;
    min-height: 45px;
    font-weight: bold;
}
section[data-testid="stSidebar"] {
    background-color: #11152a;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# API KEY
# ==========================================
def get_api_key():
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
        if key:
            return str(key).strip()
    except Exception:
        pass

    return os.getenv("GEMINI_API_KEY", "").strip()


# ==========================================
# HEADER
# ==========================================
st.markdown(
    '<div class="pixel-title">🎨 PixelAI Image Generator</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="pixel-subtitle">'
    'Write your idea. Generate a real AI image. Download it.'
    '</div>',
    unsafe_allow_html=True
)

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.header("⚙️ Image Settings")

    style = st.selectbox(
        "Art Style",
        [
            "Realistic Photography",
            "Anime",
            "Digital Art",
            "3D Render",
            "Cinematic",
            "Watercolor",
            "Oil Painting",
            "Fantasy Art",
            "Cyberpunk",
            "Minimalist",
            "Pixel Art"
        ]
    )

    aspect_ratio = st.selectbox(
        "Image Ratio",
        [
            "Square (1:1)",
            "Portrait (2:3)",
            "Landscape (3:2)",
            "Instagram Story (9:16)",
            "Widescreen (16:9)"
        ]
    )

    image_size = st.selectbox(
        "Image Resolution",
        ["1K", "2K"]
    )

    st.divider()
    st.caption("Image generation powered by Google Gemini.")

# ==========================================
# USER PROMPT
# ==========================================
st.subheader("✨ Describe the image you want")

with st.form("generate_form"):
    prompt = st.text_area(
        "Image description",
        placeholder=(
            "Example: A beautiful white horse running "
            "through a green field at sunset..."
        ),
        height=140
    )

    submitted = st.form_submit_button(
        "🎨 Generate My Image",
        use_container_width=True
    )

# ==========================================
# IMAGE GENERATION
# ==========================================
if submitted:
    if not prompt.strip():
        st.warning("Please enter an image description.")
        st.stop()

    api_key = get_api_key()

    if not api_key:
        st.error(
            "GEMINI_API_KEY is missing. Add it in "
            "Streamlit Cloud → Settings → Secrets."
        )
        st.stop()

    ratios = {
        "Square (1:1)": "1:1",
        "Portrait (2:3)": "2:3",
        "Landscape (3:2)": "3:2",
        "Instagram Story (9:16)": "9:16",
        "Widescreen (16:9)": "16:9"
    }

    # Send the user's idea directly to the image model.
    # No text-only prompt enhancement is performed.
    final_input = (
        f"Generate an image in this art style: {style}.\n"
        f"Image description: {prompt.strip()}\n"
        "Create the actual image, not a written description."
    )

    try:
        client = genai.Client(api_key=api_key)

        with st.spinner(
            "✨ Gemini is generating your image. Please wait..."
        ):
            result = client.interactions.create(
                model="gemini-nano-banana-2.1",
                input=final_input,
                response_format={
                    "type": "image",
                    "mime_type": "image/png",
                    "aspect_ratio": ratios[aspect_ratio],
                    "image_size": image_size
                }
            )

        # Extract the actual generated image.
        generated = getattr(result, "output_image", None)

        if generated is None or not getattr(generated, "data", None):
            st.error(
                "Gemini did not return an image. Check model access, "
                "API quota, and image-generation availability."
            )
            st.stop()

        image_bytes = base64.b64decode(generated.data)

        # Verify that the returned bytes form a valid image.
        image = Image.open(io.BytesIO(image_bytes))
        image.load()

        # Show the actual image only.
        st.success("Your image is ready!")

        st.image(
            image,
            use_container_width=True
        )

        # Download the generated image.
        output = io.BytesIO()
        image.save(output, format="PNG")
        output.seek(0)

        st.download_button(
            "⬇️ Download Image",
            data=output.getvalue(),
            file_name="pixelai_image.png",
            mime="image/png",
            use_container_width=True
        )

    except Exception as error:
        message = str(error)

        st.error("Image generation failed.")

        if "429" in message or "RESOURCE_EXHAUSTED" in message:
            st.warning(
                "Your Gemini API quota or rate limit may have been reached."
            )
        elif "403" in message or "PERMISSION_DENIED" in message:
            st.warning(
                "Check your API key and whether your account "
                "has permission to use the image model."
            )
        elif "404" in message or "NOT_FOUND" in message:
            st.warning(
                "The image model may not be available to your account. "
                "Check Google's current Gemini image-generation docs."
            )
        else:
            st.caption(message[:700])

# ==========================================
# FOOTER
# ==========================================
st.divider()
st.markdown(
    '<div style="text-align:center;color:#a5b4c8;">'
    'PixelAI · Streamlit + Gemini Image Generation'
    '</div>',
    unsafe_allow_html=True
)
