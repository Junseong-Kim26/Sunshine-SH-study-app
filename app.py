"""
수현이 학습일지 (Streamlit)
--------------------------------
- 매일 과목별로 '완료 체크 + 별점(0~5) + 학습내용(드롭다운) + 메모'를 기록합니다.
- '월별 비교' 탭에서 과목별 완료 횟수 / 평균 별점 / 월별 추이를 그래프로 봅니다.
- '학습내용 설정' 탭에서 드롭다운 항목을 직접 편집합니다.
- '학습대상자 정보' 탭에서 아이 정보를 편집합니다.
- 데이터/설정은 Dropbox에 저장됩니다.
- 토큰 등 비밀정보는 코드가 아니라 .streamlit/secrets.toml (또는 Streamlit Cloud Secrets)에서 읽어옵니다.
"""

import json
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st
import dropbox

# ----------------------------------------------------------------------
# 기본 설정 (여기만 바꾸면 과목/기본값을 조정할 수 있습니다)
# ----------------------------------------------------------------------
SUBJECTS = ["영어", "수학", "한글", "책읽기"]
DATA_COLUMNS = ["날짜", "과목", "완료", "별점", "학습내용", "메모"]

# 학습내용 드롭다운의 처음 기본값 (나중에 '학습내용 설정' 탭에서 자유롭게 바꿀 수 있어요)
DEFAULT_CONTENT = {
    "영어": ["파닉스", "단어 암기", "리딩", "듣기"],
    "수학": ["덧셈", "뺄셈", "곱셈", "연산 문제집", "수학 게임"],
    "한글": ["받아쓰기", "읽기", "일기 쓰기", "글쓰기"],
    "책읽기": ["그림책", "동화책", "과학책", "위인전"],
}
DEFAULT_PROFILE = {
    "이름": "수현이",
    "생년월일": "",
    "학년": "초등학교 2학년 (2026년 기준)",
    "관심분야": "수학 게임, 스키, 농구",
}

st.set_page_config(page_title="수현이 학습일지", page_icon="📚", layout="wide")


def _dbx_config() -> dict:
    """secrets.toml 의 [dropbox] 섹션을 안전하게 읽어옵니다."""
    try:
        return dict(st.secrets["dropbox"])
    except Exception:
        return {}


DROPBOX_FILE_PATH = _dbx_config().get("file_path", "/apps/learning_log/learning_log_v2.csv")
CONFIG_FILE_PATH = _dbx_config().get("config_path", "/apps/learning_log/config.json")


# ----------------------------------------------------------------------
# Dropbox 연결
#  - 권장: refresh_token (만료되지 않음). get_dropbox_token.py 로 발급.
#  - 임시: access_token (몇 시간 뒤 만료됨).
# ----------------------------------------------------------------------
def get_dropbox_client():
    cfg = _dbx_config()
    if cfg.get("refresh_token"):
        return dropbox.Dropbox(
            oauth2_refresh_token=cfg["refresh_token"],
            app_key=cfg.get("app_key"),
            app_secret=cfg.get("app_secret"),
        )
    if cfg.get("access_token"):
        return dropbox.Dropbox(cfg["access_token"])
    return None


# ----------------------------------------------------------------------
# 학습 데이터 불러오기 / 저장
# ----------------------------------------------------------------------
def _empty_df() -> pd.DataFrame:
    return pd.DataFrame(columns=DATA_COLUMNS)


@st.cache_data(ttl=10)
def load_data() -> pd.DataFrame:
    dbx = get_dropbox_client()
    if dbx is None:
        return _empty_df()
    try:
        _, res = dbx.files_download(DROPBOX_FILE_PATH)
        df = pd.read_csv(res.raw)
    except Exception:
        return _empty_df()

    # 누락된 열 보정 + 타입 정리 (CSV는 글자로 저장되므로 다시 형변환)
    for col in DATA_COLUMNS:
        if col not in df.columns:
            df[col] = None
    df["날짜"] = df["날짜"].astype(str)
    df["과목"] = df["과목"].astype(str)
    df["완료"] = df["완료"].astype(str).str.lower().isin(["true", "1", "1.0", "yes"])
    df["별점"] = pd.to_numeric(df["별점"], errors="coerce").fillna(0).astype(int)
    df["학습내용"] = df["학습내용"].fillna("").astype(str).replace("nan", "")
    df["메모"] = df["메모"].fillna("").astype(str).replace("nan", "")
    return df[DATA_COLUMNS]


