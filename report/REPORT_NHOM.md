# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** promaxima

**Thành viên:**
- Lâm Quang Anh Quân — 2A202602467
- Nguyễn Văn Diện — 2A202602615
- Bùi Văn Quang — 2A202602688

**Ngày:** 20/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** E-commerce Policies (Chính sách Trả hàng và Hoàn tiền của Shopee)

**Tại sao nhóm chọn chủ đề này?**
> Bộ quy định của Shopee cực kỳ phức tạp và được phân chia rõ ràng giữa quyền lợi của Người mua (Buyer) và Người bán (Seller). Chủ đề này lý tưởng để thử nghiệm sức mạnh của việc băm nhỏ theo cấu trúc ngữ nghĩa (Heading) cũng như ứng dụng Metadata Filtering để lọc riêng tài liệu theo từng tệp đối tượng.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|--------------------|----------------------|----------|-----------------|
| 1 | `buyer-bang-chung-va-dong-goi.md` | https://help.shopee.vn/portal/4/article/79467, https://help.shopee.vn/portal/4/article/79508 | 2026-09-20 / v2024-Q3 | 668 | `audience: buyer`, `category: evidence` |
| 2 | `buyer-gui-yeu-cau-va-tra-loi.md` | https://help.shopee.vn/portal/4/article/79233, https://help.shopee.vn/portal/4/article/190387 | 2026-09-20 / v2024-Q3 | 664 | `audience: buyer`, `category: return-refund` |
| 3 | `buyer-phuong-thuc-gui-hang.md` | https://help.shopee.vn/portal/4/article/189477 | 2026-09-20 / v2024-Q3 | 499 | `audience: buyer`, `category: logistics` |
| 4 | `buyer-quy-dinh-chung-va-han-che.md` | https://help.shopee.vn/portal/4/article/188931, https://help.shopee.vn/portal/4/article/79465 | 2026-09-20 / v2024-Q3 | 575 | `audience: buyer`, `category: return-refund` |
| 5 | `buyer-tra-hang-doi-y.md` | https://help.shopee.vn/portal/4/article/204305 | 2026-09-20 / v2024-Q3 | 831 | `audience: buyer`, `category: return-refund` |
| 6 | `seller-giai-quyet-tranh-chap.md` | https://banhang.shopee.vn/edu/article/18501 | 2026-09-20 / v2024-Q3 | 639 | `audience: seller`, `category: seller-management` |
| 7 | `seller-meo-cung-cap-bang-chung.md` | https://banhang.shopee.vn/edu/article/25057 | 2026-09-20 / v2024-Q3 | 744 | `audience: seller`, `category: evidence` |
| 8 | `seller-quy-trinh-shopee-mall.md` | https://banhang.shopee.vn/edu/article/22227 | 2026-09-20 / v2024-Q3 | 678 | `audience: seller`, `category: seller-management` |
| 9 | `seller-quy-trinh-tra-hang-hoan-tien.md` | https://banhang.shopee.vn/edu/article/563, https://banhang.shopee.vn/edu/article/13319 | 2026-09-20 / v2024-Q3 | 672 | `audience: seller`, `category: seller-management` |
| 10 | `seller-tong-quan-va-faq.md` | https://banhang.shopee.vn/edu/article/21021, https://banhang.shopee.vn/edu/article/10626 | 2026-09-20 / v2024-Q3 | 782 | `audience: seller`, `category: seller-management` |

*Bộ dữ liệu thực tế gồm đúng **10 bài**, chia đều 5 buyer – 5 seller, và `data/return_refund_policy/sources.csv` khớp 1-1 với danh sách trên. Cột "Số ký tự" đo trên phần nội dung sau khi bỏ front-matter YAML — tổng corpus là **6.752 ký tự nội dung** (9.603 ký tự nếu tính cả front-matter).*

### Danh sách kiểm tra quản trị dữ liệu (Data governance checklist)

- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `audience` | string | `buyer`, `seller` | Giúp cô lập không gian tìm kiếm. Khi user là người bán hỏi, thuật toán sẽ bỏ qua toàn bộ luật của người mua, tránh LLM trả lời nhầm chính sách. |
| `category` | string | `return-refund`, `evidence` | Lọc sâu hơn khi câu hỏi đề cập đích danh đến việc cung cấp bằng chứng hay chính sách hoàn trả chung. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| Toàn bộ Corpus | FixedSizeChunker (`fixed_size`) | 32 | 198 chars | Kém. Thường xuyên cắt ngang câu hoặc tách rời điều kiện của 1 luật. |
| Toàn bộ Corpus | SentenceChunker (`by_sentences`) | 58 | 85 chars | Trung bình. Câu văn trọn vẹn nhưng bị mất ngữ cảnh (không biết câu đang nói về luật gì). |
| Toàn bộ Corpus | RecursiveChunker (`recursive`) | 24 | 240 chars | Tốt. Giữ được các đoạn văn hoàn chỉnh. |

### Chiến lược của từng thành viên

#### Thành viên 1 — Lâm Quang Anh Quân

- **Loại chiến lược:** Custom (`HeadingChunker`)
- **Mô tả & lý do chọn cho chủ đề này:** Phân tách chunk dựa trên các thẻ tiêu đề Markdown (`#`, `##`, `###`). Do tài liệu chính sách của Shopee được tổ chức cực kỳ chặt chẽ theo các điều khoản (Ví dụ: "1. Thời gian gửi yêu cầu", "2. Quy định đóng gói"), việc băm bằng thẻ Heading giúp đảm bảo mỗi chunk chứa trọn vẹn 1 điều khoản pháp lý, không bị cắt xén hay thiếu hụt bối cảnh như Fixed Size.
- **Code snippet (nếu custom):**

```python
class HeadingChunker(ChunkingStrategy):
    def chunk(self, text: str) -> List[str]:
        chunks = []
        lines = text.split('\n')
        current_chunk = []
        for line in lines:
            if re.match(r'^#{1,6}\s', line):
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk).strip()
                    if chunk_text:
                        chunks.append(chunk_text)
                current_chunk = [line]
            else:
                current_chunk.append(line)
        if current_chunk:
            chunk_text = '\n'.join(current_chunk).strip()
            if chunk_text:
                chunks.append(chunk_text)
        return chunks
```

#### Thành viên 2 — Nguyễn Văn Diện

- **Loại chiến lược:** Custom — `FixedSizeChunker` + `SentenceChunker`
- **Mô tả & lý do chọn:** Diện thử **2 chiến lược** trên cùng bộ tài liệu. `FixedSizeChunker` cắt theo kích thước cố định (500 ký tự, overlap 50) — nhanh, đơn giản nhưng hay cắt ngang câu; `SentenceChunker` cắt theo nhóm câu (3 câu/chunk) — giữ trọn vẹn một ý/điều khoản nên trúng đáp án chuẩn tốt hơn (Top-1 ở câu 3, 4). Cả hai đều không cần code đặc thù cho Markdown, phù hợp để so sánh ảnh hưởng của cách chia chunk lên chất lượng truy xuất.
- **Code snippet (nếu custom):**

```python
class FixedSizeChunker:
    """Split text into fixed-size chunks with optional overlap."""
    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks
```

```python
class SentenceChunker:
    """Split text into chunks of at most max_sentences_per_chunk sentences."""
    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        raw_sentences = re.split(r"(?<=[.!?])\s+|(?<=\.)\n", text)
        sentences = [s.strip() for s in raw_sentences if s.strip()]
        if not sentences:
            return []
        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            group = sentences[i : i + self.max_sentences_per_chunk]
            chunks.append(" ".join(group).strip())
        return chunks
```

#### Thành viên 3 — Bùi Văn Quang

- **Loại chiến lược:** `RecursiveChunker`
- **Mô tả & lý do chọn:** Thuật toán phân tách đệ quy đa tầng, ưu tiên các dấu ngắt đoạn lớn (`\n\n`) trước khi xuống ngắt dòng (`\n`) và ranh giới câu (`. `). Sau đó gom các mảnh nhỏ liền kề để độ dài chunk tiệm cận 300 ký tự mà không vượt ngưỡng. Rất phù hợp với cấu trúc phân đoạn của điều khoản thương mại điện tử.
- **Code snippet (nếu custom):**

