import os, uuid
from flask import Flask, request, render_template, send_file, after_this_request
import fitz

app = Flask(__name__)

# 安全刪除工具
def safe_remove(paths):
    for p in paths:
        try:
            if os.path.exists(p): os.remove(p)
        except: pass

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/compress', methods=['POST'])
def compress():
    file = request.files.get('file')
    target = int(request.form.get('target', 5))
    if not file: return "Missing file", 400
    
    uid = str(uuid.uuid4())
    in_p, out_p = f"in_{uid}.pdf", f"out_{uid}.pdf"
    file.save(in_p)
    
    @after_this_request
    def cleanup(response):
        safe_remove([in_p, out_p])
        return response

    try:
        doc = fitz.open(in_p)
        new_doc = fitz.open()
        
        # 根據目標設定畫質 (DPI)
        dpi = 90 if target <= 4 else (120 if target <= 6 else 160)
        
        for page in doc:
            pix = page.get_pixmap(dpi=dpi)
            new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
            new_page.insert_image(page.rect, pixmap=pix)
            pix = None # 釋放記憶體
            
        new_doc.save(out_p, garbage=3, deflate=True)
        new_doc.close()
        doc.close()
        return send_file(out_p, as_attachment=True, download_name=f"fixed_{file.filename}")
    except Exception as e:
        print(f"Error: {e}")
        return "Internal Error", 500

@app.route('/merge', methods=['POST'])
def merge():
    files = request.files.getlist('files')
    uid = str(uuid.uuid4())
    out_p = f"merged_{uid}.pdf"
    res_doc = fitz.open()
    temp_list = []

    @after_this_request
    def cleanup(response):
        safe_remove(temp_list + [out_p])
        return response

    try:
        for f in files:
            p = f"tmp_{uuid.uuid4()[:8]}_{f.filename}"
            f.save(p)
            temp_list.append(p)
            curr = fitz.open(p)
            res_doc.insert_pdf(curr)
            curr.close()
        res_doc.save(out_p)
        res_doc.close()
        return send_file(out_p, as_attachment=True, download_name="merged_pro.pdf")
    except:
        return "Error", 500

if __name__ == '__main__':
    app.run(debug=True)