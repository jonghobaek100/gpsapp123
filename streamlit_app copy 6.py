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
NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID')  # 환경 변수에서 네이버 클라이언트 ID를 불러옵니다.
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')  # 환경 변수에서 네이버 클라이언트 비밀 키를 불러옵니다.
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')  # 환경 변수에서 날씨 API 키를 불러옵니다.
WEATHER_BASE_URL = os.getenv('WEATHER_BASE_URL')  # 환경 변수에서 날씨 API 기본 URL을 불러옵니다.

# 전역 변수 선언
seoul_tz = pytz.timezone('Asia/Seoul')  # 서울 시간대를 설정합니다.
now = datetime.datetime.now(seoul_tz) - datetime.timedelta(hours=1)  # 현재 시간에서 1시간을 뺀 시간을 계산합니다. (날씨 API 데이터는 1시간 전 기준으로 제공될 가능성이 높기 때문입니다.)
base_date = now.strftime("%Y%m%d")  # 현재 날짜를 "YYYYMMDD" 형식의 문자열로 변환합니다. (날씨 API 요청에 사용)
base_time = now.strftime("%H00")  # 현재 시간을 "HH00" 형식의 문자열로 변환합니다. (날씨 API 요청에 사용, 매 시간 정각의 데이터를 요청)

# Function to get GPS coordinates from Naver API using an address
def get_gps_from_address(address):
    """
    주소를 입력받아 네이버 Geocoding API를 사용하여 GPS 좌표(위도, 경도)를 반환하는 함수입니다.

    Args:
        address (str): GPS 좌표를 얻고자 하는 주소 문자열입니다.

    Returns:
        tuple (float, float): 위도와 경도를 포함하는 튜플입니다.
                        API 호출 실패 또는 주소를 찾을 수 없는 경우 None을 반환합니다.
    """
    url = "https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode"  # 네이버 Geocoding API 엔드포인트 URL입니다.
    headers = {
        "X-NCP-APIGW-API-KEY-ID": NAVER_CLIENT_ID,  # 네이버 클라이언트 ID를 헤더에 포함합니다.
        "X-NCP-APIGW-API-KEY": NAVER_CLIENT_SECRET  # 네이버 클라이언트 비밀 키를 헤더에 포함합니다.
    }
    params = {"query": address}  # 쿼리 매개변수에 주소를 설정합니다.
    response = requests.get(url, headers=headers, params=params)  # API 요청을 보냅니다.

    if response.status_code == 200:  # 응답 상태 코드가 200 (성공)인 경우,
        result = response.json()  # JSON 형식의 응답 데이터를 파싱합니다.
        if result['meta']['totalCount'] > 0:  # 검색 결과가 있는 경우,
            lat = result['addresses'][0]['y']  # 첫 번째 결과에서 위도를 추출합니다.
            lon = result['addresses'][0]['x']  # 첫 번째 결과에서 경도를 추출합니다.
            return float(lat), float(lon)  # 위도와 경도를 float 타입으로 반환합니다.
        else:
            return None  # 검색 결과가 없는 경우 None을 반환합니다.
    else:
        st.error("Failed to get GPS coordinates from Naver API")  # API 호출 실패 시 오류 메시지를 표시합니다.
        return None  # 오류 발생 시 None을 반환합니다.

