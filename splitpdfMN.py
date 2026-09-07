import streamlit as st
import fitz  # PyMuPDF
import io

# ตั้งค่าหน้าเพจ
st.set_page_config(page_title="PDF Slide Splitter ✂️", page_icon="📄")

st.title("✂️ ระบบแยกสไลด์ PDF (สำหรับสไลด์ที่รวมหน้า)")
st.write("เครื่องมือสำหรับหั่นเอกสาร PDF ที่รวม 2 หรือ 4 สไลด์ใน 1 หน้า ออกเป็นแผ่นละ 1 หน้า (ขนาดไฟล์จะใกล้เคียงเดิม ไม่บวม)")

# ส่วนอัปโหลดไฟล์
uploaded_file = st.file_uploader("เลือกไฟล์ PDF (สูงสุด 500MB)", type=["pdf"])

# ส่วนเลือกรูปแบบการแยก
mode = st.radio(
    "เลือกรูปแบบการหั่นเอกสาร:",
    ("2 แผ่นใน 1 หน้า (แบ่งครึ่ง)", "4 แผ่นใน 1 หน้า (แบ่งสี่ส่วน)")
)

if uploaded_file is not None:
    # ตรวจสอบขนาดไฟล์โปรแกรมเมติก (กรณี 500MB = 500 * 1024 * 1024 bytes)
    MAX_SIZE = 500 * 1024 * 1024
    if uploaded_file.size > MAX_SIZE:
        st.error(f"❌ ขนาดไฟล์เกิน 500MB (ไฟล์นี้มีขนาด {uploaded_file.size / (1024*1024):.2f} MB)")
    else:
        # ปุ่มเริ่มประมวลผล
        if st.button("🚀 เริ่มทำการแยกไฟล์"):
            with st.spinner("กำลังประมวลผล... โปรดรอสักครู่ (ไฟล์ขนาดใหญ่อาจใช้เวลาสักพัก)"):
                try:
                    # อ่านไฟล์ PDF จากการอัปโหลด
                    pdf_bytes = uploaded_file.read()
                    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                    new_doc = fitz.open() # สร้าง PDF เปล่า
                    
                    # ประมวลผลทีละหน้า
                    for page_num in range(len(doc)):
                        page = doc[page_num]
                        rect = page.rect
                        w = rect.width
                        h = rect.height
                        
                        rects = []
                        if "2" in mode:
                            # เช็คว่าเป็นกระดาษแนวนอนหรือแนวตั้ง
                            if w > h:
                                # แนวนอน (หั่นซ้าย-ขวา)
                                rects.append(fitz.Rect(0, 0, w/2, h))
                                rects.append(fitz.Rect(w/2, 0, w, h))
                            else:
                                # แนวตั้ง (หั่นบน-ล่าง)
                                rects.append(fitz.Rect(0, 0, w, h/2))
                                rects.append(fitz.Rect(0, h/2, w, h))
                                
                        elif "4" in mode:
                            # แบ่ง 4 ส่วน (ซ้ายบน, ขวาบน, ซ้ายล่าง, ขวาล่าง)
                            rects.append(fitz.Rect(0, 0, w/2, h/2))      # บนซ้าย
                            rects.append(fitz.Rect(w/2, 0, w, h/2))      # บนขวา
                            rects.append(fitz.Rect(0, h/2, w/2, h))      # ล่างซ้าย
                            rects.append(fitz.Rect(w/2, h/2, w, h))      # ล่างขวา

                        # คัดลอกหน้าและครอบตัด
                        for r in rects:
                            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                            new_page = new_doc[-1]
                            new_page.set_cropbox(r)

                    # บันทึกลงหน่วยความจำ
                    out_stream = io.BytesIO(new_doc.write(garbage=4, deflate=True))
                    out_stream.seek(0)
                    
                    doc.close()
                    new_doc.close()
                    
                    st.success("✅ ประมวลผลเสร็จสมบูรณ์!")
                    
                    # ปุ่มสำหรับดาวน์โหลด
                    st.download_button(
                        label="📥 ดาวน์โหลดไฟล์ PDF ที่แยกแล้ว",
                        data=out_stream,
                        file_name=f"split_{uploaded_file.name}",
                        mime="application/pdf"
                    )

                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")
