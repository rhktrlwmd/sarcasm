from __future__ import annotations

import json

import streamlit as st

from src.config import METADATA_PATH
from src.predict import predict_text

st.set_page_config(page_title="Sarcasm Detection", layout="centered")

st.title("Sarcasm Detection System")
st.write(
    "Enter text in English or Russian. The current coursework version is trained primarily for these two languages."
)

user_text = st.text_area(
    "Input text",
    height=180,
    placeholder="Great, another Monday morning...",
)

if st.button("Predict sarcasm", type="primary"):
    if not user_text.strip():
        st.warning("Please enter some text before running the prediction.")
    else:
        try:
            result = predict_text(user_text)
            st.subheader("Prediction")
            if result["prediction"] == "Uncertain":
                st.warning("Uncertain")
                st.caption(f"Binary fallback: {result['binary_prediction']}")
            elif result["label"] == 1:
                st.error("Sarcastic")
            else:
                st.success("NotSarcastic")

            st.metric("Sarcasm probability", f"{result['probability']:.2%}")
        except FileNotFoundError as error:
            st.warning(str(error))

st.subheader("Model information")
if METADATA_PATH.exists():
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    st.json(metadata)
else:
    st.info("Model metadata not found yet. Train the model first using `python main.py` or `python -m src.train`.")