def get_weather_info(latitude, longitude):
    """
    주어진 위도 및 경도에 대한 날씨 정보를 가져오는 함수입니다.
    기상청 API를 사용하여 현재 날씨 정보를 조회하고, 필요한 데이터만 추출하여 반환합니다.

    Args:
        latitude (float): 위도
        longitude (float): 경도

    Returns:
        list: 날씨 정보가 담긴 리스트. 각 요소는 날씨 정보 딕셔너리입니다.
            예: [{'category': 'TMP', 'obsrValue': 25.0}, ...]
            API 호출 실패, 데이터 없음 등의 경우 None 반환
    """
    # 서울 시간대를 설정하여 현재 시간 가져오기
    seoul_tz = pytz.timezone('Asia/Seoul')
    # now = datetime.datetime.now(seoul_tz)  # 최근 시간일 경우, 정각~데이터 나오는 시간까지 오류 발생
    now = datetime.datetime.now(seoul_tz) - datetime.timedelta(hours=1)  # 현재시간 대비 1시간 전 날씨
    base_date = now.strftime("%Y%m%d")
    base_time = now.strftime("%H00")  # 정시에 업데이트 되므로 "HH00" 형태로 시간 설정
    nx, ny = 55, 127  # 예시 좌표로 설정 (사용자 정의 또는 계산 필요)
    params = {
        "serviceKey": WEATHER_API_KEY,  # API 키
        "numOfRows": 10,  # 가져올 데이터 수
        "pageNo": 1,  # 페이지 번호
        "dataType": "JSON",  # 데이터 타입
        "base_date": base_date,  # 발표 날짜
        "base_time": base_time,  # 발표 시간
        "nx": nx,  # 경도 (X 좌표)
        "ny": ny,  # 위도 (Y 좌표)
    }

    response = requests.get(WEATHER_BASE_URL, params=params)  # API 호출

    if response.status_code == 200:  # 성공적인 응답
        try:
            data = response.json()  # JSON 파싱
            if data.get("response").get("header").get("resultCode") == "00":  # 응답 코드 확인
                items = data.get("response").get("body").get("items").get("item")  # 데이터 추출
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
    """
    GeoPandas DataFrame의 행과 대상 좌표 사이의 거리를 계산합니다.

    Args:
        row (pd.Series): GeoPandas DataFrame의 행
        target_coordinates (tuple): (위도, 경도) 튜플 형태의 대상 좌표

    Returns:
        float: 대상 좌표와 행의 중간 지점 사이의 거리 (미터 단위)
               계산 중 오류 발생 시 None 반환
    """
    try:
        # '공간위치G' 컬럼에서 LINESTRING 좌표 문자열을 추출하고, 쉼표로 분리하여 좌표 리스트 생성
        points_str = row['공간위치G'].replace("LINESTRING (", "").replace(")", "").split(", ")
        # 좌표 문자열 리스트를 (경도, 위도) 튜플 리스트로 변환
        points = [tuple(map(float, point.split())) for point in points_str]
        # LINESTRING의 중간 지점 계산
        mid_point = points[len(points) // 2]
        # (경도, 위도)를 (위도, 경도)로 변환하여 mid_point_coordinates 생성
        mid_point_coordinates = (mid_point[1], mid_point[0])
        # 대상 좌표와 중간 지점 사이의 거리 계산 (미터 단위)
        return geodesic(target_coordinates, mid_point_coordinates).meters
    except:
        return None

# 페이지 제목 설정
def set_page_title():
    """
    Streamlit 페이지의 제목과 소개 문구를 설정하는 함수입니다.
    """
    st.markdown("""
        ## 화재 영향 시설물 분석Tool 
            1. 주소를 입력하고, "이동" 버튼을 클릭하세요.
            2. 주소지 인근 맵에서 화재위치를 클릭하고, "화재지점 입력" 버튼을 클릭하세요""")  # Markdown 형식으로 부제목과 사용 지침을 표시합니다.

# 입력 필드 설정
def set_input_fields():
    """
    주소 입력 필드와 줌 레벨 슬라이더를 설정하는 함수입니다.
    Returns:
        tuple (str, int): 입력된 주소와 선택된 줌 레벨을 반환합니다.
    """
    address = st.text_input("주소 입력 :", value="부산시 부산진구 신천대로 258")  # 주소 입력 텍스트 상자를 생성하고 기본값을 설정합니다.
    zoom_level = 15 # st.slider("최초 줌 레벨을 설정하세요:", min_value=1, max_value=20, value=15)  # 줌 레벨 선택 슬라이더를 생성하고 범위를 설정합니다.
    return address, zoom_level  # 입력된 주소와 줌 레벨을 반환합니다.

# Session state 초기화
def initialize_session_state(zoom_level):
    """
    Streamlit 세션 상태를 초기화하는 함수입니다.
    세션 상태는 Streamlit 앱의 여러 실행 간에 변수를 유지하는 데 사용됩니다.
    """
    if "map_state" not in st.session_state:  # "map_state"가 세션 상태에 없는 경우,
        st.session_state.map_state = {  # 초기 지도 상태를 설정합니다.
            "location": [35.1649865, 129.0507722],  # 초기 위치 (부산)
            "zoom_level": zoom_level,  # 초기 줌 레벨
            "address": "부산시 부산진구 신천대로 258",  # 초기 주소
        }
        st.session_state.markers = []  # 마커 저장 리스트를 초기화합니다.
        st.session_state.last_clicked = None  # 마지막 클릭된 좌표를 None으로 초기화합니다.
        st.session_state.last_clicked_text = "지도를 클릭하여 좌표를 업데이트 가능"  # 마지막 클릭된 좌표 텍스트를 초기화합니다.
        st.session_state.fire_location = st.session_state.map_state["location"]  # 화재 지점 좌표를 초기 위치로 설정합니다.
        st.session_state.map_key = "map1"
        st.session_state.address_search_performed = True

# 주소 검색 및 지도 이동 기능
def move_to_address(address, zoom_level, gps_point):
    """
    입력된 주소를 사용하여 지도를 이동하고, 관련 세션 상태를 업데이트합니다.

    Args:
        address (str): 이동할 주소
        zoom_level (int): 지도의 줌 레벨
    """
    try:
        if gps_point:
            new_latitude = gps_point[0]
            new_longitude = gps_point[1]

            st.session_state.map_state["location"] = [new_latitude, new_longitude]
            st.session_state.map_state["zoom_level"] = zoom_level
            st.session_state.map_state["address"] = address
            st.session_state.fire_location = [new_latitude, new_longitude]  # 화재 지점 업데이트
            st.session_state.last_clicked_text = (  # 텍스트 업데이트
                f"선택한 화재 지점{address}: 위도 {new_latitude:.6f}, 경도 {new_longitude:.6f}"
            )
            st.session_state.address_search_performed = False
        else:
            st.error("주소를 찾을 수 없습니다. 다시 입력해주세요.")
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")

# 화면에 지도를 생성하는 함수
def create_map(latitude, longitude, zoom):
    """
    Folium Map 객체를 생성하고, OpenStreetMap 타일 레이어를 추가하는 함수입니다.

    Args:
        latitude (float): 지도의 중심 위도
        longitude (float): 지도의 중심 경도
        zoom (int): 지도의 초기 줌 레벨

    Returns:
        folium.Map: 생성된 Folium Map 객체를 반환합니다.
    """
    m = folium.Map(location=[latitude, longitude], zoom_start=zoom, control_scale=True)  # Folium Map 객체를 생성하고 중심 위치와 줌 레벨을 설정합니다.
    folium.TileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",  # OpenStreetMap 타일 레이어 URL
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',  # 저작권 정보
    ).add_to(m)  # 생성된 Map 객체에 타일 레이어를 추가합니다.
    return m  # 생성된 Map 객체를 반환합니다.