def save_data(df: pd.DataFrame) -> bool:
    dbx = get_dropbox_client()
    if dbx is None:
        st.error("Dropbox 연결 정보가 없습니다. secrets.toml 의 [dropbox] 설정을 확인하세요.")
        return False
    try:
        csv_data = df.to_csv(index=False).encode("utf-8")
        dbx.files_upload(csv_data, DROPBOX_FILE_PATH, mode=dropbox.files.WriteMode.overwrite)
        return True
    except Exception as e:
        st.error(f"저장 중 오류가 발생했습니다: {e}")
        return False


def upsert_day(df: pd.DataFrame, day_str: str, records: list) -> pd.DataFrame:
    """해당 날짜의 기존 기록을 지우고 새 기록으로 교체합니다."""
    kept = df[df["날짜"] != day_str]
    new_rows = pd.DataFrame(records, columns=DATA_COLUMNS)
    out = pd.concat([kept, new_rows], ignore_index=True)
    return out.sort_values(["날짜", "과목"]).reset_index(drop=True)


# ----------------------------------------------------------------------
# 설정(드롭다운 항목 + 아이 정보) 불러오기 / 저장
# ----------------------------------------------------------------------
@st.cache_data(ttl=10)
def load_config() -> dict:
    cfg = {
        "content_options": {k: list(v) for k, v in DEFAULT_CONTENT.items()},
        "profile": dict(DEFAULT_PROFILE),
    }
    dbx = get_dropbox_client()
    if dbx is None:
        return cfg
    try:
        _, res = dbx.files_download(CONFIG_FILE_PATH)
        data = json.loads(res.content.decode("utf-8"))
        if isinstance(data.get("content_options"), dict):
            cfg["content_options"].update(data["content_options"])
        if isinstance(data.get("profile"), dict):
            cfg["profile"].update(data["profile"])
    except Exception:
        pass  # 설정 파일이 아직 없으면 기본값 사용
    return cfg


def save_config(cfg: dict) -> bool:
    dbx = get_dropbox_client()
    if dbx is None:
        st.error("Dropbox 연결 정보가 없습니다. secrets 설정을 확인하세요.")
        return False
    try:
        data = json.dumps(cfg, ensure_ascii=False, indent=2).encode("utf-8")
        dbx.files_upload(data, CONFIG_FILE_PATH, mode=dropbox.files.WriteMode.overwrite)
        return True
    except Exception as e:
        st.error(f"설정 저장 중 오류가 발생했습니다: {e}")
        return False


def stars_text(n: int) -> str:
    n = max(0, min(5, int(n)))
    return "★" * n + "☆" * (5 - n)


def calc_age(birth: date, today: date):
    """생년월일로 만 나이(년, 개월)를 계산합니다."""
    years = today.year - birth.year
    months = today.month - birth.month
    if today.day < birth.day:
        months -= 1
    if months < 0:
        years -= 1
        months += 12
    return years, months


# ======================================================================
# 화면
# ======================================================================
st.title("📚 수현이 학습일지")

if get_dropbox_client() is None:
    st.warning(
        "아직 Dropbox 연결 설정이 없어요. README.md 를 참고해 secrets 를 설정하면 "
        "기록이 저장됩니다. (지금은 둘러보기만 가능)",
        icon="⚠️",
    )

tab1, tab2, tab3, tab4 = st.tabs(
    ["📅 학습일지", "📊 월별 비교", "⚙️ 학습내용 설정", "🙂 학습대상자 정보"]
)

