# MCP 서버 개발 트러블슈팅 - 2025년 7월 7일

## 개요

Model Context Protocol (MCP) 서버를 구현하는 과정에서 발생한 문제들과 해결 방법을 기록합니다.

## 초기 문제: Client vs Server 혼동

### 문제 상황
- MCP SDK를 사용할 때 Client와 Server의 차이점을 이해하지 못함
- 원래 코드에서 `MCP` 클라이언트 클래스를 사용하려고 시도함

### 해결 방법
MCP 아키텍처 이해:
- **Host**: LLM 애플리케이션 (예: Cursor, Claude Desktop)
- **Client**: Host가 내부적으로 생성하는 컴포넌트
- **Server**: 개발자가 만들어서 Host에 연결하는 서비스 (우리가 만들려는 것)

### 올바른 접근
개발자는 **MCP 서버**를 만들어야 하며, 클라이언트는 Host 애플리케이션이 관리합니다.

## 주요 트러블슈팅 이슈들

### 1. 모듈 Import 오류

#### 문제 1: `Cannot find module '@modelcontextprotocol/sdk'`
```
Cannot find module '@modelcontextprotocol/sdk' or its corresponding type declarations.
```

**원인**: `node_modules`가 설치되지 않음  
**해결**: `npm install` 실행

#### 문제 2: TypeScript ESM 오류
```
Unknown file extension ".ts"
```

**원인**: TypeScript + ES 모듈 설정 충돌  
**해결**: 
- `package.json`에서 `"type": "module"` 제거 (일시적)
- `tsconfig.json`에서 `module: "commonjs"`, `moduleResolution: "node"` 설정

#### 문제 3: 모듈 경로 오류
```
Cannot find module '@modelcontextprotocol/sdk/dist/cjs/server/mcp'
```

**원인**: 잘못된 모듈 경로 사용  
**해결**: 패키지의 exports 설정에 따라 올바른 경로 사용

## 최종 해결책

### 1. 올바른 프로젝트 설정

**package.json**:
```json
{
  "name": "klever-instant-ut-mcp",
  "version": "1.0.0",
  "type": "module",
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.15.0",
    "zod": "^3.x.x"
  }
}
```

### 2. 작동하는 MCP 서버 코드

**index.js**:
```javascript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "Hello World",
  version: "1.0.0"
});

server.tool("add",
  { a: z.number(), b: z.number() },
  async ({ a, b }) => ({
    content: [{ type: "text", text: String(a + b) }]
  })
);

const transport = new StdioServerTransport();
await server.connect(transport);
```

### 3. 실행 방법
```bash
node index.js
```

## 핵심 학습 내용

### 1. MCP 아키텍처 이해
- **서버 개발**: 도구(tools), 리소스(resources), 프롬프트(prompts) 제공
- **클라이언트**: Host 애플리케이션이 관리
- **스탠다드 프로토콜**: JSON-RPC 기반 통신

### 2. ES 모듈 vs CommonJS
- MCP SDK는 ES 모듈을 기본으로 사용
- `"type": "module"` 설정이 필요
- `.js` 확장자를 명시적으로 포함해야 함

### 3. 모듈 경로 해결
- 패키지의 `exports` 필드 확인 중요
- 직접 경로보다는 공식 export 사용

## 성공 확인

서버가 성공적으로 실행되면:
1. 프로세스가 백그라운드에서 실행됨 (대기 상태)
2. `ps aux | grep "node index.js"`로 프로세스 확인 가능
3. 오류 메시지 없이 조용히 실행됨

## 추가 개발 방향

1. **도구 추가**: 더 많은 유용한 도구 구현
2. **타입 안정성**: TypeScript로 마이그레이션
3. **테스트**: 적절한 테스트 환경 구축
4. **문서화**: API 문서 및 사용법 가이드

## 참고 자료

- [MCP 공식 문서](https://modelcontextprotocol.io/)
- [MCP 아키텍처](https://modelcontextprotocol.io/specification/2025-03-26/architecture)
- [TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [5분 만에 MCP 구축하기](https://dev.to/andyrewlee/use-your-own-mcp-on-cursor-in-5-minutes-1ag4)

---

**작성일**: 2025년 7월 7일  
**상태**: ✅ 성공적으로 해결됨 