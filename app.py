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

# 데이터 초기 로드 및 세션 저장
if "main_data" not in st.session_state:
    st.session_state.main_data = load_file_from_dropbox(DATA_FILE_PATH, is_csv=True)
if "app_config" not in st.session_state:
    st.session_state.app_config = load_file_from_dropbox(CONFIG_FILE_PATH, is_csv=False)

main_df = st.session_state.main_data
config = st.session_state.app_config

# 🔥 [무결성 보장 장치] 파일 구조 변경이나 데이터 누락으로 인한 KeyError 원천 차단
required_cols = ["일시", "영어", "수학", "한글", "책읽기 등", "비고"]
for col in required_cols:
    if col not in main_df.columns:
        main_df[col] = ""

if "student_info" not in config or not isinstance(config["student_info"], dict):
    config["student_info"] = {}
for k, v in {"name": "기찡", "birthdate": "2018-04-08", "grade": "초등학교 2학년", "note": "농구와 스키를 좋아함"}.items():
    if k not in config["student_info"] or not config["student_info"][k]:
        config["student_info"][k] = v

if "reward_info" not in config or not isinstance(config["reward_info"], dict):
    config["reward_info"] = {}
for k, v in {"monthly_goal": 20, "reward_desc": "주말 스키장 가기!"}.items():
    if k not in config["reward_info"]:
        config["reward_info"][k] = v

if "dropdown_options" not in config or not isinstance(config["dropdown_options"], dict):
    config["dropdown_options"] = {}
default_options = {
    "영어": ["선택 안 함", "파닉스", "동화책", "따라쓰기"],
    "수학": ["선택 안 함", "구구단", "연산", "사고력"],
    "한글": ["선택 안 함", "받아쓰기", "한글읽기"],
    "책읽기 등": ["선택 안 함", "위인전", "과학잡지"]
}
for k, v in default_options.items():
    if k not in config["dropdown_options"] or not config["dropdown_options"][k]:
        config["dropdown_options"][k] = v

st.session_state.main_data = main_df
st.session_state.app_config = config


# 3. 유틸리티 함수
def calculate_precise_age(birthdate_str):
    try:
        birth = datetime.strptime(birthdate_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        years = today.year - birth.year
        months = today.month - birth.month
        if today.day < birth.day: months -= 1
        if months < 0: years -= 1; months += 12
        return f"{years}세 {months}개월"
    except:
        return "날짜 형식 오류"

# 💡 [요구사항 반영] 주말 및 공휴일은 학습하지 않아도 무조건 달성으로 처리하는 스트릭 로직
def calculate_streak(df):
    done_dates = set()
    if not df.empty and "일시" in df.columns:
        df['is_done'] = df.apply(lambda r: any(str(r.get(c, "선택 안 함")).strip() not in ["선택 안 함", "", "None", "nan"] for c in ["영어", "수학", "한글", "책읽기 등"]), axis=1)
        for d_str in df[df['is_done']]['일시'].unique():
            try:
                done_dates.add(datetime.strptime(str(d_str)[:10], "%Y-%m-%d").date())
            except:
                pass

    today = datetime.now().date()
    streak = 0
    check_date = today
    
    for _ in range(365):
        is_weekend = check_date.weekday() in [5, 6]
        is_holiday = check_date in kr_holidays
        has_learned = check_date in done_dates
        
        if has_learned or is_weekend or is_holiday:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            # 평일이고 오늘 아직 학습 전이라면 스트릭이 끊긴 것이 아니므로 어제 날짜로 넘어가 연속성 확인
            if check_date == today:
                check_date -= timedelta(days=1)
                continue
            else:
                break
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
                    val = match.iloc[0][col] if col in match.columns else None
                    if pd.isna(val) or val is None:
                        display_df.at[idx, col] = "" if col == "비고" else "선택 안 함"
                    else:
                        display_df.at[idx, col] = str(val)

    show_cols = ["일시", "영어", "수학", "한글"]
    if show_reading: show_cols.append("책읽기 등")
    show_cols.append("비고")

    options = config["dropdown_options"]
    col_config = {
        "일시": st.column_config.TextColumn("일시", disabled=True),
        "영어": st.column_config.SelectboxColumn("영어", options=options.get("영어", ["선택 안 함"])),
        "수학": st.column_config.SelectboxColumn("수학", options=options.get("수학", ["선택 안 함"])),
        "한글": st.column_config.SelectboxColumn("한글", options=options.get("한글", ["선택 안 함"])),
        "비고": st.column_config.TextColumn("비고 (메모)")
    }
    if show_reading: col_config["책읽기 등"] = st.column_config.SelectboxColumn("책읽기 등", options=options.get("책읽기 등", ["선택 안 함"]))
    
    edited_df = st.data_editor(display_df[show_cols], use_container_width=True, column_config=col_config, key="editor_v6")
    
    if st.button("학습 내용 저장하기", type="primary"):
        for idx, row in edited_df.iterrows():
            pure_d = display_df.at[idx, "pure_date"]
            if not main_df.empty:
                main_df = main_df[main_df["일시"] != pure_d]
            
            reading_val = row["책읽기 등"] if "책읽기 등" in row else display_df.at[idx, "책읽기 등"]
            note_val = row["비고"] if "비고" in row else display_df.at[idx, "비고"]
            if pd.isna(note_val) or note_val is None: note_val = ""
                
            new_r = {
                "일시": pure_d, 
                "영어": row["영어"], 
                "수학": row["수학"], 
                "한글": row["한글"], 
                "책읽기 등": reading_val,
                "비고": note_val
            }
            main_df = pd.concat([main_df, pd.DataFrame([new_r])], ignore_index=True)
        st.session_state.main_data = main_df
        save_file_to_dropbox(main_df, DATA_FILE_PATH, is_csv=True)
        st.success("학습 일지가 안전하게 드롭박스에 동기화되었습니다!")
        st.rerun()

# 📍 2. 월별 비교 탭
with tab2:
    st.subheader("📊 학습 분석 및 보상 게이지")
    
    this_month = datetime.now().strftime("%Y-%m")
    done_days = 0
    if not main_df.empty:
        month_data = main_df[main_df['일시'].astype(str).str.contains(this_month, na=False)]
        if not month_data.empty:
            done_days = month_data.apply(lambda r: any(str(r.get(c, "선택 안 함")).strip() not in ["선택 안 함", "", "None", "nan"] for c in ["영어", "수학", "한글", "책읽기 등"]), axis=1).sum()
    
    goal = config["reward_info"].get("monthly_goal", 20)
    reward_desc = config["reward_info"].get("reward_desc", "목표를 설정해 주세요")
    progress = min(float(done_days) / float(goal), 1.0) if goal > 0 else 0.0
    
    st.write(f"### 🎁 이번 달 보상: **{reward_desc}**")
    st.progress(progress)
    st.write(f"현재 **{done_days}회** 완료! (목표: {goal}회까지 **{max(0, goal-done_days)}회** 남음)")

    # [실선 그래프 기능]
    st.markdown("#### 📈 학습 달성도 추이 (실선 그래프)")
    if not main_df.empty:
        analysis_df = main_df.copy()
        analysis_df['월'] = analysis_df['일시'].astype(str).str[:7]
        chart_data = []
        all_months = sorted([m for m in analysis_df['월'].unique() if len(str(m)) == 7])
        
        for m in all_months:
            m_df = analysis_df[analysis_df['월'] == m]
            row = {"월": m}
            for s in ["영어", "수학", "한글", "책읽기 등"]:
                row[s] = m_df[(m_df[s] != "선택 안 함") & (m_df[s].notna()) & (m_df[s] != "") & (m_df[s] != "None")].shape[0]
            chart_data.append(row)
        
        if chart_data:
            df_chart = pd.DataFrame(chart_data).set_index("월")
            st.line_chart(df_chart)
        else:
            st.info("실선 그래프 데이터가 생성 대기 중입니다. 학습 데이터를 입력해 주세요.")
    else:
        st.info("데이터가 존재하지 않아 그래프를 표시할 수 없습니다.")
        
    # [데이터 다운로드 기능]
    st.divider()
    st.markdown("#### 📥 데이터 백업 및 엑셀 다운로드")
    csv_data = main_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 전체 학습 데이터(CSV) 다운로드",
        data=csv_data,
        file_name="기찡이_학습_데이터.csv",
        mime="text/csv"
    )

