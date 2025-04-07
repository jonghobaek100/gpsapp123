import streamlit as st
import folium
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium, folium_static  # folium_static은 더 이상 필요하지 않습니다.

# 페이지 제목 설정
st.title("주소로 지도 이동 및 GPS 좌표 표시")

# 입력 필드: 주소 입력
address = st.text_input("주소를 입력하세요:", value="부산시 부산진구 신천대로 258")

# 입력 필드: 지도 초기 Zoom 레벨 설정
zoom_level = st.slider("최초 줌 레벨을 설정하세요:", min_value=1, max_value=20, value=15)

# Geocoder 초기화
geolocator = Nominatim(user_agent="address_to_map", timeout=10)


# Session state 초기화
def initialize_session_state():
    if "map_state" not in st.session_state:
        st.session_state.map_state = {
            "location": [35.147635, 129.047341],  # 초기 위치 (부산)
            "zoom_level": zoom_level,
            "address": "부산 부암동",
        }
        st.session_state.markers = []  # 마커 저장 리스트 초기화
        st.session_state.last_clicked = None

initialize_session_state()

# 주소 검색 및 지도 이동 기능
def move_to_address():
    try:
        location = geolocator.geocode(address)
        if location:
            st.session_state.map_state["location"] = [
                location.latitude,
                location.longitude,
            ]
            st.session_state.map_state["zoom_level"] = zoom_level
            st.session_state.map_state["address"] = address
            # Clear existing markers
            st.session_state.markers = []
            # Create and display the map
            m = create_map(location.latitude, location.longitude, zoom_level)
            st.session_state.map = m
            st.rerun()  # Force Streamlit to re-run and update the map
        else:
            st.error("주소를 찾을 수 없습니다. 다시 입력해주세요.")
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")

def create_map(latitude, longitude, zoom):
    m = folium.Map(location=[latitude, longitude], zoom_start=zoom)
    folium.Marker(
        [latitude, longitude], popup=st.session_state.map_state["address"]
    ).add_to(m)
    return m

if st.button("주소로 이동"):
    move_to_address()

# 초기 지도 설정 또는 저장된 상태 불러오기
if 'map' not in st.session_state:
    m = create_map(st.session_state.map_state["location"][0], st.session_state.map_state["location"][1], st.session_state.map_state["zoom_level"])
    st.session_state.map = m
else:
    m = st.session_state.map

# Streamlit에서 Folium 지도를 표시합니다.
st_map = st_folium(m, width=800, height=600, returned_objects=["last_clicked"], key="folium_map")

# 클릭한 위치의 GPS 좌표 표시
if st_map.get("last_clicked"):
    last_clicked = st_map["last_clicked"]
    st.write(
        f"클릭한 위치의 GPS 좌표: 위도 {last_clicked['lat']:.6f}, 경도 {last_clicked['lng']:.6f}"
    )
    # 불꽃 아이콘 추가
    fire_icon = folium.Icon(color="red", icon="fire", prefix="fa")  # Font Awesome 아이콘 사용
    # 팝업 텍스트에 좌표 추가
    popup_text = f"클릭 위치: 위도 {last_clicked['lat']:.6f}, 경도 {last_clicked['lng']:.6f}"
    marker = folium.Marker(
        location=[last_clicked["lat"], last_clicked["lng"]], icon=fire_icon, popup=popup_text
    )
    marker.add_to(m)

    # Update the map in session state
    st.session_state.map = m
    st.rerun()

else:
    st.write("지도를 클릭하여 GPS 좌표를 확인하세요.")
