# import commonly-needed built-in libraries
import string, sys, re, random, os, os.path

# import data handling libraries
import streamlit as st
import pandas as pd
import dropbox
import json
from datetime import datetime, timedelta
import holidays

# 1. 드롭박스 연결 설정
DROPBOX_ACCESS_TOKEN = "sl.u.AGgeYDybFhI61e437HC3doJQGLinDuw9XWxl2eKtEGpo5eUTHIU8UtDxz1XcwvkvxyiNYp41w998XJE-_v0VjyZtCElkDcXc_B8Q1_wjJQPrXHKxr0gwDU0rpXiZRSYNOGnvRab2gK63ZF5RwGo_x0f5WMds9i96MM0uBMkn5ho641bOFDsTgMGORz2zKQPdHrfmkjRvKv8X2Ggk20WmlI3cEd7BW3l9uyYk6IHDZnk-em6EIWGPm4CPLaWhRqdspdZPkRRsZNOFxrCaZtzypBO6l90_YbaFNBvhCzyf5yB8KzxoCR94hLgxQFYO_D-09OOQMFJvSyMSvLMw1DBPJ8RCZz3AzD2hTwbGXVHpb85MaLu5_0rdIuBRH04kgnt4OpjqxHjHt4C9D8Q57xqVSCIaiETuloyr3b2GSNdgJfZLDfN--Nykb-kNkACrSubU5a-0uHIbMonsAtGqyIB81jUWUuTxLxJ8XdD76oyuR7-42ueyKGxtgCho5YUf9x-j1783jCjW7sc-heJundkiLa4JEdSCixc1_FuJ2cq7Kmcmmdyg4SWWVnoL78qSgkj0Ihh8-gDEzJmIyGfHLfSmifTUu9f-S1i93WLDX-ZE6lTEUlw-OeT0Zw39ichIQPdcrUEzRMyfGy45niikGkFYFeJIrXc9mFbNZiMbJ-FrTDXvdx4nULv4gYiDSxaOSbqUt3RdI4tGEBAIfTspSKsMJ52PPpHFr52UBUkkxL065BBtFctdI9JIqFUslIvjuAhsr3DXTPFg0WYvgKHAgtJHa1sY1aHq0y-SWPxetG7XkFO9W0G_RJnMn6gGBXmkQ792XNKiuw9L0VrN3GI10_pnnS4GvhFkJOB0A2K4kx8YyT0qeDFekhHr0GqT8_HsysxaArBV93BSNAJdCsipxQl5ff6GOewW1rSARHsYdgPZNaBkRk74LlFWpcZvsv-_qAQ30dKRylxrHEO7ASje6Be2154YAcChUfYFmLj6DkbCg9GIsMeB645AOGsO9CU4p0KLON-emTiQERvmi9M2ic758_wMScxvOHeR8T_MkaYg43dJVzKsHA_DEqa4s_-0w7c7FhUKAhUBqfsvfa7BhrRoZ-qtP46ftj4Igwtc7vK8SHjInnOCi_odzWfmVHvBHNz4ekgraQ-ui6qmDeOzLN3d02V6ObHDhZHlN2OZ1VbTiVE16dj_Y36ucMLHQkDF_eDaOC1RBYoTrHUcZP9HlHevgxd6iAJdHishMCsZE01ojOzZKxWP-7bLgbflEDIU9655VcMcX0kVcNT-YT3SybQ6swTcNaRU46K0iCYBccfbgd9WkQ"
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

DATA_FILE_PATH = "/apps/learning_log/learning_data.csv"
CONFIG_FILE_PATH = "/apps/learning_log/app_config.json"

# 한국 공휴일 정보 가져오기 (2026년 기준)
kr_holidays = holidays.KR(years=2026)

# 2. 드롭박스 데이터 로드/저장 함수
def load_file_from_dropbox(path, is_csv=True):
    try:
        metadata, res = dbx.files_download(path)
        if is_csv:
            return pd.read_csv(res.raw)
        else:
            return json.loads(res.raw.read().decode('utf-8'))
    except Exception:
        if is_csv:
            return pd.DataFrame(columns=["일시", "영어", "수학", "한글", "책읽기 등", "비고"])
        else:
            return {
                "student_info": {
                    "name": "기찡", "birthdate": "2018-04-08", "grade": "초등학교 2학년", "note": "농구와 스키를 좋아함"
                },
                "reward_info": {
                    "monthly_goal": 20, "reward_desc": "주말 스키장 가기!"
                },
                "dropdown_options": {
                    "영어": ["선택 안 함", "파닉스", "동화책", "따라쓰기"],
                    "수학": ["선택 안 함", "구구단", "연산", "사고력"],
                    "한글": ["선택 안 함", "받아쓰기", "한글읽기"],
                    "책읽기 등": ["선택 안 함", "위인전", "과학잡지"]
                }
            }

def save_file_to_dropbox(data, path, is_csv=True):
    if is_csv:
        content = data.to_csv(index=False).encode('utf-8')
    else:
        content = json.dumps(data, ensure_ascii=False, indent=4).encode('utf-8')
    dbx.files_upload(content, path, mode=dropbox.files.WriteMode.overwrite)

# 데이터 초기 로드
if "main_data" not in st.session_state:
    st.session_state.main_data = load_file_from_dropbox(DATA_FILE_PATH, is_csv=True)
if "app_config" not in st.session_state:
    st.session_state.app_config = load_file_from_dropbox(CONFIG_FILE_PATH, is_csv=False)

