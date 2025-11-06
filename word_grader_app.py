import streamlit as st
import pandas as pd
import pytesseract
from PIL import Image
from io import BytesIO
from fpdf import FPDF

st.set_page_config(page_title="단어 시험 채점기", layout="wide")

st.title("📘 단어 시험 채점 프로그램 (OCR 버전)")

st.write("""
이미지나 스프레드시트를 업로드하면 자동으로 단어 시험을 채점해주는 프로그램입니다.  
- 📄 엑셀 여러 개 업로드 가능  
- 📸 이미지(OCR)도 자동 인식 가능  
- 📊 맞은 개수, 틀린 개수 자동 계산  
- 📥 결과는 PDF로 다운로드 가능
""")

# PDF 생성 함수
def make_pdf(results):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('Nanum', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', uni=True)
    pdf.set_font('Nanum', size=14)
    pdf.cell(200, 10, txt="단어 시험 채점 결과", ln=True, align='C')
    pdf.ln(10)

    for name, df in results.items():
        pdf.cell(200, 10, txt=f"[{name}] 결과", ln=True)
        pdf.ln(5)
        correct = (df["정답여부"] == "O").sum()
        wrong = (df["정답여부"] == "X").sum()
        pdf.cell(200, 10, txt=f"맞은 개수: {correct}개 / 틀린 개수: {wrong}개", ln=True)
        pdf.ln(5)
        for _, row in df.iterrows():
            pdf.cell(200, 10, txt=f"{row['문제']} → {row['학생답안']} ({row['정답여부']})", ln=True)
        pdf.ln(10)

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

# 업로드 구역
uploaded_files = st.file_uploader("📂 엑셀 또는 이미지 파일을 올려주세요 (여러 개 가능)", accept_multiple_files=True)

if uploaded_files:
    results = {}

    for file in uploaded_files:
        filename = file.name
        st.subheader(f"📘 {filename}")

        if filename.endswith((".xlsx", ".csv")):
            # 엑셀 or CSV
            if filename.endswith(".csv"):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            # 컬럼 확인
            if "문제" in df.columns and "정답" in df.columns and "학생답안" in df.columns:
                df["정답여부"] = df.apply(lambda x: "O" if str(x["정답"]).strip().lower() == str(x["학생답안"]).strip().lower() else "X", axis=1)
                st.dataframe(df)
                results[filename] = df
            else:
                st.warning("⚠️ '문제', '정답', '학생답안' 열이 필요합니다.")

        elif filename.lower().endswith((".png", ".jpg", ".jpeg")):
            # 이미지 (OCR 인식)
            img = Image.open(file)
            text = pytesseract.image_to_string(img, lang="eng+kor")
            st.text_area("인식된 텍스트", text, height=200)
            st.info("이 이미지는 단어시험지가 아니라면 엑셀 파일을 사용하는 게 더 정확합니다.")
        else:
            st.warning("지원하지 않는 파일 형식입니다.")

    # PDF 다운로드 버튼
    if results:
        pdf_data = make_pdf(results)
        st.download_button(
            label="📥 PDF로 결과 다운로드",
            data=pdf_data,
            file_name="grading_result.pdf",
            mime="application/pdf",
        )
