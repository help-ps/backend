import google.generativeai as genai
from PIL import Image
import os

def Circle2Search():
    '''
    image.png 파일에 있는 문제를 어떠한 알고리즘으로 풀 수 있을지.\n
    매계변수 : 없음 , 반환값 : str
    '''
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-2.5-flash-lite')

    prompt = """
        이 이미지의 있는 문제를 어떠한 알고리즘으로 풀 수 있을까?
        설명없이 아래 답변 예시처럼 답변해줘
        답변 예1) 다익스트라 알고리즘
    """

    try:
        img = Image.open('image.png')
    except FileNotFoundError:
        return "파일을 찾을 수 없습니다."

    try:
        response = model.generate_content(
            [prompt, img],
            stream=False
        )
        return response.text
    except Exception as e:
        return f"API 요청 중 오류 발생: {e}"
