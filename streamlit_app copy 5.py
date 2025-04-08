import streamlit as st
import folium
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium
import json
from streamlit.components.v1 import html
import os
from dotenv import load_dotenv
import datetime
import pytz  
import pandas as pd
import requests
from geopy.distance import geodesic
from folium import PolyLine

# .env 파일 로드
load_dotenv()

# API 키 및 URL 설정
NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
WEATHER_BASE_URL = os.getenv('WEATHER_BASE_URL')

#전역변수 선언
seoul_tz = pytz.timezone('Asia/Seoul')
now = datetime.datetime.now(seoul_tz) - datetime.timedelta(hours=1)  # 현재시간 대비 1시간 전 날씨
base_date = now.strftime("%Y%m%d")
base_time = now.strftime("%H00")  # 정시에 업데이트 되므로 "HH00" 형태로 시간 설정

# Function to get GPS coordinates from Naver API using an address
def get_gps_from_address(address):
    url = "https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode"
    headers = {
        "X-NCP-APIGW-API-KEY-ID": NAVER_CLIENT_ID,
        "X-NCP-APIGW-API-KEY": NAVER_CLIENT_SECRET
    }
    params = {"query": address}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        result = response.json()
        if result['meta']['totalCount'] > 0:
            lat = result['addresses'][0]['y']
            lon = result['addresses'][0]['x']
            return float(lat), float(lon)
        else:
            return None
    else:
        st.error("Failed to get GPS coordinates from Naver API")
        return None

def get_weather_info(latitude, longitude):
    # 서울 시간대를 설정하여 현재 시간 가져오기
    seoul_tz = pytz.timezone('Asia/Seoul')
    # now = datetime.datetime.now(seoul_tz)  # 최근 시간일 경우, 정각~데이터 나오는 시간까지 오류 발생
    now = datetime.datetime.now(seoul_tz) - datetime.timedelta(hours=1)  # 현재시간 대비 1시간 전 날씨
    base_date = now.strftime("%Y%m%d")
    base_time = now.strftime("%H00")  # 정시에 업데이트 되므로 "HH00" 형태로 시간 설정
    nx, ny = 55, 127  # 예시 좌표로 설정 (사용자 정의 또는 계산 필요)
    params = {
        "serviceKey": WEATHER_API_KEY,
        "numOfRows": 10,
        "pageNo": 1,
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
    }
    
    response = requests.get(WEATHER_BASE_URL, params=params)
    if response.status_code == 200:
        try:
            data = response.json()
            if data.get("response").get("header").get("resultCode") == "00":
                items = data.get("response").get("body").get("items").get("item")
                return items
            else:
                st.error("데이터 조회에 실패했습니다.")
                return None
        except ValueError:
            st.error("응답에서 JSON을 파싱하는 데 실패했습니다. 응답 내용이 올바르지 않을 수 있습니다.")
            return None
    else:
        st.error(f"API 요청에 실패했습니다. 상태 코드: {response.status_code}")
        return None

# Function to calculate distance from target coordinates
def calculate_distance(row, target_coordinates):
    try:
        points_str = row['공간위치G'].replace("LINESTRING (", "").replace(")", "").split(", ")
        points = [tuple(map(float, point.split())) for point in points_str]
        mid_point = points[len(points) // 2]
        mid_point_coordinates = (mid_point[1], mid_point[0])
        return geodesic(target_coordinates, mid_point_coordinates).meters
    except:
        return None

# 페이지 제목 설정
def set_page_title():
   # st.title("화재 영향 시설물 분석Tool")
    st.markdown("""
        ## 화재 영향 시설물 분석Tool 
            1. 주소를 입력하고, "이동" 버튼을 클릭하세요.
            2. 주소지 인근 맵에서 화재위치를 클릭하고, "화재지점 입력" 버튼을 클릭하세요""")

# 입력 필드 설정
def set_input_fields():
    address = st.text_input("주소 입력 :", value="부산시 부산진구 신천대로 258")
    zoom_level = 15 #st.slider("최초 줌 레벨을 설정하세요:", min_value=1, max_value=20, value=15)
    return address, zoom_level

# Geocoder 초기화
def initialize_geocoder():
    return Nominatim(user_agent="address_to_map", timeout=10)

# Session state 초기화
def initialize_session_state(zoom_level):
    if "map_state" not in st.session_state:
        st.session_state.map_state = {
            "location": [35.1649865, 129.0507722],  # 초기 위치 (부산)
            "zoom_level": zoom_level,
            "address": "부산시 부산진구 신천대로 258",
        }
        st.session_state.markers = []  # 마커 저장 리스트 초기화
        st.session_state.last_clicked = None
        st.session_state.last_clicked_text = "지도를 클릭하여 좌표를 업데이트 가능"
        st.session_state.fire_location = st.session_state.map_state["location"]  # 화재 지점 좌표 저장
        st.session_state.map_key = "map1"
        st.session_state.address_search_performed = True

# 주소 검색 및 지도 이동 기능
def move_to_address(address, zoom_level, gps_point):
    try:
        #location = geolocator.geocode(address)
        if gps_point :
            new_latitude = gps_point[0]
            new_longitude = gps_point[1]

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

# 화면에 지도를 생성하는 함수
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
            f"선택한 좌표 : 위도 {last_clicked['lat']:.6f}, 경도 {last_clicked['lng']:.6f}"
        )
        st.session_state.fire_location = [last_clicked["lat"], last_clicked["lng"]]  # 좌표 저장
    
    return m

# 마지막 클릭 위치 텍스트를 표시하는 함수
def show_last_clicked_text():
    st.write(st.session_state.last_clicked_text) 
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
    set_page_title()  #페이지 제목과 소개문 표시
    address, zoom_level = set_input_fields()  #주소(부암사옥), 줌 등 초기화
    #geolocator = initialize_geocoder()
    #맵에 사용할 변수들을 초기화(location, 주소, marker, 마지막 클릭좌표, fire_location 등), key = map1
    initialize_session_state(zoom_level)  

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
   # Naver GPS 좌표 조회 기능으로 전환할 것!!
        if st.button("이동"):
            gps_point = get_gps_from_address(address)
            st.write(address, ": ", gps_point[0], ",",gps_point[1])
            move_to_address(address, zoom_level, gps_point)

    # 마지막 클릭 위치 텍스트
    with col2:
        st.button("화재지점 변경":
            change_fire_location()

    #클릭된 좌표 표기 부분
    st.session_state.last_clicked_text

    # 화재지점 GPS 좌표 표기
    
    st_map = display_map(m, st.session_state.map_key)
    m = display_clicked_location(st_map, m)

    # Update the map
    st.session_state.map = m

if __name__ == "__main__":
    main()
