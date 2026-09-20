# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Văn Diện — **MSSV:** 2A202602615
**Nhóm:** promaxima
**Ngày:** 20/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

**Chiến lược cá nhân của tôi:** `SentenceChunker` (3 câu/chunk) và `FixedSizeChunker` (500 ký tự, overlap 50) — cùng bộ tài liệu, cùng 5 câu hỏi với cả nhóm.
**Embedding backend:** `MockEmbedder` (mặc định của lab; không có API key nên tôi không bật được embedder thật — điều này ảnh hưởng trực tiếp tới kết quả ở mục 5).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> Hai vector embedding chỉ gần như cùng một hướng trong không gian nhiều chiều, tức là hai đoạn văn bản được mô hình coi là **nói về cùng một ý** — dù câu chữ có thể khác nhau hoàn toàn. Điểm càng gần 1 thì hai đoạn càng "cùng hướng ngữ nghĩa"; gần 0 nghĩa là hai đoạn gần như không liên quan; âm nghĩa là ngược hướng.

**Ví dụ có độ tương tự CAO:** *(hai câu khác từ vựng nhưng cùng nghĩa)*
- Câu A: "Người mua được trả hàng khi đổi ý"
- Câu B: "Khách hàng có thể hoàn trả sản phẩm nếu không còn nhu cầu"
- Tại sao tương đồng: Cả hai cùng diễn đạt một hành vi (trả lại hàng) với cùng một điều kiện (vì người mua không còn muốn nữa). Không có từ nào trùng nhau ngoài "hàng", nên nếu hệ thống cho điểm cao ở cặp này thì chứng tỏ nó mã hoá **nghĩa** chứ không phải so khớp mặt chữ.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Khẩu trang y tế không được trả hàng vì lý do đổi ý"
- Câu B: "Hôm nay trời mưa to ở Hà Nội"
- Tại sao khác: Hai câu thuộc hai miền ngữ nghĩa không giao nhau (chính sách thương mại điện tử vs. thời tiết), gần như không chia sẻ khái niệm nào.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

