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
            latitude, longitude = location.latitude, location.longitude
            st.session_state['FIRE_LOCATION'] = [latitude, longitude]
            st.success(f"'{address}'의 GPS 좌표: {latitude:.6f}, {longitude:.6f}")
            return True
        else:
            st.error(f"'{address}'에 대한 GPS 좌표를 찾을 수 없습니다.")
            return False
    except Exception as e:
        st.error(f"주소 변환 중 오류가 발생했습니다: {e}")
        return False

# 모듈 2: GPS 좌표를 받아 지도에 표기하는 함수
def display_map(location, key_name, marker_name="FIRE"):
    """
    GPS 좌표를 지도에 표시합니다.

    Args:
        location (list): GPS 좌표 [위도, 경도]입니다.
        key_name (str): folium.Map에 부여할 key 값
        marker_name (str, optional): 마커 이름입니다. 기본값은 "FIRE"입니다.
    """
    m = folium.Map(location=location, zoom_start=15)
    folium.Marker(location, icon=folium.Icon(color='red', icon='fire')).add_to(m)
    return m

# 모듈 3: 지도 클릭 시 해당 GPS 좌표를 FIRE_LOCATION에 저장
# def update_fire_location_on_click():  # 더 이상 필요하지 않습니다.
#      """
#      지도 클릭 시 해당 GPS 좌표를 FIRE_LOCATION에 저장하고, 지도에 표시합니다.
#      """
#      m = folium.Map(location=st.session_state['FIRE_LOCATION'], zoom_start=15)
#      clicked = st_folium(m, key="clickable_map", height=500, width=700) # height, width 지정
#      if clicked and clicked.get("last_clicked"):
#          latitude = clicked["last_clicked"]["lat"]
#          longitude = clicked["last_clicked"]["lng"]
#          st.session_state['FIRE_LOCATION'] = [latitude, longitude]
#          st.info(f"화재 지점이 새로운 좌표로 설정되었습니다: {latitude:.6f}, {longitude:.6f}")
#          display_map(st.session_state['FIRE_LOCATION'], "updated_fire_map")  # 화재 지점 변경 후 지도 업데이트

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
    #fire_map = display_map(FIRE_LOCATION, "initial_map")

    st.subheader("화재 지점 설정")
    address_input = st.text_input("주소를 입력하세요:")
    map_key = "fire_map"  # 지도의 key 값을 변수에 저장
    fire_map = display_map(st.session_state['FIRE_LOCATION'], map_key) # display_map 호출
    

    if st.button("주소로 화재 지점 설정"): # 주소로 화재지점 설정 버튼 클릭 시
        if address_input:
            if get_gps_from_address(address_input):
                #display_map(st.session_state['FIRE_LOCATION'], "address_fire_map")  # 주소 설정 후 지도 업데이트
                #new_location = display_map(st.session_state['FIRE_LOCATION'], "address_fire_map", update_on_click=True)
                #st.session_state['FIRE_LOCATION'] = new_location
                fire_map = display_map(st.session_state['FIRE_LOCATION'], map_key) # display_map 재호출

    clicked = st_folium(fire_map, key=map_key, height=500, width=700) # 클릭이벤트 처리
    if clicked and clicked.get("last_clicked"):
        latitude = clicked["last_clicked"]["lat"]
        longitude = clicked["last_clicked"]["lng"]
        st.session_state['FIRE_LOCATION'] = [latitude, longitude]
        st.info(f"화재 지점이 새로운 좌표로 설정되었습니다: {latitude:.6f}, {longitude:.6f}")
        #fire_map = display_map(st.session_state['FIRE_LOCATION'], map_key)  # 화재 지점 변경 후 지도 업데이트 # 불필요한 호출 제거

    if st.button("화재 지점 설정 완료"):
        fire_map = display_map(st.session_state['FIRE_LOCATION'], map_key)
        st_folium(fire_map, key=map_key, height=500, width=700)

    st.subheader("현재 화재 지점")
    st_folium(fire_map, key="current_fire_map_display", height=500, width=700)
    st.write(f"현재 화재 지점 좌표: {st.session_state['FIRE_LOCATION'][0]:.6f}, {st.session_state['FIRE_LOCATION'][1]:.6f}")
    

if __name__ == "__main__":
    main()
