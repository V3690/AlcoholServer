class Config:
    HOST = 'yh-db.cdbf2m2icqmv.ap-northeast-2.rds.amazonaws.com'
    DATABASE = 'jieun_db'
    DB_USER = 'jieun_db_user'
    DB_PASSWORD = 'je1234db'
    SALT = 'jieun' # 비밀번호 암호화할때 사용하는 salt
    
     # JWT 관련 변수 셋팅
    JWT_SECRET_KEY = 'jieun' # JWT 토큰을 만들때 사용하는 비밀키 # 관리할 문자열 # SALT와 비슷한 역할
    JWT_ACCESS_TOKEN_EXPIRES = False # False 가아니고 만약, 60 * 60 * 24 # JWT 토큰의 유효기간 # 1일
    PROPAGATE_EXCEPTIONS = True # JWT 관련 에러를 발생시키는지 여부

    # AWS 관련 변수 셋팅
    ACCESS_KEY = 'AKIAXCSREUFFZD5MQ3NG'
    SECRET_ACCESS = '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'

    # S3 관련 변수 셋팅
    BUCKET_NAME= 'alcohol-app-jieun'
    # S3 Location
    S3_LOCATION = 'http://{}.s3.ap-northeast-2.amazonaws.com/'.format(BUCKET_NAME)

    # openai 시크릿키
    OPENAI_SECRET_KEY = "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"