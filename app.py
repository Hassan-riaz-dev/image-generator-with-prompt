
import io
import os
import streamlit as st
from google import genai
from google.genai import types
from PIL import Image

# ==================================================
# PAGE CONFIGURATION
# ==================================================
st.set_page_config(
    page_title="PixelAI | AI Image Generator",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================================================
# API CONFIGURATION
# ==================================================
def get_secret(name):
    try:
        value = st.secrets.get(name, "")
        if value:
            return str(value).strip()
    except Exception:
        pass

    return os.getenv(name, "").strip()


GEMINI_API_KEY = get_secret("GEMINI_API_KEY")

# Gemini models: one for text, one for image generation
TEXT_MODEL = "gemini-3.8-flash"
IMAGE_MODEL = "gemini-3.1-flash-image"

# ==================================================
# CUSTOM UI AND TEXT COLORS
# ==================================================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0b1020 0%, #17152e 100%);
    color: #dbeafe;
}

/* Main headings */
h1, h2, h3 {
    color: #c4b5fd !important;
}

/* Main title */
.pixel-title {
    text-align: center;
    font-size: clamp(30px, 4vw, 46px);
    font-weight: 800;
    background: linear-gradient(90deg, #a78bfa, #67e8f9);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    padding: 8px 0;
}

/* Subtitle */
.pixel-subtitle {
    text-align: center;
    color: #a5b4fc !important;
    font-size: 16px;
    margin-bottom: 28px;
}

/* General text */
.stApp p,
.stApp li,
.stApp label,
.stApp .stMarkdown {
    color: #dbeafe;
}

/* Text inputs */
.stTextInput input,
.stTextArea textarea {
    background-color: #20243b !important;
    color: #f0f9ff !important;
    border: 1px solid #6366f1 !important;
    border-radius: 10px !important;
    -webkit-text-fill-color: #f0f9ff !important;
}

/* Input placeholders */
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #a5b4c8 !important;
    -webkit-text-fill-color: #a5b4c8 !important;
}

/* Select boxes */
.stSelectbox div[data-baseweb="select"] {
    background-color: #20243b !important;
    color: #f0f9ff !important;
}

