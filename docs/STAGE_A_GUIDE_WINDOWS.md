# Giai đoạn A - XLM-RoBERTa DAPT/MLM - RTX 4050 6 GB

## Mục tiêu

Tiếp tục huấn luyện encoder đa ngôn ngữ `FacebookAI/xlm-roberta-base` bằng masked language modeling (MLM) trên tin tài chính tiếng Việt. Đây là **học không giám sát trên văn bản**, không học nhãn sentiment, ticker hay aspect. Mỗi giai đoạn B/C/D sẽ có head dự đoán khác nhau. Thí nghiệm chính phải đối chiếu E0 (không DAPT) và E1 (có DAPT) trên cùng Gold test.

## Điều kiện cần

Đã tạo `D:\financial-tabsa\.venv`; lệnh torch CUDA=True; transformers 4.56.1, peft 0.17.1, datasets 3.6.0, accelerate 1.10.1. Đồng thời phải chuẩn bị ít nhất file `data\processed\vi_company_dapt_candidates.csv` bằng 02_download + 03_audit_prepare thuộc kit trước.

Tệp Gold: `data\gold\article_pool_to_verify.csv` (nếu đã chạy 04_create_gold_review.py). Script A sẽ tự loại **trùng nội dung chuẩn hóa hoàn toàn** với file Gold này. Các tin gần trùng và cùng sự kiện **vẫn cần kiểm tra bổ sung**. Để làm kết quả nghiên cứu cuối cùng, cần khóa test Gold theo bài/sự kiện rồi loại toàn bộ dữ liệu giao thoa ra khỏi cả corpus MLM.

## Lệnh chạy (PowerShell trong D:\financial-tabsa)

```powershell
.\.venv\Scripts\Activate.ps1
python scripts\05_train_stage_A_dapt.py --mode prepare
python scripts\05_train_stage_A_dapt.py --mode smoke
```

Bước `prepare` chỉ phân tách corpus thành tài liệu train/MLM validation (95/5, đã khử trùng nguyên văn và loại một số tài liệu Gold nếu tìm thấy). Bước `smoke` tải checkpoint XLM-R, chuẩn hóa tokenizer, tạo các cửa sổ 128 token, huấn luyện LoRA trong 5 optimizer steps. Đây là phép thử kỹ thuật, **không** được dùng để kết luận DAPT cải thiện sentiment.

Trước khi chạy trên toàn corpus, cần có file Gold/heldout và kiểm tra nguồn dữ liệu:

```powershell
python scripts\05_train_stage_A_dapt.py --mode train --max-steps 400
```

Nếu VRAM lỗi OOM: đóng trình duyệt và Docker; thử `--max-length 96`, hoặc `--grad-accum 8` (gradient accumulation không phải nguyên nhân chính tăng VRAM vì per-device batch=1). Nếu vẫn OOM, dừng lại để điều chỉnh kỹ thuật và/hoặc sử dụng GPU cloud. Đừng tự bật FP32 full fine-tuning trên máy 6 GB.

## Đầu ra

- `data\processed\stage_A\train_documents.csv` và `validation_documents.csv`.
- `data\processed\stage_A\prepare_manifest.json`.
- `experiments\stage_A_xlmr_lora_mlm\smoke\adapter_A` (chạy thử).
- `experiments\stage_A_xlmr_lora_mlm\pilot_steps\adapter_A` (chạy 400 steps) hoặc `full_epoch\adapter_A` (chạy hết epoch).
- `experiments\stage_A_xlmr_lora_mlm\full\run_manifest.json` (GPU, config, MLM eval loss).

Adapter chỉ chứa trọng số LoRA thay đổi trên encoder; không phải classifier. Sang giai đoạn B phải khởi tạo sequence classification head 3 lớp mới và nạp adapter tương thích. Sang giai đoạn C sử dụng heads khác cho 16 khía cạnh và 3 sentiment tiếng Thái. Giai đoạn D có presence head và sentiment head theo Gold Việt. Không nên dùng ngay `from_pretrained` với đầu ra 3 lớp của stage B để dự đoán 5 aspect.

## Dấu hiệu thành công

Dòng cuối `STAGE A OK: smoke` hoặc `STAGE A OK: train`, `MLM eval_loss`, `Peak GPU allocated GiB`, adapter `adapter_model.safetensors` và `adapter_config.json` tồn tại.

## Gửi lại để sang giai đoạn B

Gửi ảnh/copy các dòng `[CHUNKS]`, `[RESULT] MLM eval_loss`, `[RESULT] Peak GPU`, `[SAVED]`, `STAGE A OK`. Nếu có lỗi, gửi 30 dòng lỗi cuối.

## Các thay đổi bắt buộc khi làm đồ án khoa học

1. Bộ `phobert_dataset.csv` là **Silver** vì nhãn do LLM tạo, không được dùng trực tiếp làm Gold test.
2. Dataset Thái trong README cho biết một đoạn **có thể chứa nhiều aspect**, không được ép tất cả về single-label classification nếu chưa phân tích phân bố. Head Thái phải khớp đơn vị nhãn thực tế.
3. Bản báo cáo 5 trang có mô tả A/B/C, nhưng phần D chưa được trình bày chi tiết trong các trang hiện có và sơ đồ C -> FastAPI còn thiếu D. Kết quả cuối phải dự đoán `aspect_present` và `sentiment_if_present` từ Gold Việt.
4. LoRA MLM dùng `learning_rate=1e-4` là cấu hình thử kỹ thuật phù hợp train adapter, khác dải learning rate `1e-5 ~ 3e-5` của báo cáo dành cho huấn luyện toàn bộ encoder. Cần báo rõ và so sánh trên validation.

## Phan biet 400 steps va 1 epoch

`--mode train --max-steps 400` la *pilot DAPT 400 optimizer updates*, KHONG bao dam doc het corpus. Neu Gold holdout da duoc khoa va cac canh bao overlap da xu ly, co the chay mot epoch tren toan bo cac chunk nhu sau (se nang hon nhieu):

```powershell
python scripts\05_train_stage_A_dapt.py --mode train --full-epoch --epochs 1
```

Che do `--full-epoch` dat `max_steps=-1`, nen `Trainer` su dung so epoch chi dinh; checkpoint duoc luu rieng trong `experiments/stage_A_xlmr_lora_mlm/full_epoch/adapter_A`. Tren laptop 6 GB, can theo doi nhiet do va nguon dien va du tru thoi gian.
