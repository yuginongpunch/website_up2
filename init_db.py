import pymysql

def get_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='0000',
        db='spaceletter',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id VARCHAR(50) PRIMARY KEY,
            password VARCHAR(256) NOT NULL,
            nickname VARCHAR(50) NOT NULL,
            school VARCHAR(100),
            bio VARCHAR(255),
            profile_img VARCHAR(255)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            m_id INT AUTO_INCREMENT PRIMARY KEY,
            m_pw VARCHAR(256),
            user_id VARCHAR(50) NOT NULL,
            title VARCHAR(100) NOT NULL,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            file_name VARCHAR(255),    
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    conn.commit()
    conn.close()
    print('테이블 생성 완료')
