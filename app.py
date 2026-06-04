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
            return pd.DataFrame(columns=["일시", "영어", "수학", "한글", "책읽기 등"])
        else:
            return {
                "student_info": {
                    "name": "기찡",
                    "birthdate": "2018-04-08",
                    "grade": "초등학교 2학년",
                    "note": "농구와 스키를 좋아함"
                },
                "dropdown_options": {
                    "영어": ["선택 안 함", "파닉스 1단원", "영어 동화책 읽기", "원서 따라쓰기"],
                    "수학": ["선택 안 함", "구구단 3단", "연산 문제집 2장", "사고력 수학"],
                    "한글": ["선택 안 함", "받아쓰기 연습", "한글 동화 읽기"],
                    "책읽기 등": ["선택 안 함", "위인전 읽기", "과학 잡지 정독"]
                }
            }

def save_file_to_dropbox(data, path, is_csv=True):
    if is_csv:
        content = data.to_csv(index=False).encode('utf-8')
    else:
        content = json.dumps(data, ensure_ascii=False, indent=4).encode('utf-8')
    dbx.files_upload(content, path, mode=dropbox.files.WriteMode.overwrite)

# 데이터 초기 로드 및 세션 상태 저장
if "main_data" not in st.session_state:
    st.session_state.main_data = load_file_from_dropbox(DATA_FILE_PATH, is_csv=True)
if "app_config" not in st.session_state:
    st.session_state.app_config = load_file_from_dropbox(CONFIG_FILE_PATH, is_csv=False)

config = st.session_state.app_config

# 3. 나이 및 개월 수 자동 계산 함수
def calculate_precise_age(birthdate_str):
    birth = datetime.strptime(birthdate_str, "%Y-%m-%d").date()
    today = datetime.now().date()
    
    years = today.year - birth.year
    months = today.month - birth.month
    
    if today.day < birth.day:
        months -= 1
        
    if months < 0:
        years -= 1
        months += 12
        
    return f"{years}세 {months}개월"

# --- UI 화면 구성 ---
st.set_page_config(layout="wide", page_title="기찡이 학습 관리 앱")
st.title("🧑‍🎓 기찡이 학습 관리 시스템")

# 상단 탭 메뉴 구성
tab1, tab2, tab3, tab4 = st.tabs(["📝 학습일지", "📊 월별 비교", "🧑‍🎓 학습대상자 정보", "⚙️ 학습내용 설정"])

# 📍 1. 학습일지 탭
with tab1:
    st.subheader("일자별 학습 일지 작성 및 조회")
    
    # 상단 메뉴 배치 (날짜 선택 및 책읽기 접기/기능 토글)
    col_date, col_chk = st.columns([3, 1])
    with col_date:
        selected_date = st.date_input("조회할 주간의 기준 날짜를 선택하세요:", datetime.now().date())
    with col_chk:
        # [요구사항 1] 체크박스를 통해 엑셀의 그룹핑처럼 숨김/열기 제어
        show_reading = st.checkbox("📖 '책읽기 등' 메뉴 펼치기", value=False)
    
    # 선택한 날짜가 속한 주의 월요일부터 일요일까지 7일 계산
    start_of_week = selected_date - timedelta(days=selected_date.weekday())
    week_dates = [start_of_week + timedelta(days=i) for i in range(7)]
    
    week_rows = []
    days_ko = ["월", "화", "수", "목", "금", "토", "일"]
    
    for d in week_dates:
        date_str = d.strftime("%Y-%m-%d")
        day_name = days_ko[d.weekday()]
        
        holiday_name = kr_holidays.get(d)
        if holiday_name:
            display_date = f"🔴 {date_str} ({day_name}) [{holiday_name}]"
        elif d.weekday() in [5, 6]:
            display_date = f"🔴 {date_str} ({day_name})"
        else:
            display_date = f"{date_str} ({day_name})"
            
        week_rows.append({"일시": display_date, "pure_date": date_str})
    
    display_df = pd.DataFrame(week_rows)
    
    # 기존 데이터 불러와 병합
    main_df = st.session_state.main_data
    for col in ["영어", "수학", "한글", "책읽기 등"]:
        display_df[col] = "선택 안 함"
        for idx, row in display_df.iterrows():
            pure_d = row["pure_date"]
            if not main_df.empty:
                match = main_df[main_df["일시"] == pure_d]
                if not match.empty and col in match.columns:
                    display_df.at[idx, col] = match.iloc[0][col]

    # 화면에 노출할 컬럼 동적 제어
    display_cols = ["일시", "영어", "수학", "한글"]
    if show_reading:
        display_cols.append("책읽기 등")

    options = config["dropdown_options"]
    
    col_config_dict = {
        "일시": st.column_config.TextColumn("일시", disabled=True),
        "영어": st.column_config.SelectboxColumn("영어", options=options.get("영어", [])),
        "수학": st.column_config.SelectboxColumn("수학", options=options.get("수학", [])),
        "한글": st.column_config.SelectboxColumn("한글", options=options.get("한글", []))
    }
    if show_reading:
        col_config_dict["책읽기 등"] = st.column_config.SelectboxColumn("책읽기 등", options=options.get("책읽기 등", []))
    
    edited_df = st.data_editor(
        display_df[display_cols],
        use_container_width=True,
        column_config=col_config_dict,
        key="editor_week"
    )
    
    if st.button("학습 내용 저장하기", type="primary"):
        for idx, row in edited_df.iterrows():
            pure_d = display_df.at[idx, "pure_date"]
            
            if not main_df.empty:
                main_df = main_df[main_df["일시"] != pure_d]
            
            # '책읽기 등'이 숨겨져 있을 때는 기존 로드된 데이터를 그대로 유지하여 덮어씀
            reading_val = row["책읽기 등"] if "책읽기 등" in row else display_df.at[idx, "책읽기 등"]
            
            new_row = {
                "일시": pure_d,
                "영어": row["영어"],
                "수학": row["수학"],
                "한글": row["한글"],
                "책읽기 등": reading_val
            }
            main_df = pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True)
            
        st.session_state.main_data = main_df
        save_file_to_dropbox(main_df, DATA_FILE_PATH, is_csv=True)
        st.success(f"{start_of_week.strftime('%m월 %d일')} 주간의 학습 일지가 저장 및 동기화되었습니다!")