> Cosine chỉ quan tâm **hướng** của vector, không quan tâm **độ dài**. Trong văn bản, độ dài vector thường phản ánh độ dài/độ lặp của câu, không phản ánh nghĩa — nên hai câu cùng nghĩa nhưng một câu dài gấp đôi sẽ bị Euclid coi là "xa nhau", còn cosine vẫn cho gần 1. Cosine cũng bị chặn trong [-1, 1] nên dễ đặt ngưỡng và dễ so sánh giữa các cặp khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> *Trình bày phép tính:*
> - Bước nhảy (step) giữa hai chunk liên tiếp = `chunk_size - overlap` = 500 − 50 = **450**.
> - Công thức trong `exercises.md`: `ceil((độ_dài − overlap) / (chunk_size − overlap))` = `ceil((10,000 − 50) / 450)` = `ceil(9,950 / 450)` = `ceil(22.11)` = **23**.
> - Kiểm chứng bằng chính `FixedSizeChunker` trong repo (đừng tin công thức suông):
> ```bash
> python -c "from src.chunking import FixedSizeChunker; print(len(FixedSizeChunker(chunk_size=500, overlap=50).chunk('a'*10000)))"
> # -> 23
> ```
> *Đáp án:* **23 chunks.**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> Overlap 100 ⇒ step = 500 − 100 = **400** ⇒ `ceil((10,000 − 100) / 400)` = `ceil(24.75)` = **25 chunks** (đã chạy `FixedSizeChunker(chunk_size=500, overlap=100).chunk('a'*10000)` → đúng 25). Số chunk tăng vì mỗi lần trượt chỉ tiến 400 ký tự thay vì 450, nên cần thêm lượt để phủ hết tài liệu.
>
> Lý do muốn tăng overlap: nếu một điều khoản nằm vắt qua ranh giới hai chunk thì **không có overlap** thông tin đó bị chẻ đôi và mỗi nửa đều vô dụng khi truy xuất; overlap lớn hơn bảo đảm câu/điều kiện quan trọng xuất hiện trọn vẹn trong ít nhất một chunk. Cái giá phải trả là tốn thêm chunk (tăng dung lượng store, tăng chi phí embed) và làm các chunk gần nhau giống nhau hơn — dễ khiến top-3 toàn chunk trùng lặp thay vì 3 nguồn tin khác nhau.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> Tôi dùng regex `re.split(r"(?<=[.!?])\s+|(?<=\.)\n", text)`. Hai lookbehind `(?<=[.!?])` / `(?<=\.)` giữ nguyên dấu chấm than, chấm hỏi, dấu chấm ở **cuối câu trước** thay vì ăn mất nó như khi split theo dấu câu thông thường; nhánh thứ hai `(?<=\.)\n` xử lý trường hợp câu kết thúc bằng dấu chấm rồi xuống dòng. Sau khi split, tôi `.strip()` từng câu và **loại bỏ phần tử rỗng** (nếu không, các dòng trống của Markdown sẽ tạo ra hàng loạt chunk rỗng). Cuối cùng gom câu thành nhóm `max_sentences_per_chunk` (mặc định 3) và nối bằng dấu cách.
>
> Các trường hợp ngoại lệ tôi xử lý: văn bản rỗng hoặc chỉ có khoảng trắng → trả `[]` (không trả `[""]`); `max(1, max_sentences_per_chunk)` để tham số 0 hoặc âm không gây vòng lặp vô hạn; văn bản không có dấu câu → rơi về đúng một chunk là cả văn bản.
>
> Hạn chế tôi phát hiện khi chạy benchmark: vì tôi nối câu bằng dấu cách nên **mất ký tự xuống dòng**, và một dòng tiêu đề Markdown không có dấu câu sẽ bị dính vào câu kế tiếp. Danh sách yêu cầu dạng gạch đầu dòng (mỗi dòng một câu ngắn) cũng bị chẻ nhỏ: trong `buyer-bang-chung-va-dong-goi`, câu "Quay rõ 6 mặt kiện hàng." nằm ở chunk `#0` nhưng chunk thắng truy vấn lại là `#1` — đây chính là nguyên nhân gốc của failure case ở mục 5.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> Ý tưởng: thử cắt bằng dấu ngắt "to" nhất trước, chỗ nào vẫn quá dài thì hạ xuống dấu ngắt nhỏ hơn, cuối cùng mới cắt cứng. Thứ tự ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Ở mỗi tầng, tôi tách văn bản theo separator hiện tại, rồi **đệ quy** những mảnh vẫn vượt `chunk_size` với danh sách separator còn lại.
>
> Base case (trường hợp cơ sở) có bốn nhánh: (1) chuỗi rỗng → `[]`; (2) `len ≤ chunk_size` → trả luôn `[text]`; (3) separator `""` (đã cạn) → cắt lát cứng theo `chunk_size`; (4) separator không xuất hiện trong văn bản → bỏ qua nó và đệ quy với separator kế tiếp.
>
> Sau khi tách, tôi có thêm **pha gộp**: các mảnh nhỏ liền kề được nối lại bằng chính separator đó chừng nào tổng độ dài còn ≤ `chunk_size`. Nếu không có pha này, văn bản nhiều dòng ngắn sẽ vỡ thành hàng chục chunk vài chữ, làm loãng top-k.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> Tôi lưu store trong bộ nhớ dưới dạng list các dict `{id, content, metadata, embedding}`. Embedding được tính **một lần, ngay lúc add** (`_make_record`) qua `embedding_fn` được inject từ constructor — mặc định là `_mock_embed`, nhưng test có thể truyền fake khác, đó là lý do tôi không hard-code embedder. `_make_record` **copy** metadata (`dict(doc.metadata)`) để việc sửa dict của người gọi sau đó không làm hỏng store, và tự bổ sung `doc_id` lấy từ tiền tố của id dạng `"file#0"` nếu front-matter chưa có.
>
> `search` embed câu truy vấn đúng một lần, chấm điểm mọi record bằng **tích vô hướng** (đúng yêu cầu của lab), sắp xếp giảm dần theo score rồi cắt `top_k`. Vì `MockEmbedder` đã chuẩn hoá vector về độ dài 1 nên tích vô hướng ở đây tương đương cosine; nếu đổi sang embedder thật chưa chuẩn hoá thì cần chuẩn hoá trước khi so sánh.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> `search_with_filter` **lọc trước, tìm sau** (pre-filtering): dựng danh sách candidate bằng cách so khớp bằng nhau trên **mọi** cặp key/value của `metadata_filter`, rồi mới chạy similarity search trên đúng danh sách đó. Nếu `metadata_filter` rỗng/None thì candidate là toàn bộ store, nên hàm này là superset của `search`. Cách này rẻ và chính xác, nhưng có đánh đổi recall: filter `{"audience": "seller"}` khiến mọi chunk `buyer` trở nên **bất khả truy cập**, kể cả khi nó chứa câu trả lời — tôi gặp đúng tình huống này ở câu 5 (mục 5).
>
> `delete_document` xoá theo **hai đường**: record có `metadata["doc_id"] == doc_id`, hoặc `id == doc_id` (phòng trường hợp tài liệu chưa từng được chunk). Tôi so sánh số lượng trước/sau khi lọc để trả về `True`/`False` thay vì đếm thủ công.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> Trước hết tôi chặn hai trường hợp thoái hoá: store rỗng, và truy xuất không trả về kết quả nào — trả thẳng một câu thông báo tiếng Việt thay vì gọi LLM với ngữ cảnh rỗng (đây là cách tránh để mô hình tự bịa). Nếu có `metadata_filter` thì đi qua `search_with_filter`, ngược lại dùng `search`.
>
> Cách đưa ngữ cảnh vào prompt: mỗi chunk thành một khối `[i] (Nguồn: <source | doc_id | id>):` + nội dung, các khối nối nhau bằng dòng trống. Phần prompt gồm ba khối có nhãn rõ ràng `--- NGỮ CẢNH ---`, `--- CÂU HỎI ---`, `--- CÂU TRẢ LỜI ---`, kèm hai ràng buộc bằng lời: (a) **chỉ** dùng thông tin trong ngữ cảnh, nếu không có thì nói rõ là không tìm thấy chứ không suy đoán; (b) trích dẫn số thứ tự nguồn `[1]`, `[2]` để câu trả lời truy vết được về chunk gốc. Việc gọi LLM được tách ra qua `llm_fn` inject từ ngoài, nên agent không phụ thuộc nhà cung cấp nào.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

