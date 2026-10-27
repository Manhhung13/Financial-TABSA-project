"""Step 1: Load XLM-R base and test a CUDA BF16 forward pass, no training."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('HF_HOME', str(ROOT / '.hf_cache'))

import torch
from transformers import AutoModel, AutoTokenizer

MODEL_ID = 'FacebookAI/xlm-roberta-base'


def main() -> None:
    print('Project:', ROOT)
    print('PyTorch:', torch.__version__)
    print('CUDA available:', torch.cuda.is_available())
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA is unavailable in the active .venv. Stop here.')
    print('GPU:', torch.cuda.get_device_name(0))
    props = torch.cuda.get_device_properties(0)
    print('GPU VRAM GiB:', round(props.total_memory / 1024**3, 2))
    print('BF16 supported:', torch.cuda.is_bf16_supported())
    print('Model checkpoint:', MODEL_ID)
    print('HF model cache:', os.environ['HF_HOME'])
    print('Loading weights (the first run downloads a large checkpoint)...')
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModel.from_pretrained(MODEL_ID, use_safetensors=True)
    model = model.to('cuda').eval()
    sentence = 'HPG ghi nhan loi nhuan tang 25 phan tram trong quy III.'
    query = 'Company: HPG. Aspect: financial performance.'
    inputs = tokenizer(sentence, text_pair=query, max_length=96,
                       truncation=True, return_tensors='pt')
    inputs = {k: v.to('cuda') for k, v in inputs.items()}
    torch.cuda.reset_peak_memory_stats()
    with torch.inference_mode():
        if torch.cuda.is_bf16_supported():
            with torch.autocast('cuda', dtype=torch.bfloat16):
                outputs = model(**inputs)
        else:
            outputs = model(**inputs)
    print('Last hidden state:', tuple(outputs.last_hidden_state.shape))
    print('Peak allocated VRAM GiB:', round(torch.cuda.max_memory_allocated()/1024**3, 3))
    print('Peak reserved VRAM GiB:', round(torch.cuda.max_memory_reserved()/1024**3, 3))
    print('STEP 1 OK: XLM-R forward pass succeeded on GPU.')
    print('Note: pretrained XLM-R does not yet predict sentiment labels.')


if __name__ == '__main__':
    main()