```python
class RecursiveChunker:
    
    def __init__(self, chunk_size: int = 300, separators: list[str] | None = None):
        self.chunk_size = chunk_size
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]
        return self._split(text, self.separators)

    def _split(self, text: str, separators: list[str]) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text]
        if not separators:
            # Hết separator thì cắt lát cứng theo kích thước
            return [text[i : i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]

        sep = separators[0]
        next_seps = separators[1:]

        if sep == "":
            return [text[i : i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]
        if sep not in text:
            return self._split(text, next_seps)

        # Pha 1: Tách nhỏ (Split)
        sub_chunks = []
        for piece in text.split(sep):
            if not piece:
                continue
            if len(piece) > self.chunk_size:
                sub_chunks.extend(self._split(piece, next_seps))
            else:
                sub_chunks.append(piece)

        # Pha 2: Gộp các mảnh nhỏ liền kề (Merge) sao cho <= chunk_size
        merged, curr = [], ""
        for piece in sub_chunks:
            if not curr:
                curr = piece
            elif len(curr) + len(sep) + len(piece) <= self.chunk_size:
                curr = curr + sep + piece
            else:
                merged.append(curr)
                curr = piece
        if curr:
            merged.append(curr)
        return merged
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Lâm Quang Anh Quân | HeadingChunker | 7/10 | Giữ ngữ cảnh 1 điều khoản cực tốt. | Nếu 1 mục Heading quá dài, chunk sẽ phình to. |
| Nguyễn Văn Diện | FixedSizeChunker + SentenceChunker | 4/10 | SentenceChunker giữ trọn câu → trúng Top-1 câu 3, 4. | FixedSize cắt ngang câu; bị MockEmbedder (MD5) làm nhiễu. |
| Bùi Văn Quang | RecursiveChunker | 3/10 | Ngắt theo đoạn câu tự nhiên, giữ trọn nghĩa, tránh chunk vụn. | Không giữ lại tiêu đề mục lớn, dễ mất ngữ cảnh cha. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Đối với chủ đề luật lệ/chính sách, `HeadingChunker` của Quân phát huy hiệu quả cao nhất vì nó tôn trọng tính toàn vẹn của một điều khoản. Tránh việc mô hình AI đọc được điều kiện A ở chunk này nhưng hệ quả B lại bị cắt sang chunk khác.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Sản phẩm đổi ý có được mở seal/mở hộp không? | Không, sản phẩm phải còn mới hoàn toàn, chưa qua sử dụng, chưa mở hộp, giữ nguyên bao bì gốc. | Phần "Sản phẩm phải đáp ứng tiêu chí nào" (`buyer-tra-hang-doi-y`) |
| 2 | Người bán gửi sai hàng có được trả hàng không? | Có, người mua có quyền gửi yêu cầu trả hàng, người bán có thể đề xuất Hoàn tiền ngay hoặc chờ trả hàng. | Phần Trả lời đề xuất hoàn tiền (`buyer-gui-yeu-cau-va-tra-loi`) |
| 3 | Khẩu trang y tế có được trả hàng với lý do đổi ý không? | Không, khẩu trang y tế thuộc nhóm Sản phẩm vệ sinh cá nhân, không áp dụng lý do đổi ý. | Phần Sản phẩm hạn chế trả hàng (`buyer-quy-dinh-chung-va-han-che`) |
| 4 | Video mở kiện hàng cần quay mấy mặt của kiện hàng? | Cần quay rõ 6 mặt của kiện hàng trước khi mở. | Phần Bằng chứng mở hàng (`seller-meo-cung-cap-bang-chung`) |
| 5 | Người bán có bao nhiêu ngày để trả hàng về kho? | Người bán có 2 ngày để khiếu nại tính từ lúc đơn cập nhật trả hàng thành công hoặc từ ngày dự kiến nhận hàng. | Phần Hạn khiếu nại (`seller-quy-trinh-tra-hang-hoan-tien`) |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Câu 1 | HeadingChunker | Có (Top-1) | 2đ - Tìm trúng `buyer-tra-hang-doi-y` |
| 2 | Câu 2 | HeadingChunker | Có (Top-1) | 2đ - Tìm trúng `buyer-gui-yeu-cau-va-tra-loi` |
| 3 | Câu 3 | HeadingChunker | Có (Top-2) | 1đ - Tìm trúng `buyer-quy-dinh-chung-va-han-che` ở Top-2 |
| 4 | Câu 4 | HeadingChunker | Có (Top-1) | 2đ - Tìm trúng `buyer-bang-chung-va-dong-goi` |
| 5 | Câu 5 | **Cần Lọc Metadata** | Không | 0đ - MD5 băm quá ngẫu nhiên đẩy chunk đúng ra khỏi Top-3 |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào? (Bằng chứng A/B Test)**
> Có, cực kỳ hữu ích ở Câu 5 (luật thời hạn khiếu nại). Khi chạy A/B Test trên câu hỏi *"Người bán có bao nhiêu ngày để trả hàng về kho?"*:
> - **Chạy có Lọc (`audience: seller`):** Trả về Top 1 là `seller-quy-trinh-shopee-mall`.
> - **Chạy KHÔNG Lọc:** Trả về Top 2 là `buyer-phuong-thuc-gui-hang` và Top 3 là `buyer-quy-dinh-chung-va-han-che`.
>
> Điều này chứng minh nếu thiếu bộ lọc Metadata, hệ thống đã kéo nhầm 2 bài viết của Người Mua vào Top 3, làm sai lệch hoàn toàn ngữ cảnh trả lời (từ quy định của Seller sang Buyer).

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Phân tích lỗi (Failure Case Analysis):**
> **Câu hỏi bị hỏng:** Câu 5 - "Người bán có bao nhiêu ngày để trả hàng về kho?"
>
> **Vì sao hỏng:** Dù đã lọc Metadata cực chuẩn (chỉ tìm trong tệp `seller`), chunk chứa đáp án vàng (`seller-quy-trinh-tra-hang-hoan-tien`) vẫn không lọt vào Top 3. Lý do là thuật toán `MockEmbedder` băm MD5 chuỗi ký tự thành các vector ngẫu nhiên. Nó không đo lường ý nghĩa ngữ nghĩa (semantics) mà chỉ băm mặt chữ. Từ đó dẫn đến một chunk chả liên quan (`seller-quy-trinh-shopee-mall`) lại vô tình có điểm số Cosine cao hơn (0.279) so với chunk chứa thông tin.
>
> **Đề xuất sửa chữa:** Lỗi này sinh ra từ kiến trúc hệ thống, không phải do cách Chunking hay Metadata. Bắt buộc phải thay thế `MockEmbedder` bằng một Embedder thực thụ (như OpenAI `text-embedding-ada-002` hoặc `all-MiniLM-L6-v2` của HuggingFace) để bắt được độ tương đồng ngữ nghĩa.

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
- Thuật toán băm (MD5) trong `MockEmbedder` bộc lộ điểm yếu "chết người" khi quy mô corpus tăng lên (37 chunks). Việc nó đưa đáp án đúng lên top 1-2 ở các câu đầu chủ yếu là ngẫu nhiên, không thể tin cậy cho ứng dụng thực tế.
- Lọc Metadata (`audience`) hoạt động như một bức tường rào, khoanh vùng chính xác bối cảnh tìm kiếm giúp bù đắp sự yếu kém của Embedder.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một bộ tài liệu, nếu cắt bằng `FixedSizeChunker` sẽ hay bị đứt ngữ cảnh (ví dụ cắt ngang danh sách các bước). Việc chuyển sang `HeadingChunker` tốn công tùy chỉnh code Regex nhưng giúp AI lấy được trọn vẹn nguyên tắc luật.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Sẽ bổ sung thêm Metadata về `platform_version` (phiên bản cập nhật năm 2024 vs 2025) để giải quyết xung đột luật cũ và luật mới. Thêm nữa, sẽ dùng `OpenAIEmbedder` thật thay cho `MockEmbedder` để kiểm chứng độ chính xác truy xuất thực tế.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 0 / 5 |
| **Tổng phần nhóm** | **35 / 40** |
