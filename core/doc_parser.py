import os


def parse_file(uploaded_file) -> dict:
    file_name = uploaded_file.name
    ext = os.path.splitext(file_name)[1].lower()
    content = ""

    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(uploaded_file)
            content = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            print(f"[PDF 解析失败] {file_name}: {e}")
            content = ""
    elif ext in (".md", ".txt"):
        try:
            content = uploaded_file.read().decode("utf-8")
        except Exception as e:
            print(f"[文件读取失败] {file_name}: {e}")
            content = ""
    else:
        print(f"[不支持的格式] {file_name}")

    return {
        "file_name": file_name,
        "content": content,
        "format": ext.lstrip("."),
        "word_count": len(content),
    }
