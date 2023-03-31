import sys
import os

resource_root = os.path.dirname(os.path.abspath(__file__)) # 현재 파일의 경로
sys.path.append(resource_root) # 현재 파일의 경로를 sys.path에 추가

# 필요한 모듈 가져오기
import alcohol