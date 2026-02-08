"""
RAG 파일럿 시스템 - FastAPI 백엔드
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import uuid
import tempfile

from rag_engine import rag_engine
from document_processor import process_document
from config import settings

app = FastAPI(
    title="RAG 파일럿 시스템",
    description="로컬 RAG 시스템 - NotebookLM 스타일",
    version="1.0.0"
)

# CORS 설정 (프론트엔드 연동)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== 요청/응답 모델 ==========

class ChatRequest(BaseModel):
    message: str
    
class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]
    
class LLMSwitchRequest(BaseModel):
    provider: str  # "openai" or "ollama"


# ========== API 엔드포인트 ==========

@app.get("/")
async def root():
    """서버 상태 확인"""
    return {
        "status": "running",
        "message": "🚀 RAG 파일럿 시스템이 실행 중입니다!",
        "llm_provider": rag_engine.llm_provider
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "llm_provider": rag_engine.llm_provider}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """문서 업로드 및 처리"""
    
    # 지원 파일 형식 확인
    allowed_extensions = ["txt", "pdf", "docx"]
    file_ext = file.filename.rsplit(".", 1)[-1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다. ({', '.join(allowed_extensions)} 지원)"
        )
    
    try:
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # 문서 처리
        doc_data = process_document(temp_path, file.filename)
        
        # 고유 ID 생성
        doc_id = str(uuid.uuid4())[:8]
        
        # 벡터 저장소에 추가
        chunks_added = rag_engine.add_documents(
            doc_id=doc_id,
            chunks=doc_data["chunks"],
            metadata=doc_data["metadata"]
        )
        
        # 임시 파일 삭제
        os.unlink(temp_path)
        
        return {
            "success": True,
            "message": f"'{file.filename}' 업로드 완료!",
            "doc_id": doc_id,
            "chunks": chunks_added
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """RAG 기반 채팅"""
    
    # 관련 문서 검색
    search_results = rag_engine.search(request.message)
    
    if not search_results:
        return ChatResponse(
            answer="업로드된 문서에서 관련 정보를 찾을 수 없습니다. 먼저 문서를 업로드해주세요.",
            sources=[]
        )
    
    # 컨텍스트 구성
    contexts = [r["content"] for r in search_results]
    
    # LLM으로 응답 생성
    answer = rag_engine.generate_response(request.message, contexts)
    
    # 소스 정보
    sources = [
        {
            "source": r["metadata"].get("source", "Unknown"),
            "content_preview": r["content"][:100] + "..." if len(r["content"]) > 100 else r["content"]
        }
        for r in search_results
    ]
    
    return ChatResponse(answer=answer, sources=sources)


@app.get("/sources")
async def get_sources():
    """업로드된 소스 목록"""
    sources = rag_engine.get_all_sources()
    return {"sources": sources, "total": len(sources)}


@app.delete("/sources/{doc_id}")
async def delete_source(doc_id: str):
    """소스 삭제"""
    success = rag_engine.delete_source(doc_id)
    
    if success:
        return {"success": True, "message": f"소스 '{doc_id}' 삭제 완료"}
    else:
        raise HTTPException(status_code=404, detail="소스를 찾을 수 없습니다.")


@app.get("/sources/{doc_id}/content")
async def get_source_content(doc_id: str):
    """소스 문서의 전체 내용 조회"""
    content = rag_engine.get_document_content(doc_id)
    
    if content:
        return content
    else:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")


@app.post("/llm/switch")
async def switch_llm(request: LLMSwitchRequest):
    """LLM 제공자 전환 (OpenAI / Ollama)"""
    result = rag_engine.switch_llm_provider(request.provider)
    return {"message": result, "current_provider": rag_engine.llm_provider}


@app.get("/llm/status")
async def llm_status():
    """현재 LLM 상태"""
    return {
        "provider": rag_engine.llm_provider,
        "openai_model": settings.OPENAI_MODEL,
        "ollama_model": settings.OLLAMA_MODEL
    }


@app.get("/ollama/models")
async def get_ollama_models():
    """Ollama에서 사용 가능한 모델 목록 조회"""
    try:
        import ollama
        models = ollama.list()
        model_list = [
            {
                "name": model.get("name", model.get("model", "unknown")),
                "size": model.get("size", 0),
                "modified_at": model.get("modified_at", "")
            }
            for model in models.get("models", [])
        ]
        return {
            "models": model_list,
            "current_model": settings.OLLAMA_MODEL,
            "total": len(model_list)
        }
    except Exception as e:
        return {
            "models": [],
            "current_model": settings.OLLAMA_MODEL,
            "error": str(e),
            "total": 0
        }


class OllamaModelRequest(BaseModel):
    model: str


@app.post("/ollama/model")
async def set_ollama_model(request: OllamaModelRequest):
    """Ollama 모델 변경"""
    old_model = settings.OLLAMA_MODEL
    settings.OLLAMA_MODEL = request.model
    
    # RAG 엔진의 모델도 업데이트
    if rag_engine.llm_provider == "ollama":
        rag_engine._init_llm_client()
    
    return {
        "success": True,
        "message": f"Ollama 모델이 '{old_model}'에서 '{request.model}'로 변경되었습니다.",
        "current_model": settings.OLLAMA_MODEL
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
