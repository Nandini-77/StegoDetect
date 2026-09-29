import os
import joblib
import numpy as np
from PIL import Image


# ============================================================
# 1. MODEL PATH
# ============================================================

MODEL_PATH = "aes_random_forest_detector.pkl"


# ============================================================
# 2. LOAD TRAINED MODEL
# ============================================================

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"Model not found at: {MODEL_PATH}\n"
        "Make sure aes_random_forest_detector.pkl is inside the models folder."
    )

model = joblib.load(MODEL_PATH)

print("=" * 60)
print("MODEL INFORMATION")
print("=" * 60)

print("Model type:", type(model).__name__)
print("Model classes:", model.classes_)

if hasattr(model, "n_estimators"):
    print("Number of trees:", model.n_estimators)

print()


# ============================================================
# 3. FEATURE EXTRACTION
# ============================================================

def load_image(image_path):

    if not os.path.exists(image_path):
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    image = Image.open(image_path).convert("RGB")

    return np.array(image)


def extract_features(image_path):

    image = load_image(image_path)

    # --------------------------------------------------------
    # LSB features
    # --------------------------------------------------------

    lsb = image & 1

    lsb_mean = np.mean(lsb)

    lsb_variance = np.var(lsb)

    transitions = (
        lsb[:, 1:, :] !=
        lsb[:, :-1, :]
    )

    lsb_transition_rate = np.mean(transitions)

    # --------------------------------------------------------
    # Pixel features
    # --------------------------------------------------------

    pixel_mean = np.mean(image)

    pixel_variance = np.var(image)

    # --------------------------------------------------------
    # IMPORTANT:
    # Keep the same feature names/order used during training.
    # --------------------------------------------------------

    features = {
        "lsb_mean": float(lsb_mean),
        "lsb_variance": float(lsb_variance),
        "lsb_transition_rate": float(lsb_transition_rate),
        "pixel_mean": float(pixel_mean),
        "pixel_variance": float(pixel_variance)
    }

    return features


# ============================================================
# 4. FEATURE ORDER
# ============================================================

FEATURE_ORDER = [
    "lsb_mean",
    "lsb_variance",
    "lsb_transition_rate",
    "pixel_mean",
    "pixel_variance"
]


# ============================================================
# 5. TEST ONE IMAGE
# ============================================================

def test_image(image_path, expected_type):

    print("=" * 60)
    print("IMAGE TEST")
    print("=" * 60)

    print("Image:", image_path)
    print("Expected:", expected_type)
    print()

    # --------------------------------------------------------
    # Extract features
    # --------------------------------------------------------

    features = extract_features(image_path)

    print("Extracted Features:")
    print("-------------------")

    for name in FEATURE_ORDER:
        print(
            f"{name:25s}: {features[name]:.10f}"
        )

    print()

    # --------------------------------------------------------
    # Create model input
    # --------------------------------------------------------

    X = np.array([
        [features[name] for name in FEATURE_ORDER]
    ])

    print("Feature vector:")
    print(X)

    print()

    # --------------------------------------------------------
    # Raw prediction
    # --------------------------------------------------------

    prediction = model.predict(X)[0]

    print("Raw model prediction:", prediction)

    # --------------------------------------------------------
    # Probabilities
    # --------------------------------------------------------

    if hasattr(model, "predict_proba"):

        probabilities = model.predict_proba(X)[0]

        print()
        print("Model probabilities:")

        for class_value, probability in zip(
            model.classes_,
            probabilities
        ):

            print(
                f"Class {class_value}: "
                f"{probability * 100:.2f}%"
            )

    else:

        probabilities = None

        print("Model does not provide predict_proba().")

    print()

    # --------------------------------------------------------
    # IMPORTANT:
    # DO NOT assume 0 = Cover or 1 = Stego yet.
    # --------------------------------------------------------

    print("Raw prediction only:")
    print("Prediction =", prediction)

    print()

    return prediction, probabilities


# ============================================================
# 6. PUT YOUR IMAGE PATHS HERE
# ============================================================

# CHANGE THESE TWO PATHS.

COVER_IMAGE = r"test_images\original.jpg"

STEGO_IMAGE = r"test_images\stego.png"


# ============================================================
# 7. TEST COVER IMAGE
# ============================================================

print()
print()
print("###############################")
print("# TESTING KNOWN COVER IMAGE")
print("###############################")
print()

cover_prediction, cover_probabilities = test_image(
    COVER_IMAGE,
    "COVER"
)


# ============================================================
# 8. TEST STEGO IMAGE
# ============================================================

print()
print()
print("###############################")
print("# TESTING KNOWN STEGO IMAGE")
print("###############################")
print()

stego_prediction, stego_probabilities = test_image(
    STEGO_IMAGE,
    "STEGO"
)


# ============================================================
# 9. FINAL RAW COMPARISON
# ============================================================

print()
print()
print("=" * 60)
print("FINAL COMPARISON")
print("=" * 60)

print("Known Cover image prediction:", cover_prediction)
print("Known Stego image prediction:", stego_prediction)

print()

print(
    "IMPORTANT: We are NOT converting 0/1 into "
    "Cover/Stego yet."
)

print(
    "We first need to verify how the training labels "
    "were assigned."
)

print("=" * 60)