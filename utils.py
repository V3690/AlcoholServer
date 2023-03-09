# 비밀번호 암호화 관련 파일임
from passlib.hash import pbkdf2_sha256

from config import Config 

# 원문 비밀번호를, 단방향 암호화 하는 함수
def hash_password(original_password): 
     # salt는 랜덤한 문자열 # 해킹이 어렵도록 ## 반드시 config에 분리저장
    password = original_password + Config.SALT # 원문 비밀번호에 salt를 붙여서 암호화
    password = pbkdf2_sha256.hash(password) # 암호화된 비밀번호를 리턴
    return password

# 유저가 로그인 할때, 입력한 비밀번호와, DB에 저장된 비밀번호를 비교하는 함수
def check_password(original_password, hashed_password): # 원문 비밀번호, 암호화된 비밀번호
    # 위에서 사용한 salt 와 똑같은 문자열
    password = original_password + Config.SALT
    check = pbkdf2_sha256.verify(password, hashed_password)
    return check # True or False
    # verify가 뭐야? -> 원문 비밀번호와, 암호화된 비밀번호를 비교해주는 함수
