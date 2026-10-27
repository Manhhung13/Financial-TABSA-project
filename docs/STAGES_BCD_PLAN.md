# Ke hoach giai doan B, C, D sau Stage A

## Nguyen tac

- XLM-R encoder/LoRA la phan kien thuc duoc chuyen giua cac giai doan.
- Khong giu lai head output MLM cua A cho B; khong su dung head 3 nhan B de du doan truc tiep aspect Thai.
- Moi dataset co schema rieng; phai train head dung don vi nhan.
- Gold test la tin VI co nhan human verified va duoc khoa truoc thuc nghiem.

## Giai doan B - Entity sentiment, tieng Anh (SEntFiN)

Nguon: data/processed/en_sentfin_entity_sentiment.csv duoc tao boi scripts/03_audit_prepare.py.
Mot headline co nhieu target -> nhieu samples. Chia train/validation theo headline/source_id truoc khi tach target.
Input A: original English headline; Input B: company target. Output: NEG/NEU/POS.
Khoi tao XLM-R sequence classification 3 classes va nap LoRA adapter A vao encoder; classifier 3 classes moi.
Train/validation Macro-F1, F1 nhom multi-entity. Luu encoder adapter B va classifier B cung metadata label2id.

## Giai doan C - Thai financial aspect sentiment

README chinh thuc cua nguon Thai cho biet MOT DOAN VAN co the co NHIEU ASPECT. Can audit file CSV thuc su xem:
(1) moi row = mot cap aspect-sentiment cua cung paragraph, hay
(2) mot row chua nhieu aspect/sentiment dang list.

Khong mac dinh '16-class softmax + sentiment 3-class' la chinh xac cho moi truong hop.
Neu mot row tuong ung voi cap (paragraph, aspect, sentiment): duong de lam nhat la dau vao dang text pair
    (paragraph, 'Aspect: <Thai aspect>') -> 3-class sentiment,
va mot head/bo du doan phat hien aspect present neu co nhan absence.
Neu can nhan 16 aspect dong thoi cho moi doan: 16-dim sigmoid/multi-label BCE;
sentiment phai co dieu kien aspect, khong dung 1 global sentiment cho doan nhieu aspect.

Chuyen encoder/adapter B, khoi tao heads dung Thai dataset. Luu encoder adapter C.
Thu so sanh khong C / co C tren cung Gold VI.

## Giai doan D - Vietnamese Gold (bat buoc truoc khi deploy)

Nguon: human-verified Gold co (article_group, text, ticker, aspect, presence, sentiment_if_present, evidence)
Input: (Vietnamese context, target company + one of 5 finance aspects).
Output 1: presence yes/no. Output 2: NEG/NEU/POS khi present = yes.
Loss: BCE(presence) cho nhan presence da xac minh va masked CE(sentiment) chi khi aspect present va sentiment duoc xac minh.
Khong coi score 0 cua LLM la absent hay neutral. Silver chi dung train (neu co kiem soat) va khong bao gio dung lam test chuan.

Ablation: E0 XLM-R + Gold; E1 A+Gold; E2 B+Gold; E3 C+Gold; E4 A+B+C+Gold.
Stage C co the gay quen stage B, can giu baseline co/khong co C.
Metric: Macro-F1 sentiment when aspect present, presence F1, end-to-end triple F1, theo aspect, nhom nhieu entities; 3 seeds cho top 2.

## Co dieu trong bao cao 5 trang can sua

- Muc 2.1 viet phobert_dataset.csv 'Dung de test model': KHONG DUNG. Day la nhan LLM = silver (nguoi dung da xac nhan).
- Luong 'A -> B -> C -> FastAPI' phai la 'A -> B -> C -> D Gold fine-tune -> FastAPI'.
- Giai doan C phai audit nhan multi-aspect thuc te; head 16 softmax chi hop le neu moi training sample co dung 1 aspect.
- Phan chi tiet D chua co trong ban 5 trang; can bo sung kieu nhan presence/sentiment va evaluation.
