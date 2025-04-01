import streamlit as st
import folium
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium, folium_static  # folium_static 추가
import time

# 페이지 제목 설정
st.title("주소로 지도 이동 및 GPS 좌표 표시")

# 입력 필드: 주소 입력
address = st.text_input("주소를 입력하세요:", value="부산시 부산진구 신천대로 258")

# 입력 필드: 지도 초기 Zoom 레벨 설정
zoom_level = st.slider("최초 줌 레벨을 설정하세요:", min_value=1, max_value=20, value=15)

# Geocoder 초기화
geolocator = Nominatim(user_agent="address_to_map", timeout=10)

# Session state 초기화
if "map_state" not in st.session_state:
    st.session_state.map_state = {
        "location": [37.55, 126.98],  # 초기 위치 (서울)
        "zoom_level": zoom_level,
        "address": "서울",
    }
    st.session_state.last_clicked = None
    st.session_state.markers = []  # 마커 저장 리스트 초기화
    st.session_state.map = None  # Folium Map 객체 저장


# 주소 검색 및 지도 이동 기능
def move_to_address():
    global st_data
    try:
        st.write(f"입력 주소: {address}")
        location = geolocator.geocode(address)
        if location:
            st.write(f"Geocode 결과: {location}")
            st.session_state.map_state["location"] = [
                location.latitude,
                location.longitude,
            ]
            st.session_state.map_state["zoom_level"] = zoom_level
            st.session_state.map_state["address"] = address
            m = folium.Map(
                location=[location.latitude, location.longitude],
                zoom_start=zoom_level,
            )
            # 기존 마커 모두 제거
            for marker_tuple in st.session_state.markers:  # 튜플로 저장된 마커와 팝업 사용
                marker_tuple[0].remove_from(m)
            st.session_state.markers = []

            folium.Marker([location.latitude, location.longitude], popup=address).add_to(
                m
            )
            st_data = st_folium(m, width=800, height=600, returned_objects=["last_clicked"], key="address_search_map")  # key 추가
        else:
            st.error("주소를 찾을 수 없습니다. 다시 입력해주세요.")
            st_data = None
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
        st.error(f"오류 내용: {e}")
        st_data = None


if st.button("주소로 이동"):
    move_to_address()

# 초기 지도 설정 또는 저장된 상태 불러오기
m = folium.Map(
    location=st.session_state.map_state["location"],
    zoom_start=st.session_state.map_state["zoom_level"],
)
st.session_state.map = m  # 맵 객체 저장

folium.Marker(
    st.session_state.map_state["location"], popup=st.session_state.map_state["address"]
).add_to(m)
st_data = st_folium(m, width=800, height=600, returned_objects=["last_clicked"], key="initial_map")  # key 추가


# 클릭한 위치의 GPS 좌표 표시
if st_data and st_data.get("last_clicked"):
    last_clicked = st_data["last_clicked"]
    st.write(
        f"클릭한 위치의 GPS 좌표: 위도 {last_clicked['lat']:.6f}, 경도 {last_clicked['lng']:.6f}"
    )
    # 불꽃 아이콘 추가
    fire_icon = folium.Icon(
        color="red", icon="fire", prefix="fa"
    )  # Font Awesome 아이콘 사용
    # 팝업 텍스트에 좌표 추가
    popup_text = f"클릭 위치: 위도 {last_clicked['lat']:.6f}, 경도 {last_clicked['lng']:.6f}"
    marker = folium.Marker(
        location=[last_clicked["lat"], last_clicked["lng"]], icon=fire_icon, popup=popup_text
    )
    marker.add_to(m)
    st.session_state.markers.append((marker, popup_text))  # 마커와 팝업 텍스트를 튜플로 저장
    st_folium(m, width=800, height=600, returned_objects=["last_clicked"], key="update_map")  # key 추가
else:
    st.write("지도를 클릭하여 GPS 좌표를 확인하세요.")
