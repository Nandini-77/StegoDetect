import os
import tempfile
from io import BytesIO

from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    send_file,
    send_from_directory,
)

from PIL import UnidentifiedImageError

from crypto_process import (
    DECRYPT_ERROR,
    decrypt_message,
    encrypt_message,
)

from lsb import hide_data, extract_data
from detector import detect_stego


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(
    __name__,
    static_folder="static",
    static_url_path="/crypto-static"
)


# ============================================================
# REACT FRONTEND
# ============================================================

# React Home page
# The actual React UI is built into dist/index.html
@app.get("/")
def home():
    return send_file(
        os.path.join(
            app.root_path,
            "dist",
            "index.html"
        )
    )


# React/Vite production assets
# Example:
# /assets/index-xxxxx.js
# /assets/index-xxxxx.css
@app.get("/assets/<path:filename>")
def react_assets(filename):
    return send_from_directory(
        os.path.join(
            app.root_path,
            "dist",
            "assets"
        ),
        filename
    )


# ============================================================
# PAGE ROUTES
# ============================================================

@app.get("/crypto")
def crypto_page():
    return render_template("crypto_page.html")


@app.get("/steganography")
def steganography_page():
    return render_template("steganography_page.html")


@app.get("/combined")
def combined_page():
    return render_template("combined_page.html")


@app.get("/detection")
def detection_page():
    return render_template("detection_page.html")


# ============================================================
# CRYPTO API
# ============================================================

@app.post("/api/crypto/<mode>")
def process_crypto(mode):

    if mode not in {"encrypt", "decrypt"}:
        return jsonify(
            error="Unsupported operation."
        ), 404

    data = request.get_json(silent=True) or {}

    text = data.get("text", "")
    key = data.get("key", "")

    if not isinstance(text, str) or not isinstance(key, str):
        return jsonify(
            error="Enter valid text and key values."
        ), 400

    try:

        if mode == "encrypt":

            result = encrypt_message(
                text,
                key
            )

        else:

            result = decrypt_message(
                text,
                key
            )

            if result == DECRYPT_ERROR:
                return jsonify(
                    error="Wrong key or invalid ciphertext."
                ), 400

    except ValueError as error:

        return jsonify(
            error=str(error)
        ), 400

    except Exception as error:

        print("Crypto error:", error)

        return jsonify(
            error="Cryptographic operation failed."
        ), 500

    return jsonify(
        result=result
    )


# ============================================================
# PURE LSB STEGANOGRAPHY — HIDE
# ============================================================

@app.post("/api/steganography/encrypt")
def steganography_encrypt():

    message = request.form.get(
        "message",
        ""
    )

    image = request.files.get(
        "image"
    )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not message.strip():

        return jsonify(
            error="Please enter a message."
        ), 400

    if image is None or image.filename == "":

        return jsonify(
            error="Please select an image."
        ), 400

    try:

        message_bytes = message.encode(
            "utf-8"
        )

        with tempfile.TemporaryDirectory() as temp_dir:

            input_path = os.path.join(
                temp_dir,
                "input_image"
            )

            output_path = os.path.join(
                temp_dir,
                "stego_image.png"
            )

            image.save(
                input_path
            )

            # ------------------------------------------------
            # HIDE MESSAGE USING LSB
            # ------------------------------------------------

            hide_data(
                input_path,
                output_path,
                message_bytes
            )

            with open(
                output_path,
                "rb"
            ) as stego_file:

                stego_image = BytesIO(
                    stego_file.read()
                )

            return send_file(
                stego_image,
                mimetype="image/png",
                as_attachment=False,
                download_name="stego_image.png"
            )

    except ValueError as error:

        return jsonify(
            error=str(error)
        ), 400

    except Exception as error:

        print(
            "Steganography encryption error:",
            error
        )

        return jsonify(
            error="Could not create the stego image."
        ), 500


# ============================================================
# PURE LSB STEGANOGRAPHY — EXTRACT
# ============================================================

@app.post("/api/steganography/decrypt")
def steganography_decrypt():

    image = request.files.get(
        "image"
    )

    if image is None or image.filename == "":

        return jsonify(
            error="Please select a stego image."
        ), 400

    try:

        with tempfile.TemporaryDirectory() as temp_dir:

            image_path = os.path.join(
                temp_dir,
                "stego_image"
            )

            image.save(
                image_path
            )

            message_bytes = extract_data(
                image_path
            )

            message = message_bytes.decode(
                "utf-8"
            )

            return jsonify(
                result=message
            )

    except UnicodeDecodeError:

        return jsonify(
            error=(
                "The image does not contain "
                "a valid hidden text message."
            )
        ), 400

    except Exception as error:

        print(
            "Steganography extraction error:",
            error
        )

        return jsonify(
            error="Could not extract the hidden message."
        ), 400


