# import commonly-needed built-in libraries
import string, sys, re, random, os, os.path

# import data handling libraries
import pandas as pd
import polars as pl
import numpy as np

import streamlit as st
import dropbox
from datetime import datetime

# 1. 드롭박스 연결 설정 (Access Token 필요)
# Dropbox 개발자 콘솔에서 발급받은 토큰을 사용합니다.
DROPBOX_ACCESS_TOKEN = "sl.u.AGgeYDybFhI61e437HC3doJQGLinDuw9XWxl2eKtEGpo5eUTHIU8UtDxz1XcwvkvxyiNYp41w998XJE-_v0VjyZtCElkDcXc_B8Q1_wjJQPrXHKxr0gwDU0rpXiZRSYNOGnvRab2gK63ZF5RwGo_x0f5WMds9i96MM0uBMkn5ho641bOFDsTgMGORz2zKQPdHrfmkjRvKv8X2Ggk20WmlI3cEd7BW3l9uyYk6IHDZnk-em6EIWGPm4CPLaWhRqdspdZPkRRsZNOFxrCaZtzypBO6l90_YbaFNBvhCzyf5yB8KzxoCR94hLgxQFYO_D-09OOQMFJvSyMSvLMw1DBPJ8RCZz3AzD2hTwbGXVHpb85MaLu5_0rdIuBRH04kgnt4OpjqxHjHt4C9D8Q57xqVSCIaiETuloyr3b2GSNdgJfZLDfN--Nykb-kNkACrSubU5a-0uHIbMonsAtGqyIB81jUWUuTxLxJ8XdD76oyuR7-42ueyKGxtgCho5YUf9x-j1783jCjW7sc-heJundkiLa4JEdSCixc1_FuJ2cq7Kmcmmdyg4SWWVnoL78qSgkj0Ihh8-gDEzJmIyGfHLfSmifTUu9f-S1i93WLDX-ZE6lTEUlw-OeT0Zw39ichIQPdcrUEzRMyfGy45niikGkFYFeJIrXc9mFbNZiMbJ-FrTDXvdx4nULv4gYiDSxaOSbqUt3RdI4tGEBAIfTspSKsMJ52PPpHFr52UBUkkxL065BBtFctdI9JIqFUslIvjuAhsr3DXTPFg0WYvgKHAgtJHa1sY1aHq0y-SWPxetG7XkFO9W0G_RJnMn6gGBXmkQ792XNKiuw9L0VrN3GI10_pnnS4GvhFkJOB0A2K4kx8YyT0qeDFekhHr0GqT8_HsysxaArBV93BSNAJdCsipxQl5ff6GOewW1rSARHsYdgPZNaBkRk74LlFWpcZvsv-_qAQ30dKRylxrHEO7ASje6Be2154YAcChUfYFmLj6DkbCg9GIsMeB645AOGsO9CU4p0KLON-emTiQERvmi9M2ic758_wMScxvOHeR8T_MkaYg43dJVzKsHA_DEqa4s_-0w7c7FhUKAhUBqfsvfa7BhrRoZ-qtP46ftj4Igwtc7vK8SHjInnOCi_odzWfmVHvBHNz4ekgraQ-ui6qmDeOzLN3d02V6ObHDhZHlN2OZ1VbTiVE16dj_Y36ucMLHQkDF_eDaOC1RBYoTrHUcZP9HlHevgxd6iAJdHishMCsZE01ojOzZKxWP-7bLgbflEDIU9655VcMcX0kVcNT-YT3SybQ6swTcNaRU46K0iCYBccfbgd9WkQ"
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
DROPBOX_FILE_PATH = "/apps/learning_log/learning_data.csv"

# 2. 드롭박스에서 데이터 불러오기 함수
@st.cache_data(ttl=10) # 10초마다 데이터 새로고침 최적화
def load_data_from_dropbox():
    try:
        metadata, res = dbx.files_download(DROPBOX_FILE_PATH)
        df = pd.read_csv(res.raw)
        return df
    except Exception:
        # 파일이 없을 경우 예시 데이터 이미지와 동일한 초기 테이블 생성
        dates = ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05"]
        df = pd.DataFrame({
            "일시": dates,
            "영어": [""] * 5,
            "수학": [""] * 5,
            "한글": [""] * 5,
            "책읽기 등": [""] * 5
        })
        return df

# 3. 드롭박스에 데이터 저장하기 함수
def save_data_to_dropbox(df):
    csv_data = df.to_csv(index=False).encode('utf-8')
    dbx.files_upload(csv_data, DROPBOX_FILE_PATH, mode=dropbox.files.WriteMode.overwrite)
    st.success("드롭박스에 실시간 저장이 완료되었습니다!")

# --- UI 화면 구성 ---
st.set_page_config(layout="wide")

# 상단 탭 메뉴 구성 (요청하신 화면 구조 반영)
tab1, tab2, tab3 = st.tabs(["학습일지", "월별 비교", "학습대상자 정보"])

with tab1:
    st.subheader("일자별 학습 일지 작성")
    
    # 데이터 로드
    df = load_data_from_dropbox()
    
    # Streamlit의 강력한 데이터 편집기 기능 활용 (아이패드 터치 입력 최적화)
    # 이미지와 동일한 주황색 계열 및 편집 환경 제공
    edited_df = st.data_editor(
        df, 
        use_container_width=True,
        num_rows="dynamic",
        disabled=["일시"] # 날짜는 수정 불가하도록 고정
    )
    
    # 저장 버튼 생성
    if st.button("학습 내용 저장하기", type="primary"):
        save_data_to_dropbox(edited_df)

with tab2:
    st.subheader("월별 학습 비교 분석")
    st.write("입력된 데이터를 바탕으로 월별 달성도를 막대그래프나 데이터 분석 대시보드로 시각화하는 영역입니다.")
    # 추후 st.bar_chart 등을 활용해 시각화 확장 가능

with tab3:
    st.subheader("학습대상자 상세 정보")
    st.markdown("""
    - **이름:** 기찡
    - **학년:** 초등학교 2학년 (2026년 기준)
    - **관심 분야:** 수학 게임, 스키, 농구
    """)