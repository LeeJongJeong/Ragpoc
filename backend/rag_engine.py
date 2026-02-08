"""
RAG 엔진 모듈
- 간단한 벡터 저장소 (Python 3.14 호환)
- 하이브리드 LLM 지원 (OpenAI / Ollama)
"""
from typing import List, Dict, Any
from config import settings
from vector_store import vector_store


class RAGEngine:
    def __init__(self):
        self.vector_store = vector_store
        self.llm_provider = settings.LLM_PROVIDER
        self._init_llm_client()
    
    def _init_llm_client(self):
        """하이브리드 LLM 클라이언트 초기화"""
        if self.llm_provider == "openai":
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                print(f"⚠️ OpenAI 초기화 오류: {e}")
                self.openai_client = None
        else:
            try:
                import ollama
                self.ollama_client = ollama
            except ImportError:
                print("⚠️ Ollama 라이브러리가 설치되지 않았습니다.")
                self.ollama_client = None
    
    def add_documents(self, doc_id: str, chunks: List[str], metadata: Dict[str, Any]) -> int:
        """문서 청크들을 벡터 저장소에 추가"""
        return self.vector_store.add(doc_id, chunks, metadata)
    
    def search(self, query: str, n_results: int = None) -> List[Dict[str, Any]]:
        """쿼리와 유사한 문서 검색"""
        n_results = n_results or settings.TOP_K_RESULTS
        return self.vector_store.search(query, n_results)
    
    def generate_response(self, query: str, context: List[str]) -> str:
        """LLM을 사용하여 응답 생성"""
        
        # 컨텍스트 구성
        context_text = "\n\n".join([f"[문서 {i+1}]\n{c}" for i, c in enumerate(context)])
        
        system_prompt = """당신은 제공된 문서를 기반으로 질문에 답변하는 AI 어시스턴트입니다.
답변 시 다음 규칙을 따르세요:
1. 제공된 문서의 정보만을 사용하여 답변하세요.
2. 문서에 없는 정보는 "제공된 문서에서 해당 정보를 찾을 수 없습니다"라고 답변하세요.
3. 답변은 한국어로 작성하세요.
4. 가능하면 구체적인 내용을 인용하세요."""
        
        user_prompt = f"""다음 문서들을 참고하여 질문에 답변해주세요.

### 참고 문서:
{context_text}

### 질문:
{query}

### 답변:"""
        
        if self.llm_provider == "openai":
            return self._generate_openai(system_prompt, user_prompt)
        else:
            return self._generate_ollama(system_prompt, user_prompt)
    
    def _generate_openai(self, system_prompt: str, user_prompt: str) -> str:
        """OpenAI API로 응답 생성"""
        if not self.openai_client:
            return "OpenAI 클라이언트가 초기화되지 않았습니다. API 키를 확인하세요."
        
        try:
            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"OpenAI API 오류: {str(e)}"
    
    def _generate_ollama(self, system_prompt: str, user_prompt: str) -> str:
        """Ollama로 응답 생성"""
        if not self.ollama_client:
            return "Ollama 클라이언트가 설치되지 않았습니다. 'pip install ollama'로 설치하세요."
        
        try:
            response = self.ollama_client.chat(
                model=settings.OLLAMA_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response["message"]["content"]
        except Exception as e:
            return f"Ollama 오류: {str(e)}. Ollama가 실행 중인지 확인하세요 (ollama serve)."
    
    def get_all_sources(self) -> List[Dict[str, Any]]:
        """저장된 모든 소스(문서) 목록 반환"""
        return self.vector_store.get_all_sources()
    
    def delete_source(self, doc_id: str) -> bool:
        """특정 소스의 모든 청크 삭제"""
        return self.vector_store.delete_by_doc_id(doc_id)
    
    def switch_llm_provider(self, provider: str) -> str:
        """LLM 제공자 전환 (openai / ollama)"""
        if provider in ["openai", "ollama"]:
            self.llm_provider = provider
            settings.LLM_PROVIDER = provider
            self._init_llm_client()
            return f"LLM 제공자가 {provider}로 전환되었습니다."
        return "지원하지 않는 LLM 제공자입니다. (openai 또는 ollama)"
    
    def get_document_content(self, doc_id: str) -> Dict[str, Any]:
        """특정 문서의 전체 내용 조회"""
        return self.vector_store.get_document_content(doc_id)


# 싱글톤 인스턴스
rag_engine = RAGEngine()
