from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import send_from_directory
import pymysql
import init_db
import os


app = Flask(__name__)
app.secret_key = 'forever'



#데이터베이스 연결 함수, 매번 호출할거임.
def get_db_conn():
    return init_db.get_connection()

#기본페이지 index.html
@app.route('/')
def index():
    return render_template('index.html')

#로그인, 아이디,비번 맞는지 확인후 아이디틀림, 비밀번호 틀림 알려주기, 맞으면 로그인 성공
@app.route('/login', methods = ['POST'])
def login():
    
    id = request.form.get('user_id')
    pw = request.form.get('password')


    conn = get_db_conn()
    
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT user_id, password FROM users WHERE user_id = %s", (id,))
            user = cursor.fetchone()
    finally:
        conn.close()

    if user is None:
        return "존재하지 않은 아이디입니다"
    if check_password_hash(user['password'], pw):
        session['user_id'] = id
        return redirect(url_for('index'))
    else:
        return "비밀번호가 일치하지 않습니다"


    

#로그아웃
@app.route('/logout', methods= ['POST'])
def logout():
    session.clear()
    return render_template('index.html')

#회원가입페이지이동
@app.route('/register_page')
def register_page():
    return render_template('register.html')


#회원가입
@app.route('/register', methods = ['POST'])
def register():
    user_id = request.form.get('id')
    pw = request.form.get('password')
    nickname = request.form.get('nickname')
    school = request.form.get('school')

    
    if not user_id or not pw or not nickname:
        return render_template('register.html', error='모두 입력해주세요')
    
    
    conn = get_db_conn()
    try:
        hashed_pw = generate_password_hash(pw)
        with conn.cursor() as cursor:
            sql = "INSERT INTO users (user_id, password, nickname, school) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (user_id, hashed_pw, nickname, school))
        conn.commit()
        return render_template('index.html', success="회원가입 완료")
    
    except Exception as e:
        print(f"에러 발생: {e}")
        return render_template('register.html', error="이미 사용중인 아이디거나 형식이 맞지않아요")
    
    finally:
        conn.close()
    

#아이디로 비밀번호찾기
@app.route('/find-pw', methods = ['GET', 'POST'])
def find_pw():
    if request.method == 'POST':
        user_id = request.form['user_id']

        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return redirect(url_for('reset_pw', user_id=user_id))
        else:
            return render_template('find_pw.html', error="존재하지 않는 아이디입니다")
    
    return render_template('find_pw.html')

#비밀번호 재설정하기
@app.route('/reset-pw', methods = ['GET', 'POST'])
def reset_pw():
    user_id = request.args.get('user_id') or request.form.get('user_id')

    if request.method == 'POST':
        new_pw = request.form['new_password']
        confirm_pw = request.form['confirm_password']

        if new_pw != confirm_pw:
            return render_template('reset-pw.html', user_id=user_id, error="비밀번호가 일치하지 않아요")
        
        hashed = generate_password_hash(new_pw) 

        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET password = %s WHERE user_id = %s", (hashed, user_id)
                )
            conn.commit()
        finally:
            conn.close()
        return redirect(url_for('index'))
    return render_template('reset_pw.html', user_id=user_id)



        
#아이디 찾기 
@app.route('/find-id', methods= ['GET', 'POST'])
def find_id():
    if request.method == 'POST':
        nickname = request.form['nickname']
        school = request.form['school']

        conn = get_db_conn()
        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(
                    "SELECT user_id FROM users WHERE nickname = %s AND school = %s", (nickname,school)
                )
                result = cursor.fetchone()
        finally:
            conn.close()
        
        if result:
            found_id = result['user_id']
            return render_template('find_id.html', found_id=found_id)
        else:
            return render_template('find_id.html', error="정보가 일치하지 않아요")
    return render_template('find_id.html') 



#업로드 한 파일 저장할 폴더 uploads
upload_folder = 'uploads'
app.config['upload_folder'] = upload_folder
os.makedirs(upload_folder, exist_ok=True)

