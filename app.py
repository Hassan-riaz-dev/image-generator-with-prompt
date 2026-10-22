
import os
import io
import secrets
import requests
import streamlit as st
from groq import Groq
from urllib.parse import quote

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="PixelAI - Image Generator",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0b1020, #17152e);
    color: #f5f5ff;
}
.main-title {
    text-align: center;
    font-size: 44px;
    font-weight: 800;
    background: linear-gradient(90deg, #8b5cf6, #22d3ee);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.subtitle {
    text-align: center;
    color: #b9bbd4;
    font-size: 17px;
    margin-bottom: 30px;
}
div.stButton > button {
    width: 100%;
    border-radius: 10px;
    min-height: 45px;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# ---------------- API CONFIG ----------------
def get_secret(name):
    try:
        value = st.secrets.get(name, "")
        if value:
            return value
    except Exception:
        pass
    return os.getenv(name, "")

groq_api_key = get_secret("GROQ_API_KEY")

# ---------------- HEADER ----------------
st.markdown(
    '<div class="main-title">🎨 PixelAI Image Generator</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="subtitle">'
    'Turn your imagination into beautiful AI images.'
    '</div>',
    unsafe_allow_html=True
)

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("⚙️ Image Settings")

    style = st.selectbox(
        "Art Style",
        [
            "Realistic Photography",
            "Digital Art",
            "Anime",
            "3D Render",
            "Watercolor",
            "Oil Painting",
            "Cinematic",
            "Fantasy Art",
            "Minimalist",
            "Cyberpunk"
        ]
    )

    quality = st.selectbox(
        "Image Quality",
        ["Standard", "Detailed", "Ultra Detailed"]
    )

    aspect_ratio = st.selectbox(
        "Aspect Ratio",
        ["Square (1:1)", "Portrait (2:3)", "Landscape (3:2)"]
    )

    enhance = st.checkbox("Enhance prompt with Groq", value=True)

    st.divider()
    st.caption("Groq enhances your text prompt. An external image service creates the image.")

# ---------------- MAIN INPUT ----------------
st.subheader("✨ Describe Your Image")

prompt = st.text_area(
    "Your prompt",
    placeholder=(
        "Example: A beautiful futuristic city at sunset, "
        "flying cars, cinematic lighting, ultra realistic..."
    ),
    height=130
)

negative_prompt = st.text_input(
    "Things to avoid (optional)",
    placeholder="blurry, low quality, distorted objects"
)

generate = st.button(
    "🚀 Generate Image",
    type="primary",
    use_container_width=True
)

# ---------------- PROMPT ENHANCEMENT ----------------
def enhance_prompt(user_prompt, art_style, image_quality):
    if not groq_api_key:
        raise ValueError(
            "GROQ_API_KEY is missing. Add it in Streamlit Secrets."
        )

    client = Groq(api_key=groq_api_key)

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert text-to-image prompt engineer. "
                    "Rewrite the user's idea as one detailed visual prompt. "
                    "Include composition, lighting, colors, environment, "
                    "and visual details where appropriate. "
                    "Respect the requested style. "
                    "Return only the final image prompt."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Image idea: {user_prompt}\n"
                    f"Art style: {art_style}\n"
                    f"Detail level: {image_quality}"
                )
            }
        ],
        temperature=0.7,
        max_tokens=300
    )

    return response.choices[0].message.content.strip()


# ---------------- IMAGE GENERATION ----------------
def generate_image(image_prompt, negative, ratio):
    dimensions = {
        "Square (1:1)": (1024, 1024),
        "Portrait (2:3)": (768, 1152),
        "Landscape (3:2)": (1152, 768)
    }

    width, height = dimensions[ratio]
    seed = secrets.randbelow(2_000_000_000)

    full_prompt = image_prompt
    if negative.strip():
        full_prompt += (
            ". Avoid these elements: " + negative.strip()
        )

    # External image provider; it is not the Groq API.
    image_url = (
        "https://image.pollinations.ai/prompt/"
        + quote(full_prompt, safe="")
    )

    params = {
        "width": width,
        "height": height,
        "seed": seed,
        "model": "flux",
        "nologo": "true"
    }

    response = requests.get(
        image_url,
        params=params,
        timeout=180,
        headers={"User-Agent": "PixelAI-Streamlit/1.0"}
    )
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")
    if "image" not in content_type.lower():
        raise RuntimeError(
            "The image provider did not return an image. "
            "Try again later."
        )

    image_bytes = response.content

    # Confirm that the response is a readable image.
    from PIL import Image
    Image.open(io.BytesIO(image_bytes)).verify()

    return image_bytes


# ---------------- GENERATION WORKFLOW ----------------
if generate:
    if not prompt.strip():
        st.warning("Please enter an image description first.")

    else:
        final_prompt = (
            f"{prompt.strip()}, style: {style}, {quality}."
        )

        try:
            if enhance:
                if not groq_api_key:
                    st.error(
                        "GROQ_API_KEY is missing. Add it in "
                        "Streamlit Secrets or disable prompt enhancement."
                    )
                    st.stop()

                with st.spinner("✨ Groq is improving your prompt..."):
                    final_prompt = enhance_prompt(
                        prompt.strip(), style, quality
                    )

            st.markdown("### 📝 Final Image Prompt")
            st.info(final_prompt)

            with st.spinner(
                "🎨 Creating your image... This may take a while."
            ):
                image_bytes = generate_image(
                    final_prompt, negative_prompt, aspect_ratio
                )

            st.success("Your image is ready!")

            st.image(
                image_bytes,
                caption="Generated with PixelAI",
                use_container_width=True
            )

            st.download_button(
                label="⬇️ Download Image",
                data=image_bytes,
                file_name="pixelai_generated.png",
                mime="image/png",
                use_container_width=True
            )

        except requests.exceptions.Timeout:
            st.error(
                "Image generation timed out. Please try again."
            )
        except requests.exceptions.RequestException as exc:
            st.error(
                "The image service is unavailable or rejected "
                "the request. Try again later."
            )
            st.caption(str(exc)[:500])
        except Exception as exc:
            st.error(f"Generation failed: {exc}")

# ---------------- FOOTER ----------------
st.divider()
st.markdown(
    "<div style='text-align:center;color:#a5a5c5;'>"
    "PixelAI • Built with Streamlit + Groq + an external "
    "image-generation service"
    "</div>",
    unsafe_allow_html=True
)
