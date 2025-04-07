import streamlit as st
import folium
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium
import json
from streamlit.components.v1 import html

# 페이지 제목 설정
def set_page_title():
    st.title("화재 영향 시설물 분석 Tool")

# 입력 필드 설정
def set_input_fields():
    address = st.text_input("주소를 입력하세요:", value="부산시 부산진구 신천대로 258")
    zoom_level = 15 # st.slider("최초 줌 레벨을 설정하세요:", min_value=1, max_value=20, value=15)
    return address, zoom_level

# Geocoder 초기화
def initialize_geocoder():
    return Nominatim(user_agent="address_to_map", timeout=10)

# Session state 초기화
def initialize_session_state(zoom_level):
    if "map_state" not in st.session_state:
        st.session_state.map_state = {
            "location": [35.147635, 129.047341],  # 초기 위치 (부산)
            "zoom_level": zoom_level,
            "address": "부산 부암동",
        }
        st.session_state.markers = []  # 마커 저장 리스트 초기화
        st.session_state.last_clicked = None
        st.session_state.last_clicked_text = "지도를 클릭하여 화재 지점을 선택하세요."
        st.session_state.fire_location = None  # 화재 지점 좌표 저장
        st.session_state.map_key = "folium_map_1"
        st.session_state.address_search_performed = False

# 주소 검색 및 지도 이동 기능
def move_to_address(address, zoom_level, geolocator):
    try:
        location = geolocator.geocode(address)
        if location:
            new_latitude = location.latitude
            new_longitude = location.longitude

            st.session_state.map_state["location"] = [new_latitude, new_longitude]
            st.session_state.map_state["zoom_level"] = zoom_level
            st.session_state.map_state["address"] = address
            st.session_state.fire_location = [new_latitude, new_longitude]  # 화재 지점 업데이트
            st.session_state.last_clicked_text = (  # 텍스트 업데이트
                f"선택한 화재 지점: 위도 {new_latitude:.6f}, 경도 {new_longitude:.6f}"
            )
            st.session_state.address_search_performed = True
        else:
            st.error("주소를 찾을 수 없습니다. 다시 입력해주세요.")
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")

# 지도 생성 함수
def create_map(latitude, longitude, zoom):
    m = folium.Map(location=[latitude, longitude], zoom_start=zoom, control_scale=True)
    folium.TileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    ).add_to(m)
    return m

# Streamlit에서 Folium 지도를 표시하는 함수
def display_map(m, key):
    return st_folium(m, width=800, height=600, returned_objects=["last_clicked"], key=key)

# 클릭한 위치의 GPS 좌표를 표시하는 함수
def display_clicked_location(st_map, m):
    if st_map and st_map.get("last_clicked") and st_map.get("last_clicked") != st.session_state.last_clicked:
        last_clicked = st_map["last_clicked"]
        st.session_state.last_clicked = last_clicked
        st.session_state.last_clicked_text = (
            f"선택한 화재 지점: 위도 {last_clicked['lat']:.6f}, 경도 {last_clicked['lng']:.6f}"
        )
        st.session_state.fire_location = [last_clicked["lat"], last_clicked["lng"]]  # 좌표 저장
    return m

# 마지막 클릭 위치 텍스트를 표시하는 함수
def show_last_clicked_text():
    #st.write(st.session_state.last_clicked_text) ->  html로 옮김
    pass

# 화재 지점 변경 버튼 클릭 시 실행되는 함수
def change_fire_location():
    if st.session_state.fire_location:
        new_latitude = st.session_state.fire_location[0]
        new_longitude = st.session_state.fire_location[1]

        st.session_state.map_state["location"] = [new_latitude, new_longitude]
        m = create_map(new_latitude, new_longitude, st.session_state.map_state["zoom_level"])
        st.session_state.map = m
        st.session_state.markers = []

        # Add fire icon marker
        fire_icon = folium.Icon(color="red", icon="fire", prefix="fa")
        folium.Marker(
            location=[new_latitude, new_longitude], icon=fire_icon, popup="화재 지점"
        ).add_to(st.session_state.map)
        st.rerun()
    else:
        st.warning("지도를 클릭하거나 주소를 검색하여 화재 지점을 선택해주세요.")


def main():
    set_page_title()
    address, zoom_level = set_input_fields()
    geolocator = initialize_geocoder()
    initialize_session_state(zoom_level)

    if st.button("주소로 이동"):
        move_to_address(address, zoom_level, geolocator)

    # 초기 지도 설정 또는 저장된 상태 불러오기
    if 'map' not in st.session_state:
        m = create_map(st.session_state.map_state["location"][0], st.session_state.map_state["location"][1], st.session_state.map_state["zoom_level"])
        st.session_state.map = m
    else:
        m = st.session_state.map

    # Use columns to position the button and text
    col1, col2 = st.columns([3, 1])  # Adjust the ratio as needed

    # 화재지점 변경 버튼
    with col1:
        st.button("화재지점 변경", on_click=change_fire_location)

    # 마지막 클릭 위치 텍스트
    with col2:
        html_content = f"""
            <div style="
                background-color: #f0f0f0;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 10px;
                font-size: 14px;
                color: #333;
                text-align: center;
                border: 1px solid #ccc;
            ">
                {st.session_state.last_clicked_text}
            </div>
        """
        html(html_content)


    st_map = display_map(m, st.session_state.map_key)
    m = display_clicked_location(st_map, m)


    # Update the map
    st.session_state.map = m

if __name__ == "__main__":
    main()
