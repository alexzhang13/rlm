import os

from dotenv import load_dotenv

from rlm import RLM
from rlm.logger import RLMLogger
import rlm as rlm_pkg
print(f"RLM package location: {rlm_pkg.__file__}")

load_dotenv()

logger = RLMLogger(log_dir="./logs")

rlm = RLM(
    backend="openai",  # or "portkey", etc.
    backend_kwargs={
        "model_name": "gpt-5.2",
        "api_key": os.getenv("OPENAI_API_KEY"),
    },
    environment="docker",
    environment_kwargs={
        "image": "rlm-vlm-tryout",
        "setup_code": "import shutil; shutil.copytree('/prompt', '/workspace/prompt')"
    },
    max_depth=1,
    logger=logger,
    verbose=True,  # For printing to console with rich, disabled by default.
)


prompt = """
# Committee Report Analysis

You are given a committee report from the Committee on House Administration of the 119th United States Congress about "STOP INSIDER TRADING ACT". Your task is to search for any tables or elements that are not indexed text in the detailed document. Wherever a point with "(ACTION X)" exists, is where you can find the actionable tasks you have to do.

## The PDF in question

The committee report resides in `/prompt/pdfs/cr.pdf`.

## Methodology

A committee report is an intricate document that can contain:

- Text that is already indexed and readily extractable (Type I)
- Text that is not indexed and isn't extractable by any libraries (Type II)
- Figures (Type III)
- Tables (Type IV)
- Numerical Graphics (Type V)

Thus the following methodology describes the manner to 1. mapping the structure by finding the elements of Types II to V and 2. extract the semantics from elements of Types II to V.

### Mapping the Structure

To map the structure and to find the elements we will first do these tasks:

(ACTION 1): Extract the page length of the document
(ACTION 2): Extract the indexed text (Type I) of the document
(ACTION 3): Map the indexed text to the page numbers
(ACTION 4): Based on the quantity of indexed text per page number, select the page numbers that possibly can contain elements of Types II to V (a lot of indexed text --> less proable, no or little indexed text --> more probable)

### Libraries

Use `pymupdf` (import as `pymupdf`) to accomplish the above. `pillow` is also available if you want to do image processing. Here are the specific
instructions:

#### ACTION 1: Extract Page Length

```python
import pymupdf

doc = pymupdf.open('/prompt/pdfs/cr.pdf')
total_pages = len(doc)
print(f"Total pages: {total_pages}")
```

ACTION 2 & 3: Extract Indexed Text and Map to Pages
```python
import pymupdf

doc = pymupdf.open('/workspace/cr.pdf')

# Dictionary to store text per page
pages_text = {}
pages_with_content = []
pages_without_content = []

for page_num in range(len(doc)):
  page = doc[page_num]
  text = page.get_text()  # Extract indexed text only
  pages_text[page_num] = text

  # Track which pages have meaningful indexed text
  if len(text.strip()) > SOME_THRESHOLD: # Threshold: meaningful content
      pages_with_content.append(page_num)
  else:
      pages_without_content.append(page_num)

print(f"Pages with indexed text: {pages_with_content}")
print(f"Pages without indexed text (need VLM analysis): {pages_without_content}")
```
ACTION 4: Identify Pages with Types II-V Content

# Pages with little or no indexed text likely contain:
# - Type II: Non-indexed text (scanned/image text)
# - Type III: Figures
# - Type IV: Tables
# - Type V: Numerical graphics/charts
```python
pages_needing_vlm = pages_without_content
print(f"\nPages requiring VLM analysis for Types II-V: {pages_needing_vlm}")
print(f"Total pages needing VLM: {len(pages_needing_vlm)}")
print(f"Total pages with indexed text: {len(pages_with_content)}")
```
"""

result = rlm.completion(prompt)

print(result)
