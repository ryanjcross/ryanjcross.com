"""Regenerate the selectable overlay after replacing the resume PDF/image pair."""
import json
from pathlib import Path
import pdfplumber

root = Path(__file__).resolve().parents[1]
with pdfplumber.open(root / "public/Ryan-Cross-Resume.pdf") as pdf:
    page = pdf.pages[0]
    words = page.extract_words(x_tolerance=1)
    data = {
        "width": page.width,
        "height": page.height,
        "words": [
            {
                "text": word["text"],
                "x": round(word["x0"], 3),
                "y": round(word["top"], 3),
                "width": round(word["x1"] - word["x0"], 3),
                "size": round(word["bottom"] - word["top"], 3),
            }
            for word in words
        ],
    }
(root / "src/data/resume-text.json").write_text(
    json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
)