Chạy `.venv/Scripts/python.exe -m pytest tests/ -v` (Python 3.11.9):

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: C:\Users\DMX\Desktop\VIN\LAB\K4-DAY07-NguyenVanDien-2A202602615
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.14s ==============================
```

**Số lượng bài test vượt qua (pass):** **42 / 42**

`python main.py "Chunking là gì?"` cũng chạy trọn vẹn từ đầu đến cuối (dòng `Skipping missing file: data/customer_support_playbook.txt` là bình thường — repo không có file đó).

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Tôi chọn 5 cặp câu **theo nghĩa**, dự đoán trước khi chạy, rồi đo bằng `compute_similarity(_mock_embed(a), _mock_embed(b))` — đúng backend mặc định của lab. Quy ước đọc kết quả: **cao** nếu điểm ≥ 0.5, **thấp** nếu < 0.5.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Người bán có 2 ngày để khiếu nại | Thời hạn khiếu nại của Người bán là 2 ngày | cao | +0.1327 | Không |
| 2 | Người mua được trả hàng khi đổi ý | Khách hàng có thể hoàn trả sản phẩm nếu không còn nhu cầu | cao | −0.2321 | Không |
| 3 | Khẩu trang y tế không được trả hàng vì lý do đổi ý | Hôm nay trời mưa to ở Hà Nội | thấp | +0.1867 | Không |
| 4 | quay rõ 6 mặt kiện hàng | quay rõ 6 mặt kiện hàng | cao | +1.0000 | **Có** |
| 5 | The buyer can return the item within 15 days | Người mua có thể trả hàng trong vòng 15 ngày | cao | −0.0172 | Không |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Chỉ **1/5** dự đoán đúng, và câu duy nhất đúng là câu *trùng nguyên văn*. Điều này củng cố kết luận: `MockEmbedder` **không mã hoá ngữ nghĩa**. Nó băm MD5 chuỗi ký tự rồi sinh vector giả ngẫu nhiên, nên "cùng nghĩa khác chữ" (cặp 2, cặp 5) nhận điểm quanh 0 hoặc âm, còn hai câu hoàn toàn không liên quan (cặp 3) lại được +0.1867 — **cao hơn cả cặp 1 và cặp 2 dù hai cặp đó cùng chủ đề**. Bất ngờ nhất là cặp 5: hai câu dịch sát nghĩa của nhau chỉ được −0.0172, trong khi cặp 3 vô nghĩa lại dương.
>
> Bài học: một embedding tốt phải mã hoá *ý niệm*, nên hai câu cùng nghĩa bất kể từ vựng (thậm chí khác ngôn ngữ) phải nằm gần nhau. Hash chỉ đảm bảo tính tất định và duy nhất — hai tính chất hoàn toàn không liên quan tới ngữ nghĩa. Vì vậy mọi con số truy xuất ở mục 5 là **nhiễu**, không phải tín hiệu; muốn kết luận về *chiến lược* thì phải nhìn vào `count` / `avg_length` / độ mạch lạc của chunk (những thứ không phụ thuộc embedding), rồi mới tới score.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

Bộ tài liệu: 10 file trong `data/return_refund_policy/` (6.752 ký tự nội dung sau khi bỏ front-matter). Chunker: `SentenceChunker(max_sentences_per_chunk=3)` → **35 chunks**; đối chứng `FixedSizeChunker(500, 50)` → **19 chunks**. Lệnh chạy: `python bench.py sentence` và `python bench.py fixed` (kết quả lưu ở `ket_qua_benchmark_sentence.txt` / `ket_qua_benchmark_fixed.txt`).

> **Ghi chú về cột "Câu trả lời của Agent":** lab không cấu hình LLM API key, nên `llm_fn` trong `bench.py` là một hàm giả lập. Để cột này có nội dung kiểm chứng được thay vì một chuỗi placeholder, tôi thay bằng một hàm **trích xuất tất định** (lấy câu trong chunk Top-1 có nhiều token trùng với câu hỏi nhất) và ghi rõ nguồn chunk. Đây là câu trả lời *được ràng buộc bởi ngữ cảnh truy xuất*, không phải văn bản do LLM sinh — đúng tinh thần "grounding" mà `docs/EVALUATION.md` muốn đo.

### Chiến lược chính của tôi — `SentenceChunker` (3 câu/chunk), 35 chunks

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Sản phẩm đổi ý có được mở seal/mở hộp không? | `buyer-bang-chung-va-dong-goi#1` — "Quá trình mở kiện thấy rõ mã vận đơn. Quay cận cảnh số lượng…" | 0.175 | Không (sai tài liệu) | "Quay cận cảnh số lượng và tình trạng sản phẩm bên trong." — không trả lời được câu hỏi |
| 2 | Người bán gửi sai hàng có được trả hàng không? | `seller-giai-quyet-tranh-chap#3` — "Nếu ngoài khả năng, đưa vụ việc ra cơ quan chức năng." | 0.278 | Không | "Nếu ngoài khả năng, đưa vụ việc ra cơ quan chức năng." — lạc đề hoàn toàn |
| 3 | Khẩu trang y tế có được trả hàng với lý do đổi ý không? | `buyer-quy-dinh-chung-va-han-che#0` — tiêu đề + "## 1. Thời gian gửi yêu cầu" | 0.236 | Đúng tài liệu, sai chunk | "Đơn hàng khác: 15 ngày kể từ lúc Giao hàng thành công." — trả lời về *thời hạn*, không phải *sản phẩm hạn chế* |
| 4 | Video mở kiện hàng cần quay mấy mặt của kiện hàng? | `buyer-bang-chung-va-dong-goi#1` — "Quá trình mở kiện thấy rõ mã vận đơn…" | 0.343 | Đúng tài liệu, sai chunk | "Quá trình mở kiện thấy rõ mã vận đơn." — thiếu đúng con số "6 mặt" |
| 5 | Người bán có bao nhiêu ngày để trả hàng về kho? | `seller-quy-trinh-shopee-mall#0` — tiêu đề "Cập nhật Quy trình… Shopee Mall" | 0.277 | Không (sai tài liệu) | "Đối với đơn Shopee Mall… Người mua sẽ gửi trả hàng trực tiếp về Người bán…" — trả lời sai câu hỏi |