#글쓰기 페이지 연결하기
@app.route('/write')
def write_page():
    return render_template('message.html')



#게시판 메시지 쓰기 + 비밀글 기능 +파일 업로드
@app.route('/messages', methods = ['POST'])
def create_messages():
    
    user_id = session.get('user_id')
    if not user_id:
        user_id = 'Guest'

    title = request.form.get('title')
    content = request.form.get('content')
    pw = request.form.get('m_pw')
    hashed_pw = generate_password_hash(pw) if pw else None #비밀글 일때만 해시
    
    file = request.files.get('file')
    file_name = None

    if file and file.filename !='':
        file_name = secure_filename(file.filename) #안전한 파일명으로 바꾸기
        file.save(os.path.join(app.config['upload_folder'], file_name)) #서버에 저장하기


    conn = get_db_conn()
    try:
        with conn.cursor()as cursor:
            sql = "INSERT INTO messages (user_id, title, content, m_pw, file_name) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(sql, (user_id, title, content, hashed_pw, file_name))
        conn.commit()
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Error:{e}")
        return "데이터 베이스 저장 오류입니다", 500

    finally:
        conn.close()
    


#파일 다운로드
@app.route('/messages/<int:m_id>/download', methods=['GET'])
def download_file(m_id):
    conn = get_db_conn()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT file_name FROM messages WHERE m_id = %s", (m_id,))
            message = cursor.fetchone()
    finally:
        conn.close()
    
    if message is None or message['file_name'] is None:
        return jsonify({"result":"fail", "message":"파일이 존재하지 않습니다"})
    
    return send_from_directory(app.config['upload_folder'], message['file_name'], as_attachment=True )



#게시판 메시지 읽기
@app.route("/messages", methods = ['GET'])
def get_messages():
    keyword = request.args.get('keyword', '')
    search_type = request.args.get('type','all')

    conn = get_db_conn()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM messages WHERE 1=1"
            params = []
            if keyword:
                if search_type == 'title':
                    sql += " AND title LIKE %s"
                    params.append(f"%{keyword}%")
                elif search_type == 'content':
                    sql += " AND content LIKE %s"
                    params.append(f"%{keyword}%")
                else:
                    sql += " AND (title LIKE %s OR content LIKE %s)"
                    params.extend([f"%{keyword}%", f"%{keyword}%"])

            cursor.execute(sql, params)
            result = cursor.fetchall()
        return jsonify(result)
    finally:
        conn.close()


#한개씩 메시지 읽기
@app.route('/messages/<int:m_id>', methods = ['GET', 'POST'])
def view_message(m_id):
    conn = get_db_conn()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM messages WHERE m_id = %s", (m_id,))
            message = cursor.fetchone()
    finally:
        conn.close()
    if message is None:
        return "존재하지 않는 게시물이에요", 404
    #비밀글이 아닐때 그냥 보여준다
    if not message['m_pw']:
        return render_template('message_detail.html', message=message)
    #비밀글일때 비밀번호 확인하기
    if request.method == 'POST':
        pw = request.form.get('password')
        if check_password_hash(message['m_pw'], pw):
            return render_template('message_detail.html', message=message)
        else:
            return render_template('message_pw.html', m_id=m_id, error='비밀번호가 일치하지 않아요')
    return render_template('message_pw.html', m_id=m_id)




#게시판 메시지 수정하기, 비밀글이면 비밀번호 맞아야 수정가능
@app.route('/messages/<int:m_id>/update', methods = ['POST'])
def update_message(m_id):
    title = request.form.get('title')
    content = request.form.get('content')
    pw = request.form.get('password')

    conn = get_db_conn()
    

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT m_pw FROM messages WHERE m_id = %s", (m_id,))
            message = cursor.fetchone()

            if message is None:
                return jsonify({"result":"fail", "message":"존재하지 않는 게시글입니다"})
            
            if message['m_pw']:
                if not pw or not check_password_hash(message['m_pw'], pw):
                    return jsonify({"result":"fail", "message":"비밀번호가 일치하지 않아요"})
            cursor.execute(
                "UPDATE messages SET title=%s, content=%s WHERE m_id=%s",(title, content, m_id)
            )
    
        conn.commit()
        return jsonify({"result":"success", "message":"수정 완료"})

    finally:
        conn.close()