config = st.session_state.app_config

# --- 💡 KeyError 방지: 과거 설정 파일 호환성 업데이트 로직 추가 ---
config_updated = False
if "reward_info" not in config:
    config["reward_info"] = {"monthly_goal": 20, "reward_desc": "주말 스키장 가기!"}
    config_updated = True
if "student_info" not in config:
    config["student_info"] = {"name": "기찡", "birthdate": "2018-04-08", "grade": "초등학교 2학년", "note": "농구와 스키를 좋아함"}
    config_updated = True

if config_updated:
    save_file_to_dropbox(config, CONFIG_FILE_PATH, is_csv=False)
    st.session_state.app_config = config
# ------------------------------------------------------------------

main_df = st.session_state.main_data

# 3. 유틸리티 함수 (나이 계산, 연속 학습 계산)
def calculate_precise_age(birthdate_str):
    birth = datetime.strptime(birthdate_str, "%Y-%m-%d").date()
    today = datetime.now().date()
    years = today.year - birth.year
    months = today.month - birth.month
    if today.day < birth.day: months -= 1
    if months < 0: years -= 1; months += 12
    return f"{years}세 {months}개월"

def calculate_streak(df):
    if df.empty: return 0
    df['is_done'] = df.apply(lambda r: any(r[c] != "선택 안 함" for c in ["영어", "수학", "한글", "책읽기 등"]), axis=1)
    done_dates = sorted([datetime.strptime(d, "%Y-%m-%d").date() for d in df[df['is_done']]['일시'].unique()], reverse=True)
    
    if not done_dates: return 0
    
    today = datetime.now().date()
    if (today - done_dates[0]).days > 1: return 0
    
    streak = 0
    current_check = done_dates[0]
    for d in done_dates:
        if (current_check - d).days <= 1:
            streak += 1
            current_check = d
        else: break
    return streak

# --- UI 구성 ---
st.set_page_config(layout="wide", page_title="기찡이 학습 관리 앱")

# 메인 헤더 및 스트릭 뱃지 표시
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.title("🧑‍🎓 기찡이 학습 관리 시스템")
with col_h2:
    streak_val = calculate_streak(main_df)
    st.metric("🔥 연속 학습 기록", f"{streak_val}일째")

tab1, tab2, tab3, tab4 = st.tabs(["📝 학습일지", "📊 월별 비교", "🧑‍🎓 정보 관리", "⚙️ 학습내용 설정"])

# 📍 1. 학습일지 탭
with tab1:
    col_date, col_chk = st.columns([3, 1])
    with col_date:
        selected_date = st.date_input("기준 날짜 선택:", datetime.now().date())
    with col_chk:
        show_reading = st.checkbox("📖 '책읽기 등' 펼치기", value=False)
    
    start_of_week = selected_date - timedelta(days=selected_date.weekday())
    week_dates = [start_of_week + timedelta(days=i) for i in range(7)]
    
    week_rows = []
    days_ko = ["월", "화", "수", "목", "금", "토", "일"]
    for d in week_dates:
        date_str = d.strftime("%Y-%m-%d")
        holiday_name = kr_holidays.get(d)
        prefix = "🔴 " if (holiday_name or d.weekday() in [5, 6]) else ""
        label = f"{prefix}{date_str} ({days_ko[d.weekday()]})" + (f" [{holiday_name}]" if holiday_name else "")
        week_rows.append({"일시": label, "pure_date": date_str})
    
    display_df = pd.DataFrame(week_rows)
    for col in ["영어", "수학", "한글", "책읽기 등", "비고"]:
        display_df[col] = "" if col == "비고" else "선택 안 함"
        for idx, row in display_df.iterrows():
            if not main_df.empty:
                match = main_df[main_df["일시"] == row["pure_date"]]
                if not match.empty:
                    display_df.at[idx, col] = match.iloc[0][col] if col in match.columns else ("선택 안 함" if col != "비고" else "")

    show_cols = ["일시", "영어", "수학", "한글"]
    if show_reading: show_cols.append("책읽기 등")
    show_cols.append("비고")

    options = config["dropdown_options"]
    col_config = {
        "일시": st.column_config.TextColumn("일시", disabled=True),
        "영어": st.column_config.SelectboxColumn("영어", options=options["영어"]),
        "수학": st.column_config.SelectboxColumn("수학", options=options["수학"]),
        "한글": st.column_config.SelectboxColumn("한글", options=options["한글"]),
        "비고": st.column_config.TextColumn("비고 (메모)")
    }
    if show_reading: col_config["책읽기 등"] = st.column_config.SelectboxColumn("책읽기 등", options=options["책읽기 등"])
    
    edited_df = st.data_editor(display_df[show_cols], use_container_width=True, column_config=col_config, key="editor_v5")
    
    if st.button("학습 내용 저장하기", type="primary"):
        for idx, row in edited_df.iterrows():
            pure_d = display_df.at[idx, "pure_date"]
            main_df = main_df[main_df["일시"] != pure_d]
            new_r = {"일시": pure_d, "영어": row["영어"], "수학": row["수학"], "한글": row["한글"], "비고": row["비고"]}
            new_r["책읽기 등"] = row["책읽기 등"] if "책읽기 등" in row else display_df.at[idx, "책읽기 등"]
            main_df = pd.concat([main_df, pd.DataFrame([new_r])], ignore_index=True)
        st.session_state.main_data = main_df
        save_file_to_dropbox(main_df, DATA_FILE_PATH)
        st.success("저장이 완료되었습니다!")