# ----------------------------------------------------------------------
# 탭 1 : 오늘의 학습 기록
# ----------------------------------------------------------------------
with tab1:
    df = load_data()
    cfg = load_config()
    content_options = cfg["content_options"]

    sel_date = st.date_input("날짜 선택", value=date.today(), format="YYYY-MM-DD")
    day_str = sel_date.strftime("%Y-%m-%d")

    existing = df[df["날짜"] == day_str].set_index("과목")
    if not existing.empty:
        st.caption(f"✅ {day_str} 기록이 이미 있어요. 아래에서 수정 후 다시 저장하면 됩니다.")

    with st.form("daily_form"):
        head = st.columns([2, 1, 3, 3, 4])
        head[0].markdown("**과목**")
        head[1].markdown("**완료**")
        head[2].markdown("**별점**")
        head[3].markdown("**학습내용**")
        head[4].markdown("**메모**")

        rows = []
        for subj in SUBJECTS:
            prev_done = bool(existing.loc[subj, "완료"]) if subj in existing.index else False
            prev_star = int(existing.loc[subj, "별점"]) if subj in existing.index else 0
            prev_content = str(existing.loc[subj, "학습내용"]) if subj in existing.index else ""
            prev_memo = str(existing.loc[subj, "메모"]) if subj in existing.index else ""

            # 드롭다운 항목: 맨 위에 빈칸(선택 안 함), 기존에 적힌 값이 목록에 없으면 살려둠
            options = [""] + list(content_options.get(subj, []))
            if prev_content and prev_content not in options:
                options.insert(1, prev_content)
            idx = options.index(prev_content) if prev_content in options else 0

            c = st.columns([2, 1, 3, 3, 4])
            c[0].markdown(f"#### {subj}")
            done = c[1].checkbox(
                "완료", value=prev_done, key=f"done_{day_str}_{subj}", label_visibility="collapsed"
            )
            star = c[2].slider(
                "별점", 0, 5, value=prev_star, key=f"star_{day_str}_{subj}",
                label_visibility="collapsed",
            )
            content = c[3].selectbox(
                "학습내용", options, index=idx, key=f"content_{day_str}_{subj}",
                label_visibility="collapsed",
            )
            memo = c[4].text_input(
                "메모", value=prev_memo, key=f"memo_{day_str}_{subj}",
                placeholder="자유 메모 (예: 5장까지)", label_visibility="collapsed",
            )
            rows.append({
                "날짜": day_str, "과목": subj, "완료": done,
                "별점": star, "학습내용": content, "메모": memo,
            })

        submitted = st.form_submit_button("💾 저장하기", type="primary", use_container_width=True)

    if submitted:
        new_df = upsert_day(df, day_str, rows)
        if save_data(new_df):
            load_data.clear()
            st.success("저장되었습니다! 잘했어요 👏")
            st.rerun()

    # 오늘 요약
    done_today = [r for r in rows if r["완료"]]
    st.divider()
    st.markdown(f"### {day_str} 요약")
    if done_today:
        cols = st.columns(len(SUBJECTS))
        for col, r in zip(cols, rows):
            mark = "✅" if r["완료"] else "⬜"
            col.markdown(f"**{mark} {r['과목']}**")
            if r["완료"]:
                col.markdown(stars_text(r["별점"]))
                label = r["학습내용"] or r["메모"]
                if label:
                    col.caption(label)
            else:
                col.markdown("—")
        st.success(f"오늘 {len(SUBJECTS)}과목 중 **{len(done_today)}과목** 완료!")
    else:
        st.info("아직 완료한 과목이 없어요. 위에서 체크하고 저장해 보세요.")

    # 📆 지난 1주일 요약 (저장된 기록 기준, 선택한 날짜부터 7일)
    st.divider()
    st.markdown("### 📆 지난 1주일 요약")
    week_dates = [(sel_date - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    wk = df[df["날짜"].isin(week_dates)]
    if wk.empty:
        st.info("최근 1주일간 저장된 기록이 없어요.")
    else:
        table = {}
        for subj in SUBJECTS:
            colvals = []
            for d in week_dates:
                cell = wk[(wk["날짜"] == d) & (wk["과목"] == subj) & (wk["완료"])]
                colvals.append(f"✅ {int(cell.iloc[0]['별점'])}★" if not cell.empty else "")
            table[subj] = colvals
        table["완료 수"] = [
            f"{int(wk[(wk['날짜'] == d) & (wk['완료'])].shape[0])}/{len(SUBJECTS)}"
            for d in week_dates
        ]
        wdf = pd.DataFrame(table, index=week_dates)
        wdf.index.name = "날짜"
        st.dataframe(wdf, use_container_width=True)

# ----------------------------------------------------------------------
# 탭 2 : 월별 비교
# ----------------------------------------------------------------------
with tab2:
    df = load_data()
    if df.empty:
        st.info("아직 기록된 데이터가 없어요. '학습일지' 탭에서 먼저 기록해 보세요!")
    else:
        df = df.copy()
        df["월"] = df["날짜"].str.slice(0, 7)
        months = sorted(df["월"].unique(), reverse=True)
        sel_month = st.selectbox("월 선택", months)
        mdf = df[df["월"] == sel_month]
        done_df = mdf[mdf["완료"]]

        # 요약 지표
        c1, c2, c3 = st.columns(3)
        c1.metric("기록한 날", f"{mdf['날짜'].nunique()}일")
        c2.metric("완료한 학습", f"{int(mdf['완료'].sum())}회")
        avg = round(done_df["별점"].mean(), 1) if not done_df.empty else 0
        c3.metric("평균 별점", f"{avg} / 5")

        st.divider()

        left, right = st.columns(2)
        with left:
            st.markdown(f"**{sel_month} 과목별 완료 횟수**")
            comp = done_df.groupby("과목").size().reindex(SUBJECTS, fill_value=0)
            st.bar_chart(comp)
        with right:
            st.markdown(f"**{sel_month} 과목별 평균 별점**")
            avg_star = done_df.groupby("과목")["별점"].mean().reindex(SUBJECTS, fill_value=0)
            st.bar_chart(avg_star)

        st.divider()
        st.markdown("**월별 추이 (완료 횟수)**")
        trend = (
            df[df["완료"]]
            .groupby(["월", "과목"])
            .size()
            .unstack(fill_value=0)
            .reindex(columns=SUBJECTS, fill_value=0)
        )
        st.bar_chart(trend)

        with st.expander(f"📄 {sel_month} 상세 기록 보기"):
            st.dataframe(mdf[DATA_COLUMNS], use_container_width=True, hide_index=True)

# ----------------------------------------------------------------------
# 탭 3 : 학습내용 설정 (드롭다운 항목 편집)
# ----------------------------------------------------------------------
with tab3:
    st.subheader("⚙️ 학습내용 설정")
    st.caption("과목마다 '학습일지'의 드롭다운에 나올 항목을 한 줄에 하나씩 적어주세요.")
    cfg = load_config()

    with st.form("content_form"):
        new_options = {}
        cols = st.columns(len(SUBJECTS))
        for col, subj in zip(cols, SUBJECTS):
            with col:
                text = "\n".join(cfg["content_options"].get(subj, []))
                edited = st.text_area(f"**{subj}**", value=text, height=200, key=f"opt_{subj}")
                new_options[subj] = [ln.strip() for ln in edited.splitlines() if ln.strip()]

        if st.form_submit_button("💾 학습내용 저장", type="primary"):
            cfg["content_options"] = new_options
            if save_config(cfg):
                load_config.clear()
                st.success("학습내용이 저장되었습니다!")
                st.rerun()

# ----------------------------------------------------------------------
# 탭 4 : 학습대상자 정보 (편집 가능)
# ----------------------------------------------------------------------
with tab4:
    st.subheader("🙂 학습대상자 정보")
    cfg = load_config()
    p = cfg["profile"]

    # 저장된 생년월일로 현재 나이 표시
    bd_str = p.get("생년월일", "")
    try:
        bd_default = datetime.strptime(bd_str, "%Y-%m-%d").date()
    except Exception:
        bd_default = date(2017, 1, 1)
    if bd_str:
        y, m = calc_age(bd_default, date.today())
        st.metric("현재 나이", f"{y}세 {m}개월")

    with st.form("profile_form"):
        name = st.text_input("이름", value=p.get("이름", ""))
        birth = st.date_input(
            "생년월일", value=bd_default,
            min_value=date(2005, 1, 1), max_value=date.today(), format="YYYY-MM-DD",
        )
        grade = st.text_input("학년", value=p.get("학년", ""))
        interest = st.text_area("관심 분야", value=p.get("관심분야", ""), height=100)

        if st.form_submit_button("💾 정보 저장", type="primary"):
            cfg["profile"] = {
                "이름": name,
                "생년월일": birth.strftime("%Y-%m-%d"),
                "학년": grade,
                "관심분야": interest,
            }
            if save_config(cfg):
                load_config.clear()
                st.success("정보가 저장되었습니다!")
                st.rerun()
