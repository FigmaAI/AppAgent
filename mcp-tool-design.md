# MCP 기반 리팩토링 프로젝트 설계

## 1. 새로운 MCP 도구 정의

### 1.1. `self_explorer-browser`

*   **기능 설명**: 웹 브라우저를 제어하고, 현재 페이지의 DOM 트리를 추출합니다. 이는 AI 에이전트가 웹 페이지의 구조와 상호작용 가능한 요소를 이해하는 데 필요한 정보를 제공합니다.
*   **입출력 명세**:
    *   **입력**:
        *   `url` (string, 필수): 탐색할 웹 페이지의 URL.
        *   `browser_session_id` (string, 선택): 기존 브라우저 세션을 재사용하기 위한 ID. (Browser MCP와 연동 시)
    *   **출력**:
        *   `dom_tree` (JSON/string): 현재 페이지의 DOM 트리 구조 (HTML, CSS 선택자, 텍스트 콘텐츠 등 포함).
        *   `interactive_elements` (JSON array): 클릭, 입력 등 상호작용 가능한 UI 요소들의 목록 (각 요소의 바운딩 박스, ID, 타입, 텍스트 등 포함).
*   **의존하는 외부 도구**:
    *   `Playwright MCP` 또는 `Browser MCP` 또는 `mcp-web-browser`: 브라우저 제어 및 DOM 추출을 위해 이들 중 하나를 활용합니다.

### 1.2. `self_explorer-screenshot`

*   **기능 설명**: 지정된 영역 또는 전체 웹 페이지의 스크린샷을 캡처하고, 이를 파일 시스템 또는 클라우드 스토리지(예: S3)에 저장합니다.
*   **입출력 명세**:
    *   **입력**:
        *   `url` (string, 필수): 스크린샷을 캡처할 웹 페이지의 URL.
        *   `output_path` (string, 필수): 스크린샷을 저장할 경로 (로컬 파일 경로 또는 S3 URL).
        *   `region` (JSON object, 선택): 캡처할 영역의 좌표 및 크기 (`{x, y, width, height}`). 생략 시 전체 페이지 캡처.
        *   `browser_session_id` (string, 선택): 기존 브라우저 세션을 재사용하기 위한 ID.
    *   **출력**:
        *   `screenshot_url` (string): 저장된 스크린샷 파일의 접근 가능한 URL 또는 경로.
*   **의존하는 외부 도구**:
    *   `Playwright MCP` 또는 `Browser MCP` 또는 `mcp-web-browser`: 스크린샷 캡처 기능을 활용합니다.
    *   (선택적) S3 클라이언트 라이브러리: S3 저장을 위한 내부 의존성.

### 1.3. `self_explorer-annotator`

*   **기능 설명**: Figma에서 추출한 바운딩 박스 정보와 웹 페이지 스크린샷을 결합하여, 스크린샷 이미지 위에 Figma 노드 ID에 해당하는 바운딩 박스를 시각적으로 마킹합니다. 이는 AI 에이전트가 Figma 디자인과 실제 웹 페이지 간의 시각적 매핑을 이해하는 데 도움을 줍니다.
*   **입출력 명세**:
    *   **입력**:
        *   `screenshot_path` (string, 필수): 마킹할 스크린샷 이미지 파일의 경로.
        *   `figma_node_data` (JSON array, 필수): Figma API 또는 `figma-mcp`를 통해 얻은 UI 요소들의 바운딩 박스 및 메타데이터 (예: `[{node_id, x, y, width, height, type, text}]`).
        *   `output_path` (string, 필수): 마킹된 이미지를 저장할 경로.
        *   `dark_mode` (boolean, 선택): 마킹 색상을 다크 모드에 맞게 조정할지 여부. 기본값 `false`.
    *   **출력**:
        *   `annotated_image_url` (string): 마킹된 이미지 파일의 접근 가능한 URL 또는 경로.
*   **의존하는 외부 도구**:
    *   `figma-mcp` (또는 Figma REST API 직접 호출): Figma 노드 데이터를 가져오는 데 사용됩니다.
    *   이미지 처리 라이브러리 (예: Pillow in Python): 이미지 위에 바운딩 박스를 그리는 데 사용됩니다.

