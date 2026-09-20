import re
import sys
from pathlib import Path

from src.models import Document
from src.store import EmbeddingStore
from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.agent import KnowledgeBaseAgent

class HeadingChunker:
    def __init__(self, chunk_size: int = 500):
        self.chunk_size = chunk_size
        self.fallback_chunker = RecursiveChunker(chunk_size=chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text.strip():
            return []
        sections = re.split(r'(?m)(?=^#{1,6}\s)', text)
        
        final_chunks = []
        for section in sections:
            section = section.strip()
            if not section:
                continue
            if len(section) > self.chunk_size:
                first_line = section.split('\n')[0]
                heading_prefix = first_line if re.match(r'^#{1,6}\s', first_line) else ""
                
                sub_chunks = self.fallback_chunker.chunk(section)
                for i, sub in enumerate(sub_chunks):
                    if i > 0 and heading_prefix and not sub.startswith(heading_prefix):
                        final_chunks.append(f"{heading_prefix}\n{sub}")
                    else:
                        final_chunks.append(sub)
            else:
                final_chunks.append(section)
        return final_chunks

def parse_markdown(file_path: Path):
    content = file_path.read_text(encoding='utf-8')
    parts = content.split('---')
    if len(parts) >= 3:
        fm = parts[1].strip()
        body = '---'.join(parts[2:]).strip()
        metadata = {}
        for line in fm.split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                metadata[k.strip()] = v.strip().strip('"')
        return metadata, body
    return {}, content

def mock_llm(prompt: str) -> str:
    return "Câu trả lời giả lập từ LLM dựa trên ngữ cảnh đã truy xuất."

CHUNKERS = {
    "fixed": FixedSizeChunker,
    "sentence": SentenceChunker,
}


def main():
    chunker_name = sys.argv[1] if len(sys.argv) > 1 else "fixed"
    out_file = sys.argv[2] if len(sys.argv) > 2 else f"ket_qua_benchmark_{chunker_name}.txt"

    store = EmbeddingStore()
    chunker = CHUNKERS[chunker_name]()
    
    docs_dir = Path("data/return_refund_policy")
    all_chunks = []
    
    for file_path in docs_dir.glob("*.md"):
        metadata, body = parse_markdown(file_path)
        chunks = chunker.chunk(body)
        for i, text in enumerate(chunks):
            doc = Document(id=f"{file_path.stem}#{i}", content=text, metadata=metadata)
            all_chunks.append(doc)
            
    store.add_documents(all_chunks)
    agent = KnowledgeBaseAgent(store=store, llm_fn=mock_llm)
    
    # Exact same string for A/B Test
    q5_str = "Người bán có bao nhiêu ngày để trả hàng về kho?"
    
    queries = [
        ("Sản phẩm đổi ý có được mở seal/mở hộp không?", {"audience": "buyer"}),
        ("Người bán gửi sai hàng có được trả hàng không?", None),
        ("Khẩu trang y tế có được trả hàng với lý do đổi ý không?", {"audience": "buyer"}),
        ("Video mở kiện hàng cần quay mấy mặt của kiện hàng?", {"audience": "buyer"}),
        (q5_str, {"audience": "seller"}),
        (q5_str, None)  # A/B TEST: Same string, no filter
    ]
    
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(f"Chiến lược chunking: {chunker_name}\n")
        f.write(f"Đã nạp {len(all_chunks)} chunks vào store.\n\n")
        
        for i, (q, filter_dict) in enumerate(queries, 1):
            if i == 6:
                f.write(f"Câu 6 [A/B TEST]: {q}\n")
            else:
                f.write(f"Câu {i}: {q}\n")
            f.write(f"Filter: {filter_dict}\n")
            
            results = store.search_with_filter(q, top_k=3, metadata_filter=filter_dict)
            for j, res in enumerate(results, 1):
                f.write(f"  Top {j}: [Score: {res['score']:.3f}] - ID: {res['metadata'].get('doc_id')}\n")
                content_snippet = res['content'][:100].replace('\n', ' ')
                f.write(f"    Snippet: {content_snippet}...\n")
                
            ans = agent.answer(q, top_k=3)
            f.write(f"  Agent: {ans}\n\n")

if __name__ == "__main__":
    main()

