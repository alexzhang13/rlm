# VLM extension for Recursive Language Models (RLMs)

This repository extends the [Recursive Language Models (RLMs)](https://github.com/alexzhang13/rlm) with support for vision-language models (VLMs), allowing images and PDFs to be passed in together with the query. The examples and tests for this implementation make use of US Congressional documents.

<h3>VLM Example: Congressional Document Analysis</h3>
<p>RLM with VLM support can reason over scanned documents,
tables, and figures that are not extractable as indexed
  text.</p>

<table>
    <tr>
      <td align="center" width="33%">
        <img src="media/doc1.png" width="100%" alt="Congressional
   document page 1"/>
        <br/><sub>Congressional Research Service (CRS) document about the situation in Venezuela, 2022</sub>
      </td>
      <td align="center" width="33%">
        <img src="media/doc2.png" width="100%" alt="Congressional
   document page 2"/>
        <br/><sub>CRS document about the situation in Yemen, 2026</sub>
      </td>
      <td align="center" width="33%">
        <img src="media/doc3.png" width="100%" alt="Congressional
   document page 3"/>
        <br/><sub>A scan of the letter inside a committee report of the House Natural Resources Committee</sub>
      </td>
    </tr>
</table>

**Disclaimer**: This extension is **OpenAI client only** for the moment and **only works in a Docker environment**.

## Overview of the Extension

Now, PDFs and images (JPG/JPEG/PNG) can be passed to the new `prompt/` directory that contains all the files that come with the prompt:

```
prompt/    
  ├──pdfs/                                                   
  │   ├── doc1.pdf                                          
  │   └── doc2.pdf
  └──images/
      ├── img1.png                                  
      ├── img2.jpeg
      └── img3.jpg
```

These files get loaded during the start-up of the Docker container (see `Dockerfile.vlm`).

We changed the signature of the `llm_query` and the `llm_query_batched` methods to accept paths and lists of paths to images:

```python
llm_query(prompt: str, image_paths: List[str] = None, **kwargs)
llm_query_batched(prompts: List[str], image_path_lists: List[List[str]] = None, **kwargs)
```

These image paths then get encoded to data URI's inside the container and then passed to the OpenAI client on the host machine. The original idea was to lazy load the images on the host machine, but this is not possible since the host machine does not have access to the filesystem container.

## How To Run the Example

1. Clone this repository
```bash
git clone https://github.com/famitzsy8/rvlm.git
```

2. Build the Docker image
```bash
docker build -t rlm-vlm-tryout -f Dockerfile.vlm .
```

3. Set your OpenAI API key in your terminal
```bash
export OPENAI_API_KEY=your_openai_api_key
```

4. Run the script (by default with `gpt-5.2`)
```bash
uv run python -m examples.vlm_example
```

## How to Run the Tests

We have 4 `pytest` fixtures inside of `tests/vlm/fixtures/`:

- `test_one_image`: Tests a prompt with a single image
- `test_n_images`: Tests a prompt with multiple images
- `test_pdf2image`: Tests a prompt with a PDF (and if the model can convert the PDF to images)
- `test_supported_formats`: Tests the prompt with 3 images of the different supported formats (JPG, JPEG, PNG)

1. Clone this repository
```bash
git clone https://github.com/famitzsy8/rvlm.git
```
2. Set the OpenAI API key in your terminal
```bash
export OPENAI_API_KEY=your_openai_api_key
```
3. Run the tests
```bash
make test-vlm
```
If you want to see the output of the tests (that can be quite long) wrap them into this command:
```bash
make test-vlm 2>&1 | tee test-vlm.txt
```
This ensures that you have all the output saved, but see it live when running the tests from your terminal.

## A Note on the Examples and the Tests

The prime motivation for this extension was my own quest to process large and complex documents from the United States Congress without polluting context. Most of the nitty-gritty details happen in hearings and are logged onto committee reports that can be long with multiple figures, tables and explanatory images. Now it is possible to detect and look at figures with the VLMs.

## Unhandled Features

- Currently we can ONLY use OpenAI models that support images as input. You can find the input descriptions for the OpenAI models [here](https://developers.openai.com/api/docs/models). Selection of a non-VLM model or a model not from OpenAI will raise errors.