# ============================================================
# COMBINED AES + LSB — ENCRYPT
# ============================================================

@app.post("/api/combined/encrypt")
def combined_encrypt():

    message = request.form.get(
        "message",
        ""
    )

    key = request.form.get(
        "key",
        ""
    )

    image = request.files.get(
        "image"
    )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not message.strip():

        return jsonify(
            error="Please enter a message."
        ), 400

    if not key:

        return jsonify(
            error="Please enter a password."
        ), 400

    if image is None or image.filename == "":

        return jsonify(
            error="Please select a carrier image."
        ), 400

    try:

        # ----------------------------------------------------
        # AES ENCRYPTION
        # ----------------------------------------------------

        encrypted_message = encrypt_message(
            message,
            key
        )

        encrypted_bytes = encrypted_message.encode(
            "utf-8"
        )

        # ----------------------------------------------------
        # LSB HIDING
        # ----------------------------------------------------

        with tempfile.TemporaryDirectory() as temp_dir:

            input_path = os.path.join(
                temp_dir,
                "input_image"
            )

            output_path = os.path.join(
                temp_dir,
                "combined_stego.png"
            )

            image.save(
                input_path
            )

            hide_data(
                input_path,
                output_path,
                encrypted_bytes
            )

            with open(
                output_path,
                "rb"
            ) as stego_file:

                stego_image = BytesIO(
                    stego_file.read()
                )

            return send_file(
                stego_image,
                mimetype="image/png",
                as_attachment=False,
                download_name="combined_stego.png"
            )

    except ValueError as error:

        return jsonify(
            error=str(error)
        ), 400

    except Exception as error:

        print(
            "Combined encryption error:",
            error
        )

        return jsonify(
            error="Could not create the encrypted image."
        ), 500


# ============================================================
# COMBINED AES + LSB — EXTRACT CIPHERTEXT
# ============================================================

@app.post("/api/combined/extract")
def combined_extract():

    image = request.files.get(
        "image"
    )

    if image is None or image.filename == "":

        return jsonify(
            error="Please select an encrypted image."
        ), 400

    try:

        with tempfile.TemporaryDirectory() as temp_dir:

            image_path = os.path.join(
                temp_dir,
                "combined_stego_image"
            )

            image.save(
                image_path
            )

            encrypted_bytes = extract_data(
                image_path
            )

            ciphertext = encrypted_bytes.decode(
                "utf-8"
            )

            return jsonify(
                result=ciphertext
            )

    except UnicodeDecodeError:

        return jsonify(
            error=(
                "The image does not contain "
                "valid encrypted data."
            )
        ), 400

    except Exception as error:

        print(
            "Combined image extraction error:",
            error
        )

        return jsonify(
            error=(
                "Could not extract ciphertext "
                "from the image."
            )
        ), 400


# ============================================================
# STEGO DETECTION
# ============================================================

@app.post("/api/detection/analyze")
def analyze_image():

    image = request.files.get(
        "image"
    )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if image is None or image.filename == "":

        return jsonify(
            error="Please select an image to analyze."
        ), 400

    try:

        with tempfile.TemporaryDirectory() as temp_dir:

            image_path = os.path.join(
                temp_dir,
                "uploaded_image"
            )

            image.save(
                image_path
            )

            # ------------------------------------------------
            # RUN TRAINED RANDOM FOREST
            # ------------------------------------------------

            result = detect_stego(
                image_path
            )

            # ------------------------------------------------
            # SAFETY CHECK
            # ------------------------------------------------

            if not isinstance(result, dict):

                return jsonify(
                    error="Invalid detector response."
                ), 500

            required_fields = [
                "prediction",
                "label",
                "confidence",
                "probabilities",
                "feature_order",
                "features"
            ]

            missing_fields = [
                field
                for field in required_fields
                if field not in result
            ]

            if missing_fields:

                print(
                    "Missing detector fields:",
                    missing_fields
                )

                return jsonify(
                    error=(
                        "Detector returned an "
                        "incomplete response."
                    )
                ), 500

            # ------------------------------------------------
            # RETURN DETECTION RESULT
            # ------------------------------------------------

            return jsonify(
                result
            )

    except (
        UnidentifiedImageError,
        OSError,
        ValueError
    ):

        return jsonify(
            error=(
                "The uploaded file is not "
                "a valid supported image."
            )
        ), 400

    except Exception as error:

        print(
            "Stego detection error:",
            error
        )

        return jsonify(
            error=(
                "Image analysis failed. "
                "Please try again."
            )
        ), 500


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )