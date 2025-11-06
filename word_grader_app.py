import streamlit as st
import pandas as pd
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
from io import BytesIO
from fpdf import FPDF

st.set_page_config(page_title="단어 시험 자동 채점기", layout="wide")

st.title("🧾 단어 시험 자동 채점기 (PDF + 정답 스프레드시트)")

st.write("""
📄 **문제지(PDF)** 파일과  
📊 **정답지(Excel 또는 CSV)** 파일을 업로드하면  
자동으로 채점하고 결과를 PDF로 만들어줍니다.
""")

# PDF 생성 함수
def make_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('Nanum', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', uni=True)
    pdf.set_font('Nanum', size=14)
    pdf.cell(200, 10, txt="단어 시험 채점 결과", ln=True, align='C')
    pdf.ln(10)

    correct = (df["정답여부"] == "O").sum()
    wrong = (df["정답여부"] == "X").sum()
    pdf.cell(200, 10, txt=f"맞은 개수: {correct}개 / 틀린 개수: {wrong}개", ln=True)
    pdf.ln(10)

    for _, row in df.iterrows():
        pdf.multi_cell(0, 8, f"{row['문제']} → {row['학생답안']} (정답: {row['정답']}) → {row['정답여부']}")
        pdf.ln(2)

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

# 업로드 구역
st.subheader("1️⃣ 문제지(PDF) 업로드")
pdf_file = st.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])

st.subheader("2️⃣ 정답지(스프레드시트) 업로드")
answer_file = st.file_uploader("정답지를 업로드하세요 (Excel 또는 CSV)", type=["xlsx", "csv"])

if pdf_file and answer_file:
    with st.spinner("문제지를 분석 중입니다... ⏳"):
        # ① PDF → 이미지 변환
        images = convert_from_bytes(pdf_file.read())

        # ② 이미지 → OCR 인식 (영어 + 한국어)
        ocr_text = ""
        for i, img in enumerate(images):
            ocr_text += f"\n--- Page {i+1} ---\n"
            text = pytesseract.image_to_string(img, lang="eng+kor")
            ocr_text += text

        st.subheader("📋 인식된 텍스트 미리보기")
        st.text_area("OCR 인식 결과", ocr_text, height=200)

        # ③ 정답지 읽기
        if answer_file.name.endswith(".csv"):
            answer_df = pd.read_csv(answer_file)
        else:
            answer_df = pd.read_excel(answer_file)

        # 정답지에 필요한 열이 있는지 확인
        if not all(col in answer_df.columns for col in ["문제", "정답"]):
            st.error("정답지에는 반드시 '문제'와 '정답' 열이 있어야 합니다.")
        else:
            # ④ 채점 로직
            results = []
            for _, row in answer_df.iterrows():
                question = str(row["문제"]).strip()
                answer = str(row["정답"]).strip().lower()

                # OCR 결과에서 해당 단어 찾기
                found = False
                for line in ocr_text.splitlines():
                    if question.lower() in line.lower():
                        student_answer = line.split()[-1]
                        found = True
                        break
                if not found:
                    student_answer = "(인식되지 않음)"

                is_correct = "O" if student_answer.lower() == answer.lower() else "X"
                results.append({
                    "문제": question,
                    "정답": answer,
                    "학생답안": student_answer,
                    "정답여부": is_correct
                })

            result_df = pd.DataFrame(results)

            # 결과 표시
            st.subheader("📊 채점 결과")
            st.dataframe(result_df)

            # PDF 다운로드
            pdf_data = make_pdf(result_df)
            st.download_button(
                label="📥 결과 PDF 다운로드",
                data=pdf_data,
                file_name="grading_result.pdf",
                mime="application/pdf"
            )
else:
    st.info("👆 위 두 파일을 모두 업로드해야 채점이 시작됩니다.")
