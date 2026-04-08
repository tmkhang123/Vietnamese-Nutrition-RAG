import pdfplumber
import os

def extract_pdf_to_raw():
    # 1. Tự động xác định thư mục chứa script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Liệt kê tất cả các file để kiểm tra
    files_in_dir = os.listdir(current_dir)
    print(f"--- Kiểm tra thư mục: {current_dir} ---")
    print("Các file đang có:", files_in_dir)
    
    # 3. Tìm file nào có chữ 'Dietary' và đuôi '.pdf'
    pdf_file = None
    for f in files_in_dir:
        if "Dietary" in f and f.endswith(".pdf"):
            pdf_file = f
            break
            
    if not pdf_file:
        print("❌ Không tìm thấy file PDF nào có chứa chữ 'Dietary'!")
        return

    pdf_path = os.path.join(current_dir, pdf_file)
    output_path = os.path.join(current_dir, pdf_file.replace(".pdf", ".txt"))

    print(f"🚀 Đang xử lý file: {pdf_file}")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "".join([page.extract_text() + "\n" for page in pdf.pages if page.extract_text()])
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)
        print(f"✅ Xong! Lưu tại: {output_path}")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    extract_pdf_to_raw()