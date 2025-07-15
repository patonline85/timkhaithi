# File: indexer.py
import os
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID
from whoosh.analysis import RegexTokenizer, LowercaseFilter

def create_search_index(docs_path, index_dir):
    """
    Hàm này đọc tất cả các tệp .txt trong thư mục docs_path
    và tạo ra một chỉ mục tìm kiếm trong thư mục index_dir.
    """
    # Định nghĩa cấu trúc của chỉ mục
    # - filename: Tên file, dùng để định danh (ID) và sẽ được lưu lại (stored=True)
    # - content: Nội dung file, dùng để tìm kiếm (TEXT)
    # Chúng ta sử dụng tokenizer để xử lý tiếng Việt tốt hơn một chút
    analyzer = RegexTokenizer() | LowercaseFilter()
    schema = Schema(filename=ID(stored=True), 
                    content=TEXT(analyzer=analyzer, stored=True))

    # Kiểm tra và tạo thư mục chứa chỉ mục nếu chưa có
    if not os.path.exists(index_dir):
        os.mkdir(index_dir)

    # Tạo chỉ mục
    print(f"Đang tạo chỉ mục tại '{index_dir}'...")
    ix = create_in(index_dir, schema)
    
    # Mở writer để bắt đầu thêm tài liệu vào chỉ mục
    writer = ix.writer()

    # Duyệt qua tất cả các file trong thư mục tài liệu
    doc_count = 0
    for root, dirs, files in os.walk(docs_path):
        for file in files:
            if file.endswith(".txt"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                        # Thêm tài liệu vào writer
                        writer.add_document(filename=file, content=content)
                        doc_count += 1
                        print(f"Đã thêm file: {file}")

                except Exception as e:
                    print(f"Lỗi khi đọc file {file_path}: {e}")

    # Lưu lại tất cả thay đổi
    print(f"\nĐang lưu chỉ mục ({doc_count} tài liệu)...")
    writer.commit()
    print("Hoàn tất lập chỉ mục!")

# --- CHẠY SCRIPT ---
if __name__ == "__main__":
    # Thay 'path/to/your/3000/docs' bằng đường dẫn thực tế
    documents_directory = "data" 
    index_directory = "search_index"
    
    # Tạo một thư mục data mẫu để chạy thử
    if not os.path.exists(documents_directory):
        os.mkdir(documents_directory)
        with open("data/file1.txt", "w", encoding="utf-8") as f:
            f.write("DataStax Astra DB là một cơ sở dữ liệu tuyệt vời.")
        with open("data/file2.txt", "w", encoding="utf-8") as f:
            f.write("Whoosh là một thư viện tìm kiếm toàn văn cho Python.")
        with open("data/file3.txt", "w", encoding="utf-8") as f:
            f.write("Python rất mạnh mẽ cho các tác vụ xử lý văn bản.")

    create_search_index(documents_directory, index_directory)
