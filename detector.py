import os
import joblib
import numpy as np
import pandas as pd
from PIL import Image


# ============================================================
# PATH TO TRAINED MODEL
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "aes_random_forest_detector.pkl"
)


# ============================================================
# LOAD TRAINED RANDOM FOREST MODEL
# ============================================================

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"Trained model not found at:\n{MODEL_PATH}"
    )

model = joblib.load(MODEL_PATH)


# ============================================================
# FEATURE ORDER
# IMPORTANT:
# This must match the order used during training.
# ============================================================

FEATURE_ORDER = [
    "lsb_mean",
    "lsb_variance",
    "lsb_transition_rate",
    "pixel_mean",
    "pixel_variance"
]


# ============================================================
# LOAD IMAGE
# ============================================================

def load_image(image_path):

    if not os.path.exists(image_path):
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    image = Image.open(
        image_path
    ).convert("RGB")

    return np.array(image)


# ============================================================
# EXTRACT FEATURES
# ============================================================

def extract_features(image_path):

    image = load_image(
        image_path
    )

    # --------------------------------------------------------
    # LSB FEATURES
    # --------------------------------------------------------

    lsb = image & 1

    # Mean of LSB values
    lsb_mean = np.mean(
        lsb
    )

    # Variance of LSB values
    lsb_variance = np.var(
        lsb
    )

    # Horizontal LSB transition rate
    transitions = (
        lsb[:, 1:, :] !=
        lsb[:, :-1, :]
    )

    lsb_transition_rate = np.mean(
        transitions
    )

    # --------------------------------------------------------
    # PIXEL FEATURES
    # --------------------------------------------------------

    pixel_mean = np.mean(
        image
    )

    pixel_variance = np.var(
        image
    )

    # --------------------------------------------------------
    # RETURN FEATURES
    # --------------------------------------------------------

    return {
        "lsb_mean": float(
            lsb_mean
        ),

        "lsb_variance": float(
            lsb_variance
        ),

        "lsb_transition_rate": float(
            lsb_transition_rate
        ),

        "pixel_mean": float(
            pixel_mean
        ),

        "pixel_variance": float(
            pixel_variance
        )
    }


# ============================================================
# DETECT STEGO
# ============================================================

def detect_stego(image_path):

    # --------------------------------------------------------
    # STEP 1: EXTRACT FEATURES
    # --------------------------------------------------------

    features = extract_features(
        image_path
    )

    # --------------------------------------------------------
    # STEP 2: CREATE DATAFRAME
    #
    # The model was trained using feature names.
    # Using a DataFrame avoids the sklearn warning:
    #
    # "X does not have valid feature names"
    # --------------------------------------------------------

    X = pd.DataFrame(
        [
            [
                features[name]
                for name in FEATURE_ORDER
            ]
        ],
        columns=FEATURE_ORDER
    )

    # --------------------------------------------------------
    # STEP 3: MODEL PREDICTION
    # --------------------------------------------------------

    prediction = int(
        model.predict(X)[0]
    )

    # --------------------------------------------------------
    # STEP 4: MODEL PROBABILITIES
    # --------------------------------------------------------

    probabilities = model.predict_proba(
        X
    )[0]

    class_probabilities = {
        int(class_value): float(probability)

        for class_value, probability in zip(
            model.classes_,
            probabilities
        )
    }

    # --------------------------------------------------------
    # VERIFIED CLASS MAPPING
    #
    # We tested your actual model:
    #
    # original.jpg:
    # prediction = 0
    # probability class 0 = 83%
    #
    # stego.png:
    # prediction = 1
    # probability class 1 = 96%
    #
    # Therefore:
    #
    # 0 = Cover
    # 1 = Stego
    # --------------------------------------------------------

    if prediction == 0:

        label = "Cover Image"

    elif prediction == 1:

        label = "Stego Image"

    else:

        label = "Unknown"


    # --------------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------------

    confidence = (
        class_probabilities
        .get(prediction, 0.0)
        * 100
    )


    # --------------------------------------------------------
    # RETURN COMPLETE RESULT
    # --------------------------------------------------------

    return {

        # Raw model prediction
        "prediction": prediction,

        # Human-readable prediction
        "label": label,

        # Confidence of predicted class
        "confidence": round(
            confidence,
            2
        ),

        # Both class probabilities
        "probabilities": {

            "cover": round(
                class_probabilities.get(
                    0,
                    0.0
                ) * 100,
                2
            ),

            "stego": round(
                class_probabilities.get(
                    1,
                    0.0
                ) * 100,
                2
            )
        },

        # IMPORTANT:
        # Frontend expects this.
        "feature_order": FEATURE_ORDER,

        # Extracted feature values
        "features": {

            "lsb_mean": round(
                features["lsb_mean"],
                6
            ),

            "lsb_variance": round(
                features["lsb_variance"],
                6
            ),

            "lsb_transition_rate": round(
                features["lsb_transition_rate"],
                6
            ),

            "pixel_mean": round(
                features["pixel_mean"],
                6
            ),

            "pixel_variance": round(
                features["pixel_variance"],
                6
            )
        }
    }