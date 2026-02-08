"""
간단한 벡터 저장소 (Python 3.14 호환)
- Sentence Transformers 기반 임베딩
- Numpy 코사인 유사도 검색
- JSON 기반 영구 저장
"""
import json
import os
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# 임베딩 모델 (지연 로딩)
_embedding_model = None


def get_embedding_model():
    """임베딩 모델 지연 로딩"""
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        except ImportError:
            print("⚠️ sentence-transformers 설치 필요: pip install sentence-transformers")
            _embedding_model = None
    return _embedding_model


@dataclass
class Document:
    id: str
    doc_id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]
    created_at: str


class SimpleVectorStore:
    """간단한 벡터 저장소"""
    
    def __init__(self, persist_path: str = "./data/vector_store"):
        self.persist_path = persist_path
        self.documents: Dict[str, Document] = {}
        self.embeddings: Optional[np.ndarray] = None
        self.doc_ids: List[str] = []
        
        os.makedirs(persist_path, exist_ok=True)
        self._load()
    
    def _load(self):
        """저장된 데이터 로드"""
        data_file = os.path.join(self.persist_path, "documents.json")
        if os.path.exists(data_file):
            try:
                with open(data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for doc_data in data:
                        doc = Document(**doc_data)
                        self.documents[doc.id] = doc
                self._rebuild_index()
            except Exception as e:
                print(f"데이터 로드 오류: {e}")
    
    def _save(self):
        """데이터 저장"""
        data_file = os.path.join(self.persist_path, "documents.json")
        data = [asdict(doc) for doc in self.documents.values()]
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _rebuild_index(self):
        """임베딩 인덱스 재구축"""
        if self.documents:
            self.doc_ids = list(self.documents.keys())
            embeddings = [self.documents[doc_id].embedding for doc_id in self.doc_ids]
            self.embeddings = np.array(embeddings)
        else:
            self.embeddings = None
            self.doc_ids = []
    
    def _get_embedding(self, text: str) -> List[float]:
        """텍스트 임베딩 생성"""
        model = get_embedding_model()
        if model is None:
            # 폴백: 간단한 TF-IDF 스타일 벡터 (데모용)
            import hashlib
            hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
            np.random.seed(hash_val % (2**32))
            return np.random.randn(384).tolist()
        
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def add(self, doc_id: str, texts: List[str], metadata: Dict[str, Any]) -> int:
        """문서 추가"""
        added = 0
        for i, text in enumerate(texts):
            chunk_id = f"{doc_id}_chunk_{i}"
            
            embedding = self._get_embedding(text)
            
            doc = Document(
                id=chunk_id,
                doc_id=doc_id,
                content=text,
                embedding=embedding,
                metadata={**metadata, "chunk_index": i},
                created_at=datetime.now().isoformat()
            )
            
            self.documents[chunk_id] = doc
            added += 1
        
        self._rebuild_index()
        self._save()
        return added
    
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """유사 문서 검색"""
        if not self.documents or self.embeddings is None:
            return []
        
        query_embedding = np.array(self._get_embedding(query))
        
        # 코사인 유사도 계산
        similarities = np.dot(self.embeddings, query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # 상위 k개 인덱스
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            doc_id = self.doc_ids[idx]
            doc = self.documents[doc_id]
            results.append({
                "content": doc.content,
                "metadata": doc.metadata,
                "similarity": float(similarities[idx])
            })
        
        return results
    
    def get_all_sources(self) -> List[Dict[str, Any]]:
        """모든 소스 목록"""
        sources = {}
        for doc in self.documents.values():
            doc_id = doc.doc_id
            if doc_id not in sources:
                sources[doc_id] = {
                    "id": doc_id,
                    "name": doc.metadata.get("source", "Unknown"),
                    "chunks": 0
                }
            sources[doc_id]["chunks"] += 1
        return list(sources.values())
    
    def delete_by_doc_id(self, doc_id: str) -> bool:
        """doc_id로 문서 삭제"""
        to_delete = [k for k, v in self.documents.items() if v.doc_id == doc_id]
        
        if not to_delete:
            return False
        
        for k in to_delete:
            del self.documents[k]
        
        self._rebuild_index()
        self._save()
        return True
    
    def get_document_content(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """특정 문서의 전체 내용 조회"""
        chunks = []
        metadata = None
        
        for doc in self.documents.values():
            if doc.doc_id == doc_id:
                chunks.append({
                    "index": doc.metadata.get("chunk_index", 0),
                    "content": doc.content
                })
                if metadata is None:
                    metadata = doc.metadata
        
        if not chunks:
            return None
        
        # 청크 인덱스 순으로 정렬
        chunks.sort(key=lambda x: x["index"])
        
        # 전체 내용 합치기
        full_content = "\n\n".join([c["content"] for c in chunks])
        
        return {
            "doc_id": doc_id,
            "name": metadata.get("source", "Unknown"),
            "chunks": len(chunks),
            "full_content": full_content,
            "chunks_detail": chunks
        }


# 싱글톤 인스턴스
vector_store = SimpleVectorStore()