### Chiến lược đối chứng — `FixedSizeChunker` (500 ký tự, overlap 50), 19 chunks

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Sản phẩm đổi ý có được mở seal/mở hộp không? | `buyer-gui-yeu-cau-va-tra-loi#0` | 0.125 | **Có, nhưng ở Top-3** (`buyer-tra-hang-doi-y#1` chứa "bao bì gốc") | "Nguồn 1: https://help.shopee.vn/portal/4/article/79233" — dính phần header, vô nghĩa |
| 2 | Người bán gửi sai hàng có được trả hàng không? | `seller-giai-quyet-tranh-chap#1` | 0.378 | Không | "Yêu cầu cung cấp tài liệu." — lạc đề |
| 3 | Khẩu trang y tế có được trả hàng với lý do đổi ý không? | `buyer-phuong-thuc-gui-hang#0` | 0.151 | **Có, nhưng ở Top-3** (`buyer-quy-dinh-chung-va-han-che#0` chứa "Không áp dụng lý do… Vệ sinh cá nhân") | "Hình thức trả hàng" — chỉ là dòng tiêu đề |
| 4 | Video mở kiện hàng cần quay mấy mặt của kiện hàng? | `buyer-tra-hang-doi-y#0` | 0.288 | Không | "…người mua quyết định trả lại sản phẩm như nguyên bản." — lạc đề |
| 5 | Người bán có bao nhiêu ngày để trả hàng về kho? | `seller-giai-quyet-tranh-chap#0` | 0.129 | Không | "Shopee khuyến khích hòa giải giữa Người bán và Người mua." — lạc đề |