#게시판 메시지 삭제하기
@app.route('/messages/<int:m_id>', methods = ['DELETE'])
def delete_message(m_id):
    conn = get_db_conn()
    try:
        with conn.cursor() as cursor:
            sql = "DELETE FROM messages WHERE m_id=%s"
            cursor.execute(sql, (m_id,))
        conn.commit()
        return jsonify({"result":"success", "message":"삭제 완료"})
    finally:
        conn.close()





#프로필 이미지 저장 폴더
profile_folder = 'static/profiles' #static 폴더에 저장해서 html 에서 바로 보여줄수 있다
app.config['profile_folder'] = profile_folder
os.makedirs(profile_folder, exist_ok=True)




#마이페이지 프로필 보기 
@app.route('/user/<string:user_id>', methods = ['GET'])
def mypage(user_id):
    if 'user_id' not in session: #로그인 상태가 아니면 index 페이지로 가기
        return redirect(url_for('index'))
    conn = get_db_conn()
    
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT user_id, nickname, school, bio, profile_img FROM users WHERE user_id = %s", (session['user_id'],))
            user = cursor.fetchone()
    finally:
        conn.close()
    return render_template('mypage.html', user=user)


    
#다른사람 마이페이지 조회
@app.route('/users/<string:user_id>', methods=['GET'])
def user_profile(user_id):
    conn = get_db_conn()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT user_id, nickname, school, bio, profile_img FROM users WHERE user_id=%s",(user_id,))
            user = cursor.fetchone()
    finally:
        conn.close()
    if user is None:
        return jsonify({"result":"fail", "message":"존재하지 않는 유저입니다"})
    return render_template('user_profile.html', user=user)
    
    
#내 프로필 수정하기, 프로필 이미지 업로드
@app.route('/users/<string:user_id>/update', methods=['POST'])
def update_mypage(user_id):
    if 'user_id' not in session:
        return jsonify({"result":"fail", "message":"로그인이 필요합니다"})
    
    if session['user_id'] != user_id:
        return jsonify({"result":"fail", "message":"본인의 정보만 수정할 수 있어요"})
    
    nickname = request.form.get('nickname')
    bio = request.form.get('bio')
    school = request.form.get('school')
    file = request.files.get('profile_img')

    profile_img_name = None
    if file and file.filename != '':
        profile_img_name = f"{user_id}_{secure_filename(file.filename)}"
        file.save(os.path.join(app.config['profile_folder'], profile_img_name))#서버에 이미지저장

    conn = get_db_conn()
    try:
        with conn.cursor() as cursor:
            if profile_img_name:
                sql = "UPDATE users SET nickname=%s, bio=%s, school=%s, profile_img=%s WHERE user_id=%s"
                cursor.execute(sql, (nickname, bio, school, profile_img_name, user_id))

            else:
                sql = "UPDATE users SET nickname=%s, bio=%s, school=%s WHERE user_id=%s"
                cursor.execute(sql, (nickname, bio, school, user_id))
               
        conn.commit()
        return redirect(url_for('mypage', user_id=session['user_id']))
    except Exception as e:
        print(f"프로필 수정 에러:{e}")
        return "수정 중 오류가 발생했어요", 500
    finally:
        conn.close()


#수정 페이지 연결하기
@app.route('/users/<string:user_id>/edit', methods = ['GET'])
def edit_mypage(user_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_conn()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(
                "SELECT user_id, nickname, school, bio, profile_img FROM users WHERE user_id=%s",(user_id)
            )
            user = cursor.fetchone()
    finally:
        conn.close()
    return render_template('user_profile_edit.html', user=user)
   


if __name__ == '__main__':
    init_db.init_db()
    app.run(debug=True)