# Streamlit에서 Folium 지도를 표시하는 함수
def display_map(m, key):
    """
    Streamlit 앱에 Folium 지도를 표시하고, 사용자의 지도 클릭 이벤트를 처리하는 함수입니다.

    Args:
        m (folium.Map): 표시할 Folium Map 객체
        key (str): Streamlit 컴포넌트 키 (세션 상태 관리에 사용)

    Returns:
        dict: 사용자가 마지막으로 클릭한 위치의 위도, 경도 정보
              None: 지도가 표시되지 않거나, 클릭이벤트가 없는 경우
    """
    return st_folium(m, width=800, height=600, returned_objects=["last_clicked"], key=key)  # Streamlit에 Folium 지도를 표시하고, 클릭된 위치 정보를 반환하도록 설정합니다.

# 클릭한 위치의 GPS 좌표를 표시하는 함수
def display_clicked_location(st_map, m):
    """
    지도를 클릭했을 때 클릭한 위치의 GPS 좌표를 Streamlit 앱에 표시하는 함수

    Args:
        st_map (dict): st_folium() 함수로부터 반환된 값. 클릭된 위치 정보 포함.
        m (folium.Map): Folium Map 객체
    Returns:
        folium.Map: 입력받은 Folium Map 객체를 그대로 반환. (혹시라도 모듈 내부에서 지도가 변경되었을 경우를 대비)
    """
    if st_map and st_map.get("last_clicked") and st_map.get("last_clicked") != st.session_state.last_clicked:
        # st_map이 None이 아니고, "last_clicked" 키를 가지고 있으며,
        # 클릭된 위치가 이전 클릭 위치와 다른 경우에만 실행
        last_clicked = st_map["last_clicked"]  # 클릭된 위치 정보를 가져옴
        st.session_state.last_clicked = last_clicked  # 세션 상태에 마지막 클릭 위치 저장
        st.session_state.last_clicked_text = (
            f"선택한 좌표 : 위도 {last_clicked['lat']:.6f}, 경도 {last_clicked['lng']:.6f}"  # 클릭된 좌표 텍스트 생성
        )
        st.session_state.fire_location = [last_clicked["lat"], last_clicked["lng"]]  # 좌표 저장
    return m