/* Buttons */
.stButton > button,
.stDownloadButton > button {
    background: linear-gradient(90deg, #7c3aed, #6366f1);
    color: #ffffff !important;
    border: none;
    border-radius: 10px;
    min-height: 45px;
    font-weight: 700;
    transition: 0.2s ease;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    background: linear-gradient(90deg, #6d28d9, #4f46e5);
    border: 1px solid #a78bfa;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #11152a;
}

/* Cards and alerts */
div[data-testid="stAlert"] {
    border-radius: 10px;
}

hr {
    border-color: #37345e;
}

/* Footer */
.pixel-footer {
    text-align: center;
    color: #a5b4c8 !important;
    font-size: 13px;
    padding: 18px 0;
}
</style>
""", unsafe_allow_html=True)

# ==================================================
# HEADER
# ==================================================
st.markdown(
    '<div class="pixel-title">🎨 PixelAI Image Generator</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="pixel-subtitle">'
    'Bring your imagination to life with Gemini AI.'
    '</div>',
    unsafe_allow_html=True
)

# ==================================================
# SIDEBAR SETTINGS
# ==================================================
with st.sidebar:
    st.markdown("## ⚙️ Image Settings")

    art_style = st.selectbox(
        "Choose an art style",
        [
            "Realistic Photography",
            "Digital Art",
            "Anime",
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

    quality = st.selectbox(
        "Detail level",
        [
            "Standard",
            "Highly Detailed",
            "Ultra Detailed"
        ]
    )

    aspect_ratio = st.selectbox(
        "Image dimensions",
        [
            "Square (1:1)",
            "Portrait (2:3)",
            "Landscape (3:2)",
            "Story (9:16)",
            "Widescreen (16:9)"
        ]
    )

    enhance_prompt = st.checkbox(
        "Enhance prompt with Gemini",
        value=True
    )

    st.divider()

    st.caption("Powered by Google's Gemini API.")
    st.caption("API usage may be subject to quotas or charges.")

# ==================================================
# MAIN INPUTS
# ==================================================
st.markdown("### ✨ Describe your imagination")

with st.form("image_generator_form"):
    prompt = st.text_area(
        "Image prompt",
        placeholder=(
            "Example: A beautiful futuristic city at sunset, "
            "flying cars, glowing buildings and cinematic lighting..."
        ),
        height=130
    )

    negative_prompt = st.text_input(
        "Optional: What should the image avoid?",
        placeholder="Example: blurry details, unwanted text"
    )

    submitted = st.form_submit_button(
        "🚀 Generate Image",
        type="primary",
        use_container_width=True
    )

# ==================================================
# GEMINI CLIENT
# ==================================================
def create_client():
    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is missing. Add it to Streamlit "
            "Secrets before generating images."
        )

    return genai.Client(api_key=GEMINI_API_KEY)


# ==================================================
# PROMPT ENHANCEMENT
# ==================================================
def improve_prompt(client, user_prompt, style, detail, avoid):
    instructions = f"""
You are a professional AI image prompt engineer.

Transform the user's idea into a clear, detailed visual prompt.

Art style: {style}
Detail level: {detail}
User idea: {user_prompt}
Elements to avoid: {avoid if avoid else "None specified"}

Include appropriate composition, lighting, colors, environment,
camera perspective, textures, and artistic details.

Keep the original idea intact. Do not add unrelated subjects.
Return only the final image-generation prompt.
"""

    response = client.models.generate_content(
        model=TEXT_MODEL,
        contents=instructions
    )

    result = response.text

    if not result or not result.strip():
        raise RuntimeError(
            "Gemini did not return an improved prompt. Please try again."
        )

    return result.strip()


# ==================================================
# IMAGE GENERATION WITH GEMINI
# ==================================================
def generate_image(client, final_prompt, ratio):
    aspect_ratios = {
        "Square (1:1)": "1:1",
        "Portrait (2:3)": "2:3",
        "Landscape (3:2)": "3:2",
        "Story (9:16)": "9:16",
        "Widescreen (16:9)": "16:9"
    }

    image_instructions = (
        "Create one high-quality image based on this description:\n\n"
        + final_prompt
    )

    response = client.models.generate_content(
        model=IMAGE_MODEL,
        contents=image_instructions,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratios[ratio]
            )
        )
    )

    # Find the returned image in Gemini's response.
    for part in response.parts:
        if part.inline_data is not None:
            image = part.as_image()

            image_buffer = io.BytesIO()
            image.save(image_buffer, format="PNG")

            image_buffer.seek(0)
            return image_buffer.getvalue()

    raise RuntimeError(
        "Gemini did not return an image. Check model access, "
        "API quotas, and the image-generation API response."
    )


# ==================================================
# GENERATION WORKFLOW
# ==================================================
if submitted:
    if not prompt.strip():
        st.warning("Please enter a description for your image.")

    else:
        try:
            client = create_client()

            final_prompt = (
                f"{prompt.strip()}\n"
                f"Art style: {art_style}.\n"
                f"Detail level: {quality}."
            )

            if negative_prompt.strip():
                final_prompt += (
                    "\nAvoid these elements: "
                    + negative_prompt.strip()
                )

            if enhance_prompt:
                with st.spinner("✨ Gemini is improving your prompt..."):
                    final_prompt = improve_prompt(
                        client,
                        prompt.strip(),
                        art_style,
                        quality,
                        negative_prompt.strip()
                    )

                    if negative_prompt.strip():
                        final_prompt += (
                            "\nAvoid these elements: "
                            + negative_prompt.strip()
                        )

            st.markdown("### 📝 Final image prompt")
            st.info(final_prompt)

            with st.spinner(
                "🎨 Gemini is creating your image. Please wait..."
            ):
                image_bytes = generate_image(
                    client,
                    final_prompt,
                    aspect_ratio
                )

            # Validate returned image data.
            image = Image.open(io.BytesIO(image_bytes))
            image.load()

            st.success("Your image has been generated successfully!")

            st.markdown("### 🖼️ Your generated image")

            st.image(
                image,
                caption="Created with PixelAI",
                use_container_width=True
            )

            st.download_button(
                label="⬇️ Download Image (PNG)",
                data=image_bytes,
                file_name="pixelai_generated.png",
                mime="image/png",
                use_container_width=True
            )

        except Exception as error:
            error_text = str(error)

            st.error("Image generation failed.")

            # Give useful troubleshooting guidance.
            if "API_KEY" in error_text:
                st.warning(
                    "Add GEMINI_API_KEY in your Streamlit Secrets."
                )
            elif "404" in error_text or "NOT_FOUND" in error_text:
                st.warning(
                    "The selected Gemini model may not be available "
                    "to your API key. Check Google's current model list."
                )
            elif (
                "429" in error_text
                or "RESOURCE_EXHAUSTED" in error_text
            ):
                st.warning(
                    "Your API quota or rate limit may have been reached."
                )
            elif (
                "403" in error_text
                or "PERMISSION_DENIED" in error_text
            ):
                st.warning(
                    "Check your API key, project permissions, and "
                    "whether image generation is available to your account."
                )
            else:
                st.caption(error_text[:700])

# ==================================================
# FOOTER
# ==================================================
st.divider()

st.markdown(
    '<div class="pixel-footer">'
    'PixelAI · Built with Streamlit and Google Gemini'
    '</div>',
    unsafe_allow_html=True
)
