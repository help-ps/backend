import google.generativeai as genai
from PIL import Image
import jellyfish
import json
import os


def Circle2Search(path:str):
    '''
    image.png 파일에 있는 문제를 어떠한 알고리즘으로 풀 수 있을지.\n
    매계변수 : 이미지 파일 위치 , 반환값 : str
    '''
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-2.5-flash-lite')

    prompt = """
        이 이미지의 있는 문제를 어떠한 알고리즘으로 풀 수 있을까?
        설명없이 아래 답변 예시처럼 답변해줘
        답변 예1) 다익스트라 알고리즘
    """

    try:
        img = Image.open(path)
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


def tag_Search(query, n=5):
    """
    query: 검색어, 반환 갯수\n
    n : 반환 갯수(기본값 5)\n
    return: 길이 n의 단어 리스트
    """
    
    query_lower = query.lower()
    
    tag_score = []

    with open('tag.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    for key in data.keys():
        word_list = data[key].split()
        scores = []
        for word in word_list: # 모든 단어에 대해
            item_lower = word.lower()
            
            # Damerau-Levenshtein 거리 계산
            distance = jellyfish.damerau_levenshtein_distance(query_lower, item_lower)
            scores.append((distance, key))

        scores.sort(key=lambda x: x[0]) 
        tag_score.append(scores[0]) # 가장 좋은 점수만 추가

    tag_score.sort(key=lambda x: x[0])
    

    for i in range(n):
        tag_score[i] = tag_score[i][1]
    return tag_score[:n]

