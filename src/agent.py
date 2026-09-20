from __future__ import annotations

from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(
        self,
        question: str,
        top_k: int = 3,
        metadata_filter: dict | None = None,
    ) -> str:
        """
        Retrieve relevant chunks from store and ask LLM to answer based on context.
        """
        if self.store.get_collection_size() == 0:
            return "Không tìm thấy thông tin phù hợp do cơ sở tri thức hiện đang rỗng."

        if metadata_filter:
            results = self.store.search_with_filter(
                question, top_k=top_k, metadata_filter=metadata_filter
            )
        else:
            results = self.store.search(question, top_k=top_k)

        if not results:
            return "Không tìm thấy tài liệu phù hợp trong cơ sở tri thức để trả lời câu hỏi."

        context_blocks = []
        for index, item in enumerate(results, start=1):
            source = (
                item.get("metadata", {}).get("source")
                or item.get("metadata", {}).get("doc_id")
                or item.get("id", f"doc_{index}")
            )
            context_blocks.append(f"[{index}] (Nguồn: {source}):\n{item['content']}")

        context_text = "\n\n".join(context_blocks)

        prompt = (
            "Bạn là một trợ lý thông minh giải đáp câu hỏi dựa trên cơ sở tri thức.\n"
            "Chỉ sử dụng thông tin trong các đoạn ngữ cảnh được cung cấp dưới đây để trả lời câu hỏi.\n"
            "Nếu thông tin không có trong ngữ cảnh, hãy nói rõ là không tìm thấy và không tự suy đoán.\n"
            "Khi trả lời, hãy trích dẫn số thứ tự nguồn tương ứng (ví dụ [1], [2]).\n\n"
            f"--- NGỮ CẢNH ---\n{context_text}\n\n"
            f"--- CÂU HỎI ---\n{question}\n\n"
            "--- CÂU TRẢ LỜI ---"
        )

        return self.llm_fn(prompt)
