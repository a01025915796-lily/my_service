import os
import random

import pandas as pd
import requests
import streamlit as st

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="위치 랜덤 데이터 시각화", layout="wide")
st.title("위치 기반 랜덤 데이터 시각화")

try:
    locations = requests.get(f"{BACKEND_URL}/locations", timeout=5).json()
except requests.exceptions.RequestException as e:
    st.error(f"백엔드 연결 실패: {e}")
    st.stop()

st.sidebar.subheader("검색 조건")
filter_region = st.sidebar.selectbox("지역", ["전체"] + list(locations.keys()))
filter_min_score = st.sidebar.slider("최소 만족도", 1, 5, 1)
filter_keyword = st.sidebar.text_input("메모 검색")

with st.form("record_form"):
    record_name = st.text_input("이름")
    record_city = st.selectbox("지역", list(locations.keys()))
    record_score = st.slider("만족도", 1, 5, 3)
    record_memo = st.text_input("한 줄 메모")
    submitted = st.form_submit_button("기록 저장")

if submitted:
    if not record_name:
        st.warning("이름을 입력해주세요")
    else:
        try:
            res = requests.post(
                f"{BACKEND_URL}/records",
                json={
                    "user_name": record_name,
                    "region": record_city,
                    "score": record_score,
                    "memo": record_memo,
                },
                timeout=5,
            )
            if res.status_code == 201:
                st.success(f"저장 완료! (id: {res.json()['id']})")
            else:
                st.error(res.json().get("detail"))
        except requests.exceptions.RequestException:
            st.error("백엔드에 연결할 수 없습니다. 터미널 1에서 백엔드가 켜져 있는지 확인하세요.")

st.subheader("전체 현황")
try:
    stats_res = requests.get(f"{BACKEND_URL}/stats", timeout=5).json()
    s_col1, s_col2, s_col3 = st.columns(3)
    s_col1.metric("총 기록 수", stats_res["total"])
    s_col2.metric("참여자 수", stats_res["user_count"])
    s_col3.metric("전체 평균 만족도", stats_res["overall_avg"])

    if stats_res["by_region"]:
        region_df = pd.DataFrame(stats_res["by_region"]).set_index("region")
        st.bar_chart(region_df["avg_score"])
except requests.exceptions.RequestException:
    st.error("백엔드에 연결할 수 없습니다. 터미널 1에서 백엔드가 켜져 있는지 확인하세요.")

st.subheader("내 기록 조회")
lookup_name = st.text_input("조회할 이름")

if st.button("내 기록 보기"):
    if not lookup_name:
        st.warning("이름을 입력해주세요")
    else:
        try:
            user_res = requests.get(
                f"{BACKEND_URL}/records/user/{lookup_name}", timeout=5
            ).json()
            st.session_state["lookup_user_name"] = lookup_name
            st.session_state["lookup_result"] = user_res
            if user_res["count"] == 0:
                st.info(f"'{lookup_name}' 이름으로 남긴 기록이 없습니다.")
        except requests.exceptions.RequestException:
            st.error("백엔드에 연결할 수 없습니다. 터미널 1에서 백엔드가 켜져 있는지 확인하세요.")

user_res = st.session_state.get("lookup_result")
if user_res and user_res["count"] > 0:
    m_col1, m_col2 = st.columns(2)
    m_col1.metric("내 기록 수", user_res["count"])
    m_col2.metric("평균 만족도", user_res["avg_score"])
    st.dataframe(pd.DataFrame(user_res["records"]))

    delete_options = {
        f"{r['id']} · {r['region']} · {r['score']} · {r['memo']}": r["id"]
        for r in user_res["records"]
    }
    delete_label = st.selectbox("삭제할 기록 선택", list(delete_options.keys()))
    if st.button("선택한 기록 삭제"):
        target_id = delete_options[delete_label]
        try:
            del_res = requests.delete(
                f"{BACKEND_URL}/records/{target_id}", timeout=5
            )
            if del_res.status_code == 200:
                st.success("삭제했습니다")
                refreshed = requests.get(
                    f"{BACKEND_URL}/records/user/{st.session_state['lookup_user_name']}",
                    timeout=5,
                ).json()
                st.session_state["lookup_result"] = refreshed
                st.rerun()
            else:
                st.error(del_res.json().get("detail"))
        except requests.exceptions.RequestException:
            st.error("백엔드에 연결할 수 없습니다. 터미널 1에서 백엔드가 켜져 있는지 확인하세요.")

st.subheader("전체 기록")
try:
    filter_params = {}
    if filter_region != "전체":
        filter_params["region"] = filter_region
    if filter_min_score > 1:
        filter_params["min_score"] = filter_min_score
    if filter_keyword:
        filter_params["keyword"] = filter_keyword

    records_res = requests.get(
        f"{BACKEND_URL}/records", params=filter_params, timeout=5
    ).json()
    st.sidebar.markdown(f"조건에 맞는 기록: {records_res['count']}건")
    if records_res["count"] == 0:
        if filter_params:
            st.warning("조건에 맞는 기록이 없습니다. 조건을 완화해보세요.")
        else:
            st.info("아직 기록이 없습니다. 위에서 첫 기록을 남겨보세요.")
    else:
        st.dataframe(pd.DataFrame(records_res["records"]))
except requests.exceptions.RequestException:
    st.error("백엔드에 연결할 수 없습니다. 터미널 1에서 백엔드가 켜져 있는지 확인하세요.")

city = st.selectbox("지역 선택", list(locations.keys()))
n_points = st.slider("랜덤 포인트 개수", 10, 200, 50)

center = locations[city]

random.seed()
df = pd.DataFrame(
    {
        "lat": [center["lat"] + random.uniform(-0.02, 0.02) for _ in range(n_points)],
        "lon": [center["lon"] + random.uniform(-0.02, 0.02) for _ in range(n_points)],
        "value": [random.randint(1, 100) for _ in range(n_points)],
    }
)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"{city} 지도")
    st.map(df, latitude="lat", longitude="lon", size="value")

with col2:
    st.subheader("값 분포")
    st.bar_chart(df["value"])

st.subheader("원본 데이터")
st.dataframe(df)
