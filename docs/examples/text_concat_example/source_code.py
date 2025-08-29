
from pathlib import Path
# --- Hardcoded paths ---
FILE1 = Path(IN_1)
FILE2 = Path(IN_2)
OUT = Path(OUT_RESULT.TXT)
# Read files
text1 = FILE1.read_text(encoding="utf-8")
text2 = FILE2.read_text(encoding="utf-8")
# Concatenate (ensure a single newline between if file1 doesn't end with one)
if text1 and not text1.endswith("\n") and text2:
    combined = text1 + "\n" + text2
else:
    combined = text1 + text2
# Write output
OUT.write_text(combined, encoding="utf-8")
print(f"Combined into: {OUT}")