### Chấm hai mức: đây là phát hiện quan trọng nhất của tôi

Theo `docs/SCORING.md` thì điều kiện tính điểm là *"top-3 chứa chunk liên quan **và** agent trả lời đúng"*, nên không thể chỉ kiểm `doc_id` của tài liệu vàng. Với mỗi câu tôi khai báo một **chuỗi đặc trưng bắt buộc phải xuất hiện trong ngữ cảnh truy xuất** rồi kiểm tra thật:

- Câu 1 → `"bao bì gốc"` · Câu 2 → `"trả hàng bình thường"` · Câu 3 → `"Không áp dụng lý do"` · Câu 4 → `"6 mặt kiện hàng"` · Câu 5 → `"2 ngày kể từ khi đơn"`

| Cách chấm | `SentenceChunker` | `FixedSizeChunker` |
|-----------|-------------------|--------------------|
| **Theo tài liệu** (chỉ kiểm `doc_id` vàng có trong top-3) | **4/10** (2/5 câu) | 2/10 (2/5 câu) |
| **Theo nội dung** (chuỗi đặc trưng thật sự có trong ngữ cảnh) | **0/10** (0/5 câu) | 2/10 (2/5 câu) |

Khoảng cách 4/10 → 0/10 của `SentenceChunker` chính là cái bẫy mà hướng dẫn lab cảnh báo. Cụ thể:

- **Câu 3 và câu 4** đều đưa **đúng tài liệu vàng lên Top-1**, nên cách chấm theo tài liệu cho 2 điểm/câu. Nhưng chunk thắng lại **không chứa câu trả lời**: ở `buyer-bang-chung-va-dong-goi`, câu "Quay rõ 6 mặt kiện hàng." nằm ở chunk `#0`, còn chunk `#1` ("Quá trình mở kiện thấy rõ mã vận đơn…") mới là chunk được truy xuất — nhóm 3 câu đã **chẻ đôi danh sách yêu cầu bằng chứng**. Agent vì thế trả lời thiếu đúng con số cần tìm.
- **Câu 3** tương tự: chunk `#0` (`buyer-quy-dinh-chung-va-han-che`) chứa tiêu đề và mục "Thời gian gửi yêu cầu", còn mục "Sản phẩm hạn chế trả hàng" — nơi có đáp án — nằm ở chunk `#2`, không lọt top-3.

Nói cách khác: **retrieval đúng chủ đề nhưng sai vị trí**. Đây đúng là failure case "top-3 đúng tài liệu nhưng sai section" mà tài liệu lab liệt kê, và nó có nguyên nhân kỹ thuật rõ ràng chứ không phải "tại embedder".

### Lọc metadata có giúp ích không? (A/B Test, câu 5)

Chạy đúng một chuỗi truy vấn *"Người bán có bao nhiêu ngày để trả hàng về kho?"* hai lần:

| Lần chạy | Top-1 | Top-2 | Top-3 | Đáp án vàng `seller-quy-trinh-tra-hang-hoan-tien` |
|----------|-------|-------|-------|--------------------|
| Có lọc `{"audience": "seller"}` | `seller-quy-trinh-shopee-mall` (0.277) | `seller-giai-quyet-tranh-chap` (0.206) | `seller-meo-cung-cap-bang-chung` (0.173) | **không có trong top-3** |
| Không lọc | `buyer-gui-yeu-cau-va-tra-loi` (0.303) | `seller-quy-trinh-shopee-mall` (0.277) | `seller-giai-quyet-tranh-chap` (0.206) | **không có trong top-3** |

