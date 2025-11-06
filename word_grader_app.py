import streamlit as st
import pandas as pd
import easyocr
import tempfile
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# 페이지 기본 설정
st.set_page_config(page_title="영어 단어 시험 채점기", layout="centered")

st.title("📘 영어 단어 시험 채점 프로그램")
st.caption("필기체 인식 + 자동 채점 + PDF 결과 저장")

# 1️⃣ 정답 스프레드시트 업로드
answer_files = st.file_uploader(
    "정답 스프레드시트를 업로드하세요 (xlsx 여러 개 가능)", 
    type=["xlsx"], 
    accept_multiple_files=True
)

# 2️⃣ 학생 답안 이미지 업로드
answer_images = st.file_uploader(
    "학생의 필기체 답안 이미지를 업로드하세요 (jpg/png 등)", 
    type=["jpg", "png", "jpeg"], 
    accept_multiple_files=True
)

# OCR 모델 로드
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en', 'ko'])

reader = load_ocr()

# 결과 저장용
results = []

# 정답 데이터 통합
def load_all_answers(files):
    all_answers = []
    for file in files:
        df = pd.read_excel(file)
        all_answers.append(df)
    return pd.concat(all_answers, ignore_index=True)

if answer_files and answer_images:
    st.info("채점 중입니다. 잠시만 기다려 주세요...")

    answers_df = load_all_answers(answer_files)

    for img_file in answer_images:
        # OCR 실행
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(img_file.read())
            text = " ".join([t[1] for t in reader.readtext(tmp.name)])
            os.remove(tmp.name)

        correct = 0
        wrong = 0
        corrections = []

        for i, row in answers_df.iterrows():
            word = str(row["word"]).strip().lower()
            meaning = str(row["meaning"]).strip().lower()

            if word in text.lower() or meaning in text.lower():
                correct += 1
            else:
                wrong += 1
                corrections.append(f"{word} → {meaning}")

        results.append({
            "파일명": img_file.name,
            "맞은 개수": correct,
            "틀린 개수": wrong,
            "틀린 부분 수정": corrections
        })

    # 결과표 표시
    results_df = pd.DataFrame(results)
    st.subheader("📊 채점 결과")
    st.dataframe(results_df)

    # PDF 다운로드 생성
    if st.button("PDF로 결과 다운로드"):
        pdf_path = "grading_result.pdf"
        c = canvas.Canvas(pdf_path, pagesize=A4)
        width, height = A4
        y = height - 50
        c.setFont("Helvetica", 12)
        c.drawString(100, y, "영어 단어 시험 채점 결과")
        y -= 30
        for r in results:
            c.drawString(80, y, f"파일: {r['파일명']}")
            y -= 20
            c.drawString(100, y, f"맞은 개수: {r['맞은 개수']}  /  틀린 개수: {r['틀린 개수']}")
            y -= 20
            if r['틀린 부분 수정']:
                c.drawString(120, y, "틀린 부분:")
                y -= 20
                for corr in r['틀린 부분 수정']:
                    c.drawString(140, y, corr)
                    y -= 15
                    if y < 100:
                        c.showPage()
                        y = height - 50
        c.save()

        with open(pdf_path, "rb") as f:
            st.download_button(
                "📄 결과 PDF 다운로드",
                f,
                file_name="채점결과.pdf",
                mime="application/pdf"
            )

        os.remove(pdf_path)