## 2. 조합 흐름 (Chat 창 내에서 GPT 호출)

Chat 창에서 AI 에이전트가 사용자 요청을 처리하는 일반적인 조합 흐름은 다음과 같습니다:

1.  **사용자 요청**: "이 Figma 프로토타입을 탐색하고, '로그인' 버튼을 찾아 클릭해줘."
2.  **`self_explorer-browser` 호출**:
    *   에이전트가 `self_explorer-browser` 도구를 호출하여 Figma 프로토타입 URL을 전달합니다.
    *   `self_explorer-browser`는 브라우저를 열고 해당 URL로 이동한 후, 현재 페이지의 DOM 트리와 상호작용 가능한 요소 목록을 반환합니다.
3.  **`self_explorer-screenshot` 호출**:
    *   에이전트가 `self_explorer-screenshot` 도구를 호출하여 현재 브라우저 세션의 전체 페이지 스크린샷을 캡처하고 임시 경로에 저장합니다.
4.  **`figma-mcp` (또는 Figma API) 호출**:
    *   에이전트가 `figma-mcp` 도구(또는 직접 Figma API)를 호출하여 현재 Figma 파일의 노드 데이터를 가져옵니다.
5.  **`self_explorer-annotator` 호출**:
    *   에이전트가 `self_explorer-annotator` 도구를 호출하여 캡처된 스크린샷과 Figma 노드 데이터를 사용하여 스크린샷에 바운딩 박스를 마킹합니다. 마킹된 이미지는 임시 경로에 저장됩니다.
6.  **GPT 호출 (Chat 창)**:
    *   에이전트가 마킹된 스크린샷 이미지, DOM 트리 정보, 상호작용 가능한 요소 목록, 그리고 사용자 요청(`로그인 버튼 클릭`)을 포함하여 GPT 모델에 질의합니다.
    *   GPT는 이 정보를 바탕으로 "로그인" 버튼에 해당하는 요소의 ID와 클릭 액션을 제안합니다.
7.  **`self_explorer-browser` 재호출 (액션 수행)**:
    *   에이전트가 GPT의 제안에 따라 `self_explorer-browser` 도구를 재호출하여 해당 요소 ID에 대한 "클릭" 액션을 수행합니다.
8.  **반복**: 필요한 경우 2-7단계를 반복하여 사용자 요청을 완료합니다.
9.  **결과 반환**: 최종 탐색 결과 또는 요청 완료 메시지를 사용자에게 전달합니다.

## 3. Python 기존 기능 매핑

기존 `scripts/self_explorer_figma.py`의 주요 기능들을 새로운 MCP 도구로 다음과 같이 분리할 수 있습니다:

| 기존 `self_explorer_figma.py` 기능 | 새로운 MCP 도구 | 비고 |
| :--------------------------------- | :---------------- | :--- |
| `SeleniumController` 초기화 및 브라우저 제어 (`execute_selenium`, `tap`, `long_press`, `swipe`, `back`, `get_current_node_id`, `get_canvas_size`, `calculate_position`) | `self_explorer-browser` | 브라우저 자동화 및 상호작용 |
| 스크린샷 캡처 (`take_screenshot`, `take_canvas_screenshot`) | `self_explorer-screenshot` | 스크린샷 캡처 및 저장 |
| `UIElement.process_node_data`, `find_node_by_id` (Figma 데이터 처리) | `figma-mcp` (또는 `self_explorer-annotator` 내부에서 Figma API 호출) | Figma 노드 데이터 추출 및 처리. `figma-mcp`가 이 역할을 담당하는 것이 이상적. |
| `draw_bbox_multi`, `draw_circle`, `draw_arrow` (이미지 위에 바운딩 박스 그리기) | `self_explorer-annotator` | 스크린샷에 시각적 마킹 |
| `mllm.get_model_response` (LLM 호출) | **Chat 창 내 GPT 호출** | Python 내부에서 직접 LLM 호출하지 않음. |
| `parse_explore_rsp`, `parse_reflect_rsp` (LLM 응답 파싱) | **AI 에이전트 내부 로직** | GPT 응답을 파싱하여 다음 액션을 결정하는 로직은 에이전트가 담당. |
| `append_to_log` (보고서 생성) | **AI 에이전트 내부 로직** | 탐색 로그 및 보고서 생성은 에이전트가 관리. |
| `get_figma_file_data` (Figma API 호출) | `figma-mcp` (또는 `self_explorer-annotator`의 내부 의존성) | Figma 파일 데이터 가져오기. |