> **Kết luận trung thực:** filter **có ích nhưng không đủ**. Nó đẩy được tài liệu `buyer` ra khỏi Top-1 (không lọc thì `buyer-gui-yeu-cau-va-tra-loi` chiếm ngôi đầu, tức agent sẽ trả lời bằng chính sách của **người mua** cho câu hỏi của **người bán**) — đây đúng là giá trị "hàng rào" mà nhóm tôi kỳ vọng. Nhưng nó **không cứu được** trường hợp đáp án vàng: chunk `seller-quy-trinh-tra-hang-hoan-tien#1` ("## 2. Hạn khiếu nại — 2 ngày kể từ khi đơn cập nhật trả hàng thành công") chưa bao giờ lọt top-3, kể cả khi đã khoanh vùng đúng `audience`. Đó là hạn chế của embedding (hash không phân biệt "hạn khiếu nại" với "quy trình Shopee Mall"), không phải của filter.

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?**
- Chấm theo nội dung: **0 / 5** (`SentenceChunker`) — **2 / 5** (`FixedSizeChunker`)
- Chấm theo tài liệu: **2 / 5** cho cả hai chiến lược

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> Hai điều. Thứ nhất, từ chỗ Quân dùng `HeadingChunker`: với văn bản quy định, **cấu trúc mục đã là một đơn vị ngữ nghĩa do người soạn chia sẵn**, nên tôn trọng nó rẻ hơn và đúng hơn là tự chia lại theo số câu. Chiến lược của tôi thắng ở những câu hỏi có đáp án nằm gọn trong 1–2 câu, nhưng đúng ở dạng tài liệu "danh sách yêu cầu" thì nó tự bắn vào chân mình (câu 4). Thứ hai, nguyên tắc **chấm hai mức** (kiểm `doc_id` vs. kiểm chuỗi đặc trưng trong ngữ cảnh) là thứ tôi sẽ mang sang mọi bài retrieval sau này — nếu chỉ chấm theo tài liệu, tôi đã tự báo cáo 4/10 trong khi agent thực chất **không trả lời được câu nào**.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 (42/42 passed) |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 2 / 10 |
| **Tổng phần cá nhân** | **52 / 60** |

> **Vì sao tôi tự cho phần truy xuất 2/10** (thay vì 4/10 như bảng tổng hợp của nhóm): theo `docs/SCORING.md`, điểm chỉ được tính khi *top-3 chứa chunk liên quan **và** agent trả lời đúng*. Chấm theo nội dung — cách chấm đúng — `SentenceChunker` của tôi được 0/10, `FixedSizeChunker` được 2/10 (câu 1 và câu 3 có chuỗi đáp án trong ngữ cảnh, nhưng đều ở Top-3 nên chỉ 1 điểm/câu). Con số 4/10 trong `REPORT_NHOM.md` là **chấm theo tài liệu**, và tôi giữ nguyên nó ở bảng trên để đối chiếu. Tôi cho rằng phần chênh lệch này là kết quả đáng giá nhất tôi rút ra được từ lab, nên tôi báo cáo đúng nó thay vì chọn con số đẹp hơn.

---

## Phụ lục — Lệnh tái lập kết quả

```bash
# 1. Kiểm thử (mục 3)
.venv/Scripts/python.exe -m pytest tests/ -v

# 2. Benchmark theo từng chiến lược (mục 5) — xuất kết quả top-3 kèm score + doc_id
.venv/Scripts/python.exe bench.py sentence ket_qua_benchmark_sentence.txt   # 35 chunks
.venv/Scripts/python.exe bench.py fixed    ket_qua_benchmark_fixed.txt      # 19 chunks

# 3. Bài toán chunking (mục 1.2)
python -c "from src.chunking import FixedSizeChunker; print(len(FixedSizeChunker(chunk_size=500, overlap=50).chunk('a'*10000)), len(FixedSizeChunker(chunk_size=500, overlap=100).chunk('a'*10000)))"
# -> 23 25
```

`bench.py` chạy câu 5 hai lần (có lọc `audience: seller` / không lọc) — đó là bằng chứng A/B Test ở mục 5. Kết quả của tôi tái lập được **byte-for-byte**: chạy lại `bench.py` cho ra file trùng khớp hoàn toàn với `ket_qua_benchmark_*.txt` đã lưu.
