# 이미지 전송 최적화 제안

## 현재 상황
- 모든 이미지를 base64로 인코딩하여 전송
- 이미지 크기가 33% 증가 (base64 오버헤드)
- 작은 모델(llava:7b, llava:13b)에서 컨텍스트 제한 문제 가능

## 문제점
1. **토큰 소비**: 1MB 이미지 → 1.33MB base64 → 많은 토큰 사용
2. **컨텍스트 제한**: MAX_TOKENS=300 설정 시 긴 응답 불가
3. **비용**: API 모드에서 불필요한 비용 증가

## 개선 방안

### 방안 1: API별 조건부 이미지 전송 (추천)

#### OpenAI API 모드
```python
# 이미지를 임시 HTTP 서버에 올리거나 공개 URL 사용
{
  "type": "image_url",
  "image_url": {
    "url": "https://example.com/temp/screenshot.png"
  }
}
```

#### Ollama Local 모드
```python
# 계속 base64 사용 (필수)
{
  "type": "image_url",
  "image_url": {
    "url": "data:image/jpeg;base64,{base64}"
  }
}
```

**장점:**
- OpenAI 사용 시 토큰 비용 대폭 감소
- Ollama는 기존 방식 유지 (호환성)

**단점:**
- 임시 HTTP 서버 필요 (또는 클라우드 스토리지)

---

### 방안 2: 이미지 압축 최적화

#### 스크린샷 크기 줄이기
```python
def optimize_image(image_path, max_size=(1280, 720), quality=85):
    """
    이미지 크기와 품질 최적화

    - 해상도 제한: 1280x720 (config에서 설정)
    - JPEG 품질: 85% (시각적 품질 유지)
    - 예상 절감: 50-70%
    """
    img = cv2.imread(image_path)
    h, w = img.shape[:2]

    # 리사이즈
    if w > max_size[0] or h > max_size[1]:
        ratio = min(max_size[0]/w, max_size[1]/h)
        new_size = (int(w*ratio), int(h*ratio))
        img = cv2.resize(img, new_size, interpolation=cv2.INTER_AREA)

    # JPEG 압축
    cv2.imwrite(image_path, img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return image_path
```

**장점:**
- 간단한 구현
- 즉시 적용 가능
- 양쪽 API 모두 혜택

**단점:**
- 여전히 base64 오버헤드 존재

---

### 방안 3: 하이브리드 접근 (최적 솔루션)

```python
class OpenAIModel(BaseModel):
    def __init__(self, base_url, api_key, model, temperature, max_tokens,
                 use_image_url=False, image_server_url=None):
        # ...
        self.use_image_url = use_image_url  # API 모드에서만 True
        self.image_server_url = image_server_url

    def get_model_response(self, prompt, images):
        content = [{"type": "text", "text": prompt}]

        for img in images:
            # 이미지 최적화 (항상)
            optimized_img = optimize_image(img)

            if self.use_image_url and self.image_server_url:
                # API 모드: HTTP URL 사용
                temp_url = upload_to_temp_server(optimized_img)
                content.append({
                    "type": "image_url",
                    "image_url": {"url": temp_url}
                })
            else:
                # Local 모드: base64 사용
                base64_img = encode_image(optimized_img)
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_img}"
                    }
                })
```

#### Config 설정
```yaml
# API 모드 (OpenAI, OpenRouter)
MODEL: "api"
API_BASE_URL: "https://api.openai.com/v1/chat/completions"
USE_IMAGE_URL: true  # HTTP URL 사용
IMAGE_SERVER_URL: "http://localhost:8000"  # 임시 서버

# Local 모드 (Ollama)
MODEL: "local"
USE_IMAGE_URL: false  # base64 사용 (필수)

# 이미지 최적화 설정
IMAGE_MAX_WIDTH: 1280
IMAGE_MAX_HEIGHT: 720
IMAGE_QUALITY: 85  # JPEG 품질 (1-100)
```

---

## 성능 비교

### 예시: 1920x1080 스크린샷 (2MB)

| 방식 | 이미지 크기 | 전송 크기 | 토큰 예상 | 비고 |
|------|-----------|----------|----------|------|
| **원본 base64** | 2MB | 2.66MB | ~2000 | 현재 방식 |
| **최적화 + base64** | 600KB | 800KB | ~600 | 70% 감소 |
| **HTTP URL** | 600KB | 50 bytes | ~2 | 99.9% 감소 |

---

## 추천 구현 단계

### 단계 1: 이미지 최적화 추가 (즉시 적용 가능)
- `utils.py`에 `optimize_image()` 함수 추가
- `get_screenshot()` 후 자동 최적화
- **예상 효과**: 토큰 50-70% 감소

### 단계 2: HTTP URL 지원 (선택적)
- 간단한 임시 파일 서버 구현
- API 모드에서만 활성화
- **예상 효과**: API 비용 99% 감소

### 단계 3: Config 통합
- `USE_IMAGE_URL` 설정 추가
- 플랫폼별 자동 선택

---

## 임시 HTTP 서버 예시

```python
# scripts/temp_image_server.py
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import os

class TempImageServer:
    def __init__(self, port=8000, directory="./temp_images"):
        self.port = port
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

    def start(self):
        os.chdir(self.directory)
        handler = SimpleHTTPRequestHandler
        self.httpd = HTTPServer(("localhost", self.port), handler)
        thread = threading.Thread(target=self.httpd.serve_forever)
        thread.daemon = True
        thread.start()

    def get_url(self, filename):
        return f"http://localhost:{self.port}/{filename}"
```

---

## 결론

1. **즉시 적용 가능**: 방안 2 (이미지 압축) 구현
2. **장기 솔루션**: 방안 3 (하이브리드) 구현
3. **트레이드오프**:
   - Local 모드는 base64 필수
   - API 모드는 HTTP URL로 큰 비용 절감 가능

## 다음 단계

어떤 방안을 구현할까요?
1. 이미지 최적화만 먼저 추가 (간단)
2. 하이브리드 방식 전체 구현 (최적)
3. 다른 접근 방식 논의
