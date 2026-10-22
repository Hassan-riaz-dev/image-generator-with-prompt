
import os
import io
import base64
import streamlit as st
from google import genai
from PIL import Image

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="PixelAI - Image Generator",
    page_icon="🎨",
    layout="wide"
)

# ============================================
# CUSTOM CSS - DARK PURPLE & LIGHT TEXT
# ============================================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0b1020, #191532);
    color: #dbeafe;
}

.pixel-title {
    text-align: center;
    font-size: clamp(30px, 4vw, 46px);
    font-weight: 800;
    background: linear-gradient(90deg, #c4b5fd, #67e8f9);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.pixel-subtitle {
    text-align: center;
    color: #a5b4fc !important;
    font-size: 16px;
    margin-bottom: 28px;
}

h1, h2, h3 {
    color: #c4b5fd !important;
}

.stApp p,
.stApp label,
.stApp li {
    color: #dbeafe;
}

.stTextArea textarea,
.stTextInput input {
    background-color: #20243b !important;
    color: #f0f9ff !important;
    -webkit-text-fill-color: #f0f9ff !important;
    border: 1px solid #6366f1 !important;
    border-radius: 10px !important;
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
    min-height: 46px;
    font-weight: 700;
}

.stButton > button:hover,
.stDownloadButton > button:hover,
.stFormSubmitButton > button:hover {
    border: 1px solid #a78bfa;
}

section[data-testid="stSidebar"] {
    background-color: #11152a;
}

.pixel-footer {
    text-align: center;
    color: #a5b4c8 !important;
    font-size: 13px;
    padding: 18px;
}
</style>
""", unsafe_allow_html=True)


# ============================================
# API KEY
# ============================================
def get_api_key():
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
        if key:
            return str(key).strip()
    except Exception:
        pass

    return os.getenv("GEMINI_API_KEY", "").strip()


# ============================================
# HEADER
# ============================================
st.markdown(
    '<div class="pixel-title">🎨 PixelAI Image Generator</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="pixel-subtitle">'
    'Describe your imagination and generate a real picture.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================
# SIDEBAR SETTINGS
# ============================================
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
            "Pixel Art",
            "Studio Portrait"
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

    resolution = st.selectbox(
        "Image Resolution",
        ["1K", "2K"]
    )

    st.divider()
    st.caption("Image generation powered by Google Gemini.")


# ============================================
# PROMPT INPUT
# ============================================
st.subheader("✨ What picture do you want?")

with st.form("image_form"):
    prompt = st.text_area(
        "Describe your image",
        placeholder=(
            "Example: A white sports car on a mountain road "
            "at sunset, cinematic lighting, realistic details..."
        ),
        height=140
    )

    generate = st.form_submit_button(
        "🎨 Generate My Image",
        use_container_width=True
    )


# ============================================
# IMAGE GENERATION
# ============================================
if generate:

    if not prompt.strip():
        st.warning("Please enter an image description.")
        st.stop()

    api_key = get_api_key()

    if not api_key:
        st.error(
            "GEMINI_API_KEY missing. Add it in "
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

    # Send the prompt directly to an image-generation model.
    image_prompt = (
        f"Create an actual image. Do not return a written description. "
        f"Art style: {style}. "
        f"Image description: {prompt.strip()}"
    )

    try:
        client = genai.Client(api_key=api_key)

        with st.spinner(
            "🎨 Generating your picture... Please wait."
        ):
            result = client.interactions.create(
                model="gemini-3.1-flash-image",
                input=image_prompt,
                response_format={
                    "type": "image",
                    "mime_type": "image/jpeg",
                    "aspect_ratio": ratios[aspect_ratio],
                    "image_size": resolution
                }
            )

        # Get the actual generated image, not text.
        generated_image = getattr(result, "output_image", None)

        if not generated_image or not generated_image.data:
            st.error(
                "No image was returned. Please try again or "
                "check your Gemini model access and API quota."
            )
            st.stop()

        image_bytes = base64.b64decode(generated_image.data)

        # Validate image bytes.
        image = Image.open(io.BytesIO(image_bytes))
        image.load()

        # Convert to JPEG for consistent downloads.
        jpg_buffer = io.BytesIO()
        image.convert("RGB").save(
            jpg_buffer,
            format="JPEG",
            quality=95
        )
        jpg_bytes = jpg_buffer.getvalue()

        # Display the generated picture only.
        st.success("Your picture is ready!")

        st.image(
            jpg_bytes,
            caption="Generated with PixelAI",
            use_container_width=True
        )

        st.download_button(
            label="⬇️ Download Your Picture",
            data=jpg_bytes,
            file_name="pixelai_image.jpg",
            mime="image/jpeg",
            use_container_width=True
        )

    except Exception as error:
        message = str(error)
        st.error("Image generation failed.")

        if "404" in message or "NOT_FOUND" in message:
            st.warning(
                "The image model may not be available to your API key. "
                "Check the official Gemini model documentation."
            )
        elif "400" in message or "INVALID_ARGUMENT" in message:
            st.warning(
                "The API rejected a request setting. Check the "
                "supported image format, ratio, and resolution."
            )
        elif "403" in message or "PERMISSION_DENIED" in message:
            st.warning(
                "Check your API key, account permissions, and "
                "image-generation access."
            )
        elif "429" in message or "RESOURCE_EXHAUSTED" in message:
            st.warning(
                "Your API quota or rate limit may have been reached."
            )
        else:
            st.caption(message[:700])


# ============================================
# FOOTER
# ============================================
st.divider()

st.markdown(
    '<div class="pixel-footer">'
    'PixelAI · Streamlit + Gemini Image Generation'
    '</div>',
    unsafe_allow_html=True
)
