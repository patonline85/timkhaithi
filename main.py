# File: main.py (đã cập nhật cho deployment)
import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from whoosh.index import open_dir
from whoosh.qparser import QueryParser
from whoosh.highlight import HtmlFormatter, Highlighter, WholeFragmenter

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

# === API ĐỌC FILE ĐÃ ĐƯỢC NÂNG CẤP ĐỂ HIGHLIGHT ===
@app.get("/document/")
def get_document(filename: str = Query(..., min_length=1), query: str | None = Query(None)):
    requested_path = os.path.join(ABS_DATA_DIR, filename)
    real_path = os.path.realpath(requested_path)
    
    if not real_path.startswith(ABS_DATA_DIR):
        raise HTTPException(status_code=400, detail="Truy cập file không hợp lệ.")

    if not os.path.exists(real_path):
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")

    try:
        with open(real_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Nếu có từ khóa tìm kiếm, thực hiện làm nổi bật
        if query and ix:
            qparser = QueryParser("content", ix.schema)
            q = qparser.parse(query)
            
            formatter = HtmlFormatter(tagname="mark")
            # Sửa lỗi: Sử dụng phương thức highlight() cũ hơn và tương thích hơn
            highlighter = Highlighter(formatter=formatter)
            
            # Trích xuất các từ khóa từ câu truy vấn
            terms = {term for fieldname, term in q.all_terms() if fieldname == "content"}
            
            # Sử dụng phương thức highlight() thay vì highlight_text()
            highlighted_content = highlighter.highlight(content, terms, WholeFragmenter())
            
            highlighted_content_with_breaks = highlighted_content.replace('\n', '<br>')
            return HTMLResponse(content=highlighted_content_with_breaks)
        else:
            content_with_breaks = content.replace('\n', '<br>')
            return HTMLResponse(content=content_with_breaks)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi đọc file: {e}")


# API phục vụ giao diện
@app.get("/")
async def read_root():
    return FileResponse('index.html')
