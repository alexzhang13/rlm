FROM python:3.11-slim
# that is where I would have added the transformers library
RUN pip install requests dill pymupdf pillow pytesseract

RUN mkdir -p /workspace /prompt/images /prompt/pdfs /tmp/rlm_images /tmp/rlm_pdfs

# Build with: docker build --build-arg FIXTURE=test_one_image -t rlm-vlm-test-one-image .
ARG FIXTURE

COPY ./tests/vlm/fixtures/${FIXTURE}/images /prompt/images
COPY ./tests/vlm/fixtures/${FIXTURE}/pdfs /prompt/pdfs

WORKDIR /workspace

CMD ["tail", "-f", "/dev/null"]
