import streamlit as st
import fitz  # PyMuPDF
import io

# ----------------- ตั้งค่าหน้าเว็บ -----------------
st.set_page_config(page_title="PDF Custom Splitter ✂️", page_icon="📄")
st.title("✂️ ระบบแยกสไลด์ PDF (ตั้งค่าอิสระ)")

# ----------------- ส่วนตั้งค่าการแบ่ง -----------------
st.subheader("⚙️ ตั้งค่าการแบ่งหน้า")
st.write("เลือกรูปแบบที่ต้องการ (ค่าเริ่มต้นคือแบ่งครึ่งบน-ล่าง)")

col1, col2 = st.columns(2)

with col1:
    split_vertical = st.checkbox("⬇️ แบ่งตามแนวตั้ง (หั่น บน-ล่าง)", value=True)
    if split_vertical:
        rows = st.number_input("จำนวนส่วน (แนวตั้ง)", min_value=2, max_value=10, value=2)
    else:
        rows = 1

with col2:
    split_horizontal = st.checkbox("➡️ แบ่งตามแนวนอน (หั่น ซ้าย-ขวา)", value=False)
    if split_horizontal:
        cols = st.number_input("จำนวนส่วน (แนวนอน)", min_value=2, max_value=10, value=2)
    else:
        cols = 1

# ----------------- แสดงตัวอย่าง (Preview) -----------------
st.markdown("### 👁️ ตัวอย่างการแบ่ง (Preview)")
st.write(f"ผลลัพธ์: 1 หน้าเดิม จะถูกแยกออกเป็น **{rows * cols} หน้า** เรียงตามลำดับตัวเลข")

# สร้าง CSS Grid เพื่อวาดรูปจำลองกระดาษ
grid_html = f"""
<div style="
    display: grid; 
    grid-template-columns: repeat({cols}, 1fr); 
    grid-template-rows: repeat({rows}, 1fr); 
    gap: 3px; 
    width: 200px; 
    height: 280px; 
    background-color: #333; 
    border: 3px solid #111;
    border-radius: 4px;
    margin-bottom: 20px;
">
"""
# วนลูปสร้างกล่องตัวเลขตามจำนวนส่วน
for i in range(rows * cols):
    grid_html += f'''
    <div style="
        background-color: #fff; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        font-size: 20px; 
        font-weight: bold; 
        color: #0066cc;
    ">{i+1}</div>
    '''
grid_html += "</div>"
st.markdown(grid_html, unsafe_allow_html=True)


# ----------------- ส่วนอัปโหลดและประมวลผล -----------------
st.markdown("---")
uploaded_file = st.file_uploader("📂 เลือกไฟล์ PDF (สูงสุด 500MB)", type=["pdf"])

if uploaded_file is not None:
    if not split_vertical and not split_horizontal:
        st.warning("⚠️ คุณยังไม่ได้ติ๊กเลือกการแบ่งหน้าเลย (ไฟล์ผลลัพธ์จะเหมือนต้นฉบับ)")
        
    MAX_SIZE = 500 * 1024 * 1024
    if uploaded_file.size > MAX_SIZE:
        st.error(f"❌ ขนาดไฟล์เกิน 500MB (ไฟล์นี้มีขนาด {uploaded_file.size / (1024*1024):.2f} MB)")
    else:
        if st.button("🚀 เริ่มทำการแยกไฟล์"):
            with st.spinner("กำลังประมวลผล... โปรดรอสักครู่"):
                try:
                    pdf_bytes = uploaded_file.read()
                    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                    new_doc = fitz.open()
                    
                    for page_num in range(len(doc)):
                        page = doc[page_num]
                        w = page.rect.width
                        h = page.rect.height
                        
                        # คำนวณความกว้างและความสูงของแต่ละช่อง
                        cell_w = w / cols
                        cell_h = h / rows
                        
                        # วนลูปตัดกรอบจาก ซ้ายไปขวา, บนลงล่าง
                        rects = []
                        for r in range(rows):
                            for c in range(cols):
                                x0 = c * cell_w
                                y0 = r * cell_h
                                x1 = (c + 1) * cell_w
                                y1 = (r + 1) * cell_h
                                rects.append(fitz.Rect(x0, y0, x1, y1))
                                
                        # คัดลอกหน้ามาซ้ำๆ แล้วบังคับขอบเขต (Cropbox) เพื่อไม่ให้ไฟล์ใหญ่ขึ้น
                        for rect in rects:
                            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                            new_page = new_doc[-1]
                            new_page.set_cropbox(rect)

                    # เซฟลงหน่วยความจำพร้อมบีบอัดขยะส่วนเกิน
                    out_stream = io.BytesIO(new_doc.write(garbage=4, deflate=True))
                    out_stream.seek(0)
                    
                    doc.close()
                    new_doc.close()
                    
                    st.success(f"✅ ประมวลผลเสร็จสิ้น! เอกสารใหม่มีทั้งหมด {rows * cols * len(doc)} หน้า")
                    
                    st.download_button(
                        label="📥 ดาวน์โหลดไฟล์ PDF",
                        data=out_stream,
                        file_name=f"split_custom_{uploaded_file.name}",
                        mime="application/pdf"
                    )

                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")
