# File: main.py (đã cập nhật cho deployment)
import os
import re # Thêm thư viện regex
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from whoosh.index import open_dir
from whoosh.qparser import QueryParser
from whoosh.highlight import HtmlFormatter

app = FastAPI()

INDEX_DIR = "search_index"
DATA_DIR = "data"
ABS_DATA_DIR = os.path.realpath(DATA_DIR)

ix = None
if os.path.exists(INDEX_DIR):
    try:
        ix = open_dir(INDEX_DIR)
        print("Đã tải chỉ mục tìm kiếm thành công!")
    except Exception as e:
        print(f"Lỗi khi mở chỉ mục: {e}")
else:
    print(f"Cảnh báo: Không tìm thấy thư mục chỉ mục '{INDEX_DIR}'. Hãy chắc chắn script build đã chạy.")


class SearchQuery(BaseModel):
    query: str

@app.post("/search")
def search(search_query: SearchQuery):
    if not ix:
        raise HTTPException(status_code=503, detail="Hệ thống tìm kiếm chưa sẵn sàng.")
    results_list = []
    with ix.searcher() as searcher:
        parser = QueryParser("content", ix.schema)
        query = parser.parse(search_query.query)
        results = searcher.search(query, limit=18) 
        results.formatter = HtmlFormatter(tagname="mark")
        for hit in results:
            highlighted_content = hit.highlights("content", top=2)
            results_list.append({
                "filename": hit["filename"],
                "content_snippet": highlighted_content or hit["content"][:250] + "..."
            })
    return results_list

# === API ĐỌC FILE VỚI LOGIC HIGHLIGHT ĐƯỢC SỬA LẠI HOÀN TOÀN ===
@app.get("/document/")
def get_document(filename: str = Query(..., min_length=1), query: str | None = Query(None)):
    # --- Step 1: Get the document content safely ---
    try:
        real_path = os.path.join(ABS_DATA_DIR, filename)
        if not os.path.realpath(real_path).startswith(ABS_DATA_DIR):
             raise HTTPException(status_code=400, detail="Truy cập file không hợp lệ.")
        with open(real_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi đọc file: {e}")

    # --- Step 2: Highlight the content if a query is provided ---
    highlighted_content = content
    if query and ix:
        try:
            qparser = QueryParser("content", ix.schema)
            q_obj = qparser.parse(query)
            
            # Lấy các từ khóa từ câu truy vấn
            terms = {term.decode('utf-8') if isinstance(term, bytes) else term for fieldname, term in q_obj.all_terms() if fieldname == "content"}
            
            # Tự làm nổi bật bằng regex để đảm bảo hoạt động
            temp_content = content
            for term in terms:
                # re.escape để xử lý ký tự đặc biệt, \b để khớp toàn bộ từ
                regex = re.compile(r'\b(' + re.escape(term) + r')\b', re.IGNORECASE)
                temp_content = regex.sub(r'<mark>\1</mark>', temp_content)
            highlighted_content = temp_content
        except Exception:
            # Nếu highlight thất bại, vẫn trả về nội dung gốc
            pass
            
    # --- Step 3: Format for HTML and return ---
    content_with_breaks = highlighted_content.replace('\n', '<br>')
    return HTMLResponse(content=content_with_breaks)


# API phục vụ giao diện
@app.get("/")
async def read_root():
    return FileResponse('index.html')