# 📍 3. 정보 관리 탭
with tab3:
    st.subheader("🧑‍🎓 학습대상자 상세 정보 관리")
    info = config["student_info"]
    c1, c2 = st.columns(2)
    with c1:
        u_name = st.text_input("이름", value=info.get("name", "기찡"))
        u_birth = st.text_input("생년월일 (YYYY-MM-DD)", value=info.get("birthdate", "2018-04-08"))
    with c2:
        u_grade = st.text_input("학년", value=info.get("grade", "초등학교 2학년"))
        st.info(f"💡 현재 나이 기준 자동 계산: **{calculate_precise_age(u_birth)}**")
        
    u_note = st.text_area("특이사항", value=info.get("note", "농구와 스키를 좋아함"))
    
    if st.button("학생 정보 저장"):
        config["student_info"] = {"name": u_name, "birthdate": u_birth, "grade": u_grade, "note": u_note}
        st.session_state.app_config = config
        save_file_to_dropbox(config, CONFIG_FILE_PATH, is_csv=False)
        st.success("학생 정보가 드롭박스에 안전하게 저장되었습니다!")
        st.rerun()

# 📍 4. 학습내용 설정 탭
with tab4:
    st.subheader("⚙️ 학습내용 및 보상 목표 설정")
    col_opt, col_rew = st.columns(2)
    with col_opt:
        st.markdown("#### 📝 과목별 선택 목록 설정")
        new_opts = {}
        for s in ["영어", "수학", "한글", "책읽기 등"]:
            cur = options.get(s, ["선택 안 함"])
            val = st.text_area(f"■ {s} 목록 (쉼표 구분)", ", ".join([x for x in cur if x != "선택 안 함"]))
            new_opts[s] = ["선택 안 함"] + [x.strip() for x in val.split(",") if x.strip()]
    with col_rew:
        st.markdown("#### 🎁 동기부여 보상 설정")
        new_goal = st.number_input("월간 목표 학습 횟수", min_value=1, value=int(config["reward_info"].get("monthly_goal", 20)))
        new_desc = st.text_input("목표 달성 시 보상 내용", value=config["reward_info"].get("reward_desc", "주말 스키장 가기!"))
    
    if st.button("모든 설정 저장"):
        config["dropdown_options"] = new_opts
        config["reward_info"] = {"monthly_goal": new_goal, "reward_desc": new_desc}
        st.session_state.app_config = config
        save_file_to_dropbox(config, CONFIG_FILE_PATH, is_csv=False)
        st.success("학습 설정 목록과 보상 목표가 성공적으로 동기화되었습니다!")
        st.rerun()
