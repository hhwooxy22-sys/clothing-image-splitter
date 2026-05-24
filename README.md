# 🎨 Clothing Image Splitter

의류 이미지를 AI 분석에 최적화된 개별 이미지로 자동 분할하고, OCR을 통해 메타데이터를 추출하는 프로그램입니다.

## 📋 기능

- ✅ **자동 의류 영역 감지**: 이미지에서 각 의류 아이템 자동 인식
- ✅ **개별 이미지 추출**: 각 의류를 별도의 이미지 파일로 저장 (1.jpg, 2.jpg, ...)
- ✅ **OCR 텍스트 추출**: 이미지에서 브랜드명, 제품명, 가격 등 자동 추출
- ✅ **색상 감지**: 주요 색상 자동 인식 (빨강, 파랑, 초록 등)
- ✅ **패턴 인식**: 무늬 감지 (솔리드, 줄무늬, 체크 등)
- ✅ **메타데이터 저장**: 모든 정보를 JSON으로 구조화하여 저장

## 🚀 빠른 시작

### 1. 설치

```bash
# 저장소 클론
git clone https://github.com/hhwooxy22-sys/clothing-image-splitter.git
cd clothing-image-splitter

# 가상 환경 생성 (선택사항이지만 권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# Tesseract OCR 설치 (시스템 별로 다름)
# Windows: https://github.com/UB-Mannheim/tesseract/wiki에서 설치
# macOS: brew install tesseract
# Linux: sudo apt-get install tesseract-ocr
```

### 2. 사용 방법

#### 기본 사용법

```bash
# input_image.jpg 파일을 준비합니다
python main.py
```

#### Python 코드에서 직접 사용

```python
from main import ClothingImageSplitter

# 프로그램 초기화
splitter = ClothingImageSplitter(
    input_image_path="your_image.jpg",
    output_dir="output"
)

# 실행
splitter.run()
```

### 3. 출력 형식

프로그램 실행 후 `output` 디렉토리에 다음 파일들이 생성됩니다:

```
output/
├── 1.jpg                 # 첫 번째 의류 이미지
├── 2.jpg                 # 두 번째 의류 이미지
├── 3.jpg                 # 세 번째 의류 이미지
├── ...
└── metadata.json         # 모든 메타데이터
```

#### metadata.json 예시

```json
{
  "timestamp": "2024-01-20T10:30:00.000000",
  "source_image": "input_image.jpg",
  "total_items": 6,
  "items": [
    {
      "number": 1,
      "image_file": "1.jpg",
      "brand": "스트릿도래",
      "product_name": "87-STAN333 YZK 사이버 버터플라이 크레식",
      "price": "73% 9,900원",
      "discount": "73%",
      "color": "black",
      "pattern": "solid",
      "extracted_text": "스트릿도래\n87-STAN333 YZK 사이버 버터플라이 크레식\n73% 9,900원\n68명이 구매 중",
      "region": {
        "x": 10,
        "y": 20,
        "width": 250,
        "height": 350
      }
    },
    {
      "number": 2,
      "image_file": "2.jpg",
      "brand": "제너럼스",
      "product_name": "N-GS-L-888 레이어드 몽 바밀드를화",
      "price": "21,900원",
      "discount": "",
      "color": "white",
      "pattern": "solid",
      "extracted_text": "제너럼스\nN-GS-L-888 레이어드 몽 바밀드를화\n21,900원",
      "region": {
        "x": 280,
        "y": 20,
        "width": 250,
        "height": 350
      }
    }
  ]
}
```

## 📊 메타데이터 필드 설명

| 필드 | 설명 |
|------|------|
| `number` | 의류 번호 (1부터 시작) |
| `image_file` | 저장된 이미지 파일명 |
| `brand` | OCR로 추출한 브랜드명 |
| `product_name` | 제품명 |
| `price` | 가격 정보 |
| `discount` | 할인율 |
| `color` | 자동 감지된 주요 색상 |
| `pattern` | 패턴 종류 (solid, vertical_stripe, horizontal_stripe, checkered) |
| `extracted_text` | OCR로 추출한 전체 텍스트 |
| `region` | 원본 이미지에서의 위치 정보 |

## 🔧 설정 및 커스터마이징

### 의류 영역 감지 임계값 조정

`main.py`의 `detect_clothing_regions()` 메서드에서 다음을 수정:

```python
# 최소 면적 (픽셀 제곱)
if area < 5000:  # 이 값을 조정
    continue

# 종횡비 (height/width)
if aspect_ratio < 0.5 or aspect_ratio > 3:  # 범위 조정
    continue
```

### OCR 언어 설정

`extract_metadata_from_image()` 메서드에서:

```python
# 한글만: 'kor'
# 영어만: 'eng'
# 한글 + 영어: 'kor+eng' (기본값)
extracted_text = pytesseract.image_to_string(roi_pil, lang='kor+eng')
```

## 📝 요구사항

- Python 3.8 이상
- OpenCV
- Tesseract OCR (시스템 패키지)
- PIL (Pillow)
- NumPy
- Pandas

## 🐛 트러블슈팅

### Tesseract 찾을 수 없음 오류

**해결책:**
```python
# main.py 상단에 추가
import pytesseract
pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows
# pytesseract.pytesseract.pytesseract_cmd = '/usr/local/bin/tesseract'  # macOS
```

### 의류가 감지되지 않음

1. 입력 이미지 품질 확인
2. `detect_clothing_regions()` 메서드의 임계값 조정
3. 이미지 전처리 매개변수 수정

## 🎯 사용 사례

- 🛒 온라인 쇼핑몰의 의류 상품 자동 분류
- 🤖 AI 패션 추천 시스템의 훈련 데이터 전처리
- 📊 패션 트렌드 분석
- 👕 의류 카탈로그 자동화

## 📄 라이센스

MIT License

## 👤 작성자

hhwooxy22-sys

## 🤝 기여

이슈 제출이나 PR은 언제든 환영합니다!

---

**마지막 업데이트**: 2024년 1월 20일
