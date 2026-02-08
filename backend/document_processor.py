"""
문서 처리 모듈
- TXT, PDF, DOCX 파일 지원
- 텍스트 청킹 (Chunking)
"""
from typing import List, Dict, Any
import os
import re
from config import settings


def extract_text_from_file(file_path: str, file_type: str) -> str:
    """파일에서 텍스트 추출"""
    
    if file_type == "txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    
    elif file_type == "pdf":
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            raise ValueError(f"PDF 파싱 오류: {str(e)}")
    
    elif file_type == "docx":
        try:
            from docx import Document
            doc = Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        except Exception as e:
            raise ValueError(f"DOCX 파싱 오류: {str(e)}")
    
    else:
        raise ValueError(f"지원하지 않는 파일 형식: {file_type}")


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
    """텍스트를 청크로 분할"""
    
    chunk_size = chunk_size or settings.CHUNK_SIZE
    overlap = overlap or settings.CHUNK_OVERLAP
    
    # 문장 단위로 먼저 분리
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += sentence + " "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            # 오버랩 처리
            overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
            current_chunk = overlap_text + sentence + " "
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks


def process_document(file_path: str, filename: str) -> Dict[str, Any]:
    """문서 처리 - 텍스트 추출 및 청킹"""
    
    # 파일 확장자 추출
    file_ext = filename.rsplit(".", 1)[-1].lower()
    
    # 텍스트 추출
    text = extract_text_from_file(file_path, file_ext)
    
    # 청킹
    chunks = chunk_text(text)
    
    return {
        "filename": filename,
        "file_type": file_ext,
        "total_chunks": len(chunks),
        "chunks": chunks,
        "metadata": {
            "source": filename,
            "file_type": file_ext
        }
    }
