import streamlit as st
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import st_folium

# 전역 변수
FIRE_LOCATION = [37.5665, 126.9780]  # 초기 서울 시청 좌표

# 모듈 1: 주소를 받아 GPS 좌표로 변환하여 FIRE_LOCATION에 저장
def get_gps_from_address(address):
    """
    주소를 GPS 좌표로 변환합니다.

    Args:
        address (str): 변환할 주소입니다.

    Returns:
        bool: 성공 여부를 반환합니다.
    """
    geolocator = Nominatim(user_agent="geocoding_service")
    try:
        location = geolocator.geocode(address)
        if location:
            st.session_state['FIRE_LOCATION'] = [location.latitude, location.longitude]
            st.success(f"'{address}'의 GPS 좌표: {st.session_state['FIRE_LOCATION']}")
            return True
        else:
            st.error(f"'{address}'에 대한 GPS 좌표를 찾을 수 없습니다.")
            return False
    except Exception as e:
        st.error(f"주소 변환 중 오류가 발생했습니다: {e}")
        return False

# 모듈 2: GPS 좌표를 받아 지도에 표기하는 함수
def display_map(location, key_name, marker_name="FIRE", update_on_click=False):
    """
    GPS 좌표를 지도에 표시합니다.

    Args:
        location (list): GPS 좌표 [위도, 경도]입니다.
        key_name (str): folium.Map에 부여할 key 값
        marker_name (str, optional): 마커 이름입니다. 기본값은 "FIRE"입니다.
        update_on_click (bool, optional): 지도를 클릭하여 좌표를 업데이트할지 여부입니다. 기본값은 False입니다.
    """
    m = folium.Map(location=location, zoom_start=15)
    folium.Marker(location, icon=folium.Icon(color='red', icon='fire')).add_to(m)
    if update_on_click:
        clicked = st_folium(m, key=key_name, height=500, width=700)
        if clicked and clicked.get("last_clicked"):
            latitude = clicked["last_clicked"]["lat"]
            longitude = clicked["last_clicked"]["lng"]
            st.session_state['FIRE_LOCATION'] = [latitude, longitude]
            st.info(f"화재 지점이 새로운 좌표로 설정되었습니다: {st.session_state['FIRE_LOCATION']}")
            #st.experimental_rerun()  # Update the map after the click
            return [latitude, longitude] #클릭한 좌표 반환
        else:
            return location # 클릭 안했으면 기존 좌표 반환
    else:
        st_folium(m, key=key_name, height=500, width=700)  # height, width 지정
        return location

# 모듈 3: 지도 클릭 시 해당 GPS 좌표를 FIRE_LOCATION에 저장
# def update_fire_location_on_click():  # 더 이상 필요하지 않습니다.
#     """
#     지도 클릭 시 해당 GPS 좌표를 FIRE_LOCATION에 저장하고, 지도에 표시합니다.
#     """
#     m = folium.Map(location=st.session_state['FIRE_LOCATION'], zoom_start=15)
#     clicked = st_folium(m, key="clickable_map", height=500, width=700) # height, width 지정
#     if clicked and clicked.get("last_clicked"):
#         latitude = clicked["last_clicked"]["lat"]
#         longitude = clicked["last_clicked"]["lng"]
#         st.session_state['FIRE_LOCATION'] = [latitude, longitude]
#         st.info(f"화재 지점이 새로운 좌표로 설정되었습니다: {st.session_state['FIRE_LOCATION']}")
#         display_map(st.session_state['FIRE_LOCATION'], "updated_fire_map")  # 화재 지점 변경 후 지도 업데이트

# Streamlit 앱 메인
def main():
    """
    Streamlit 앱의 메인 함수입니다.
    """
    st.title("화재 지점 시각화 프로그램")

    # 세션 상태 초기화
    if 'FIRE_LOCATION' not in st.session_state:
        st.session_state['FIRE_LOCATION'] = FIRE_LOCATION

    #st.subheader("초기 지도 (서울)")
    #display_map(FIRE_LOCATION, "initial_map")

    st.subheader("화재 지점 설정")
    address_input = st.text_input("주소를 입력하세요:")
    if st.button("주소로 화재 지점 설정"):
        if address_input:
            if get_gps_from_address(address_input):
                #display_map(st.session_state['FIRE_LOCATION'], "address_fire_map")  # 주소 설정 후 지도 업데이트
                new_location = display_map(st.session_state['FIRE_LOCATION'], "address_fire_map", update_on_click=True)
                st.session_state['FIRE_LOCATION'] = new_location
    else: #주소입력 안하고 버튼 누른경우
        new_location = display_map(st.session_state['FIRE_LOCATION'], "address_fire_map", update_on_click=True)
        if new_location != st.session_state['FIRE_LOCATION']: #좌표가 변경되었으면
            st.session_state['FIRE_LOCATION'] = new_location

 #   st.subheader("현재 화재 지점")
 #   display_map(st.session_state['FIRE_LOCATION'], "current_fire_map")

if __name__ == "__main__":
    main()
