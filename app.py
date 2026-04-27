import os
from flask import Flask, request, render_template, send_file
import fitz # PyMuPDF

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# 合併邏輯
@app.route('/merge', methods=['POST'])
def merge():
    files = request.files.getlist('files')
    output = "merged.pdf"
    result_doc = fitz.open()
    try:
        for file in files:
            path = f"temp_{file.filename}"
            file.save(path)
            curr = fitz.open(path)
            result_doc.insert_pdf(curr)
            curr.close()
            os.remove(path)
        result_doc.save(output)
        result_doc.close()
        return send_file(output, as_attachment=True)
    except: return "Error", 500

# 壓縮邏輯 (省記憶體分頁版)
@app.route('/compress', methods=['POST'])
def compress():
    file = request.files['file']
    target_mb = int(request.form.get('target', 5))
    in_path, out_path = "in.pdf", "out.pdf"
    file.save(in_path)
    try:
        doc = fitz.open(in_path)
        new_doc = fitz.open()
        for page in doc:
            pix = page.get_pixmap(dpi=130) # 兼顧畫質與記憶體
            new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
            new_page.insert_image(page.rect, pixmap=pix)
            pix = None
        new_doc.save(out_path, garbage=3, deflate=True)
        new_doc.close()
        doc.close()
        return send_file(out_path, as_attachment=True)
    except: return "Error", 500
    finally:
        if os.path.exists(in_path): os.remove(in_path)

if __name__ == '__main__':
    app.run(debug=True)