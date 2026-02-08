# 🚀 RAG 파일럿 시스템

로컬 노트북에서 실행 가능한 **초경량 RAG (Retrieval Augmented Generation) 시스템**입니다.
NotebookLM 스타일의 UI로 문서를 업로드하고 AI와 대화할 수 있습니다.

## ✨ 주요 기능

- **📄 다중 문서 지원**: TXT, PDF, DOCX 파일 업로드
- **🔍 의미 기반 검색**: Sentence Transformers + NumPy 코사인 유사도
- **🤖 하이브리드 LLM**: OpenAI API + Ollama 동시 지원
- **💬 실시간 채팅**: 문서 기반 질의응답
- **🎨 NotebookLM 스타일 UI**: 다크테마, 글래스모피즘

## 🛠️ 기술 스택

| 구분 | 기술 |
|------|------|
| 임베딩 | Sentence Transformers (all-MiniLM-L6-v2) |
| 벡터 저장소 | 자체 구현 (JSON + NumPy) |
| 백엔드 | FastAPI (Python) |
| 프론트엔드 | Vanilla HTML/CSS/JS |
| LLM | OpenAI / Ollama |

## 📦 설치 방법

### 1. Python 의존성 설치

```bash
cd backend
pip install -r requirements.txt
```

### 2. 환경 변수 설정 (선택사항)

```bash
# .env.example을 복사하여 .env 생성
cp .env.example .env

# OpenAI 사용 시 API 키 설정
# LLM_PROVIDER=openai
# OPENAI_API_KEY=your-api-key
```

### 3. Ollama 설치 (로컬 LLM 사용 시)

```bash
# Ollama 설치: https://ollama.ai
ollama pull llama3.2
```

## 🚀 실행 방법

### 백엔드 서버 실행

```bash
cd backend
uvicorn main:app --reload
```

서버가 `http://localhost:8000` 에서 실행됩니다.

### 프론트엔드 실행

`frontend/index.html` 파일을 브라우저에서 열거나, Live Server로 실행합니다.

## 📖 사용법

1. **문서 업로드**: 왼쪽 사이드바에서 파일을 드래그 앤 드롭
2. **LLM 선택**: Ollama 또는 OpenAI 버튼 클릭
3. **질문하기**: 하단 입력창에 질문 입력 후 Enter

## 📁 프로젝트 구조

```
ragpoc/
├── backend/
│   ├── main.py              # FastAPI 앱
│   ├── rag_engine.py        # RAG 엔진
│   ├── document_processor.py # 문서 처리
│   ├── config.py            # 설정
│   └── requirements.txt     # 의존성
├── frontend/
│   ├── index.html           # 메인 UI
│   ├── style.css            # 스타일
│   └── app.js               # 로직
└── README.md
```

## 🔧 API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | 서버 상태 |
| GET | `/health` | 헬스 체크 |
| POST | `/upload` | 문서 업로드 |
| POST | `/chat` | RAG 채팅 |
| GET | `/sources` | 소스 목록 |
| DELETE | `/sources/{id}` | 소스 삭제 |
| POST | `/llm/switch` | LLM 전환 |

## 📄 라이선스

MIT License