# 마지막 클릭 위치 텍스트를 표시하는 함수
def show_last_clicked_text():
    """
    세션 상태에 저장된 마지막 클릭 위치 텍스트를 Streamlit 앱에 표시하는 함수
    """
    st.write(st.session_state.last_clicked_text)  # 세션 상태의 텍스트를 표시
    pass

# 화재 지점 변경 버튼 클릭 시 실행되는 함수
def change_fire_location():
    """
    화재 지점을 변경하고 지도를 업데이트하는 함수.
    st.session_state.fire_location에 저장된 좌표를 사용하여 지도의 중심을 변경하고,
    화재 지점을 표시하는 마커를 추가합니다.
    """
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

def change_fire_location2():
    """
    화재 지점을 변경하고 지도를 업데이트하는 함수. (st.rerun() 없이 지도 객체 직접 수정)
    st.session_state.fire_location에 저장된 좌표를 사용하여 지도의 중심을 변경하고,
    화재 지점을 표시하는 마커를 추가합니다.  st.rerun()을 호출하지 않고,
    현재 세션 상태에 저장된 folium.Map 객체를 직접 수정하여 지도 상태를 변경합니다.
    """
    if st.session_state.fire_location:
        new_latitude = st.session_state.fire_location[0]
        new_longitude = st.session_state.fire_location[1]

        st.session_state.map_state["location"] = [new_latitude, new_longitude]
        m = st.session_state.map  # Get the existing map object

        # Remove existing markers
        for layer in m._children.values():
            if isinstance(layer, folium.Marker):
                m.remove_child(layer)

        # Add the new marker
        fire_icon = folium.Icon(color="red", icon="fire", prefix="fa")
        folium.Marker(
            location=[new_latitude, new_longitude], icon=fire_icon, popup="화재 지점"
        ).add_to(m)

        st.session_state.map = m  # Update the map object in session state
        # No need to rerun the entire app, the map object is updated in place
    else:
        st.warning("지도를 클릭하거나 주소를 검색하여 화재 지점을 선택해주세요.")

# Function to update the map
def update_map(new_latitude, new_longitude):
    """
    지도를 새로운 좌표로 업데이트하고, 화재 지점 마커를 추가하는 함수입니다.

    Args:
        new_latitude (float): 새로운 위도 좌표
        new_longitude (float): 새로운 경도 좌표
    """
    st.session_state.map_state["location"] = [new_latitude, new_longitude]
    m = st.session_state.map  # Get the existing map object

    # Remove existing markers
    for layer in m._children.values():
        if isinstance(layer, folium.Marker):
            m.remove_child(layer)

    # Add the new marker
    fire_icon = folium.Icon(color="red", icon="fire", prefix="fa")
    folium.Marker(
        location=[new_latitude, new_longitude], icon=fire_icon, popup="화재 지점"
    ).add_to(m)

    st.session_state.map = m  # Update the map object in session state

def main():
    """
    Streamlit 앱의 메인 함수입니다.
    이 함수는 페이지 제목 설정, 입력 필드 설정, Geocoder 초기화, 세션 상태 초기화,
    지도 생성 및 표시, 버튼 이벤트 처리 등의 주요 기능을 수행합니다.
    """
    set_page_title()  # 페이지 제목과 소개문 표시
    address, zoom_level = set_input_fields()  # 주소(부암사옥), 줌 등 초기화

    # 초기 지도 설정 또는 저장된 상태 불러오기
    if 'map' not in st.session_state:
    # 맵에 사용할 변수들을 초기화(location, 주소, marker, 마지막 클릭좌표, fire_location 등), key = map1
        initialize_session_state(zoom_level)
        m = create_map(st.session_state.map_state["location"][0], st.session_state.map_state["location"][1],
                        st.session_state.map_state["zoom_level"])
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
            st.write(address, ": ", gps_point[0], ",", gps_point[1])
            move_to_address(address, zoom_level, gps_point)


    # 마지막 클릭 위치 텍스트
    with col2:
        if st.button("화재지점변경"):
            change_fire_location2()

    # 클릭된 좌표 표기 부분
    show_last_clicked_text() # st.session_state.last_clicked_text -> 함수 호출로 변경

    # 화재지점 GPS 좌표 표기
    st_map = display_map(m, st.session_state.map_key)
    m = display_clicked_location(st_map, m)

    # Update the map
    st.session_state.map = m

if __name__ == "__main__":
    main()