# 📍 2. 월별 비교 탭 [요구사항 2 구현 완료]
with tab2:
    st.subheader("📊 월별 학습 달성도 비교")
    
    main_df = st.session_state.main_data
    
    # 데이터가 비어있거나 실질적인 기록이 없는 경우 예외 처리
    if main_df.empty:
        st.info("아직 기록된 학습 데이터가 없습니다. 학습일지를 작성하고 저장해 주세요!")
    else:
        analysis_df = main_df.copy()
        # 날짜에서 YYYY-MM 문자열 파싱
        analysis_df['년월'] = analysis_df['일시'].apply(lambda x: str(x)[:7] if pd.notna(x) else "")
        
        subjects = ["영어", "수학", "한글", "책읽기 등"]
        monthly_counts = []
        
        unique_months = sorted([m for m in analysis_df['년월'].unique() if m])
        
        if not unique_months:
            st.info("분석할 수 있는 유효한 날짜 데이터가 부족합니다.")
        else:
            for month in unique_months:
                month_data = analysis_df[analysis_df['년월'] == month]
                row_data = {"월": month}
                for sub in subjects:
                    if sub in month_data.columns:
                        # 유효한 학습 횟수 필터링 (선택 안 함, 누락값 제외)
                        done_count = month_data[
                            (month_data[sub] != "선택 안 함") & 
                            (month_data[sub].notna()) & 
                            (month_data[sub] != "")
                        ].shape[0]
                        row_data[sub] = done_count
                    else:
                        row_data[sub] = 0
                monthly_counts.append(row_data)
            
            chart_df = pd.DataFrame(monthly_counts).set_index("월")
            
            # 1. 수치 요약 표 데이터프레임 노출
            st.markdown("#### 📅 월별 과목별 학습 완료 횟수 요약 (단위: 회)")
            st.dataframe(chart_df, use_container_width=True)
            
            # 2. 직관적인 시각화 차트 연동
            st.markdown("#### 📈 학습 달성도 비교 그래프")
            st.bar_chart(chart_df)

# 📍 3. 학습대상자 정보 탭
with tab3:
    st.subheader("학습대상자 상세 정보 관리")
    info = config["student_info"]
    
    edit_name = st.text_input("이름", value=info["name"])
    edit_birth = st.text_input("생년월일 (YYYY-MM-DD)", value=info["birthdate"])
    
    try:
        precise_age = calculate_precise_age(edit_birth)
        st.info(f"💡 현재 나이 기준 계산 결과: **{precise_age}**")
    except:
        st.error("생년월일 형식을 YYYY-MM-DD 형태로 정확히 입력해 주세요.")
        
    edit_grade = st.text_input("학년", value=info["grade"])
    edit_note = st.text_area("특이사항", value=info["note"])
    
    if st.button("학생 정보 저장하기"):
        config["student_info"] = {
            "name": edit_name,
            "birthdate": edit_birth,
            "grade": edit_grade,
            "note": edit_note
        }
        st.session_state.app_config = config
        save_file_to_dropbox(config, CONFIG_FILE_PATH, is_csv=False)
        st.success("학습대상자 정보가 업데이트되었습니다!")

# 📍 4. 학습내용 설정 탭
with tab4:
    st.subheader("과목별 드롭다운 학습내용 설정")
    st.write("학습일지에서 선택할 드롭다운 항목들을 관리합니다. 쉼표(,)로 구분하여 입력해 주세요.")
    
    updated_options = {}
    for subject, current_list in config["dropdown_options"].items():
        clean_list = [x for x in current_list if x != "선택 안 함"]
        input_val = st.text_area(f"■ {subject} 과목 선택 목록", value=", ".join(clean_list), help="항목을 쉼표로 구분해 주세요.")
        parsed_list = ["선택 안 함"] + [x.strip() for x in input_val.split(",") if x.strip()]
        updated_options[subject] = parsed_list
        
    if st.button("학습내용 목록 저장하기"):
        config["dropdown_options"] = updated_options
        st.session_state.app_config = config
        save_file_to_dropbox(config, CONFIG_FILE_PATH, is_csv=False)
        st.success("드롭다운 학습 내용 목록이 저장되었습니다!")