## 4. 중요 의문사항 / 구현 고려점

*   **MCP 표준 선택**: JSON-RPC와 SSE-based MCP 중 어떤 것을 선택할 것인가? 각 방식의 장단점(실시간성, 구현 복잡성, 메시지 크기 제한 등)을 고려해야 합니다. 현재 `figma-client`가 서버 폴링 방식을 사용하고 있으므로, SSE-based MCP가 더 적합할 수 있습니다.
*   **브라우저 세션 관리**: `self_explorer-browser`가 기존 브라우저 세션을 재사용할 수 있도록 `browser_session_id`를 어떻게 관리하고 전달할 것인가? 로그인 상태 유지 등 중요한 고려사항입니다.
*   **스크린샷 저장 위치**: `self_explorer-screenshot`에서 캡처된 스크린샷을 로컬에 저장할지, 아니면 S3와 같은 클라우드 스토리지에 저장하여 접근성을 높일지 결정해야 합니다. GPT에 이미지를 전달하려면 접근 가능한 URL이 필요합니다.
*   **Figma 노드 데이터의 실시간성**: `figma-mcp`를 통해 가져오는 Figma 노드 데이터가 브라우저의 현재 DOM 상태와 얼마나 일치하는지, 그리고 불일치 시 어떻게 처리할 것인지 고려해야 합니다. 특히 프로토타입의 동적 변화가 있을 경우 중요합니다.
*   **에러 처리 및 재시도**: 각 MCP 도구 호출 시 발생할 수 있는 네트워크 오류, 타임아웃, 도구 내부 오류 등에 대한 견고한 에러 처리 및 재시도 로직이 필요합니다.
*   **성능 최적화**: 브라우저 자동화, 스크린샷 캡처, 이미지 처리 등은 시간이 많이 소요될 수 있습니다. 각 도구의 성능 최적화 방안을 고려해야 합니다.
*   **보안**: 특히 `self_explorer-browser`를 통해 민감한 정보가 포함된 웹 페이지를 다룰 경우, 보안 취약점(예: XSS)에 대한 고려가 필요합니다.
*   **확장성**: 향후 새로운 기능 추가 시 MCP 도구 아키텍처가 유연하게 확장될 수 있도록 설계해야 합니다.
*   **로깅 및 디버깅**: 각 MCP 도구의 동작을 추적하고 문제를 진단할 수 있는 효과적인 로깅 및 디버깅 메커니즘이 필요합니다.
*   **GPT와의 인터페이스**: Chat 창 내에서 GPT와 상호작용할 때, 어떤 형식으로 정보를 주고받을 것인지 (예: JSON, Markdown), 그리고 GPT가 어떤 종류의 응답을 기대하는지 명확히 정의해야 합니다. 특히 이미지와 텍스트를 함께 전달하는 멀티모달 입력 방식에 대한 고려가 필요합니다.
*   **Figma API 토큰 관리**: `figma-mcp` 또는 직접 Figma API를 호출할 때 필요한 인증 토큰을 어떻게 안전하게 관리하고 전달할 것인가?
*   **UI 요소 식별의 정확성**: `self_explorer-browser`가 반환하는 `interactive_elements`와 `figma-mcp`가 반환하는 `figma_node_data` 간의 매핑 정확성을 어떻게 높일 것인가? 시각적 정보(스크린샷)와 구조적 정보(DOM, Figma 노드)를 결합하여 AI가 정확한 요소를 식별하도록 돕는 것이 중요합니다.
