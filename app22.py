# app22.py - SyntaxError (U+00A0)가 수정된 파일

def get_age_ranges():
    """
    연령대 옵션 목록을 반환하는 함수.
    이전 코드에서 발생했던 'invalid non-printable character U+00A0' 오류는
    문자열 내의 공백 문자를 일반 공백(ASCII Space)으로 교체하여 해결되었습니다.
    """
    # 주의: 이 줄들은 오류가 발생했던 라인 주변을 재구성한 것입니다.
    # 원래 코드의 전체 맥락에 따라 이 목록의 위치나 용도가 달라질 수 있습니다.
    age_ranges = [
        "만 0세~6세",
        "만 7세~12세",
        # 다음 라인이 오류가 났던 부분입니다. 공백 문자가 정상적으로 수정되었습니다.
        "만 13세~19세", "만 20세~29세", "만 30세~39세",
        "만 40세~49세",
        "만 50세 이상",
    ]
    return age_ranges

def run_app():
    """
    앱의 메인 로직을 실행하는 예제입니다.
    """
    print("--- app22.py 실행 결과 ---")
    ranges = get_age_ranges()
    print("성공적으로 로드된 연령대 목록:")
    for r in ranges:
        print(f"  - {r}")
    
    if len(ranges) > 0:
        print(f"\n목록에 총 {len(ranges)}개의 연령대가 있습니다.")

if __name__ == "__main__":
    run_app()
