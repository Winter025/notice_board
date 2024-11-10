from flask import Flask, render_template, request, redirect, session, url_for, send_file
import pymysql
from werkzeug.utils import secure_filename



app = Flask(__name__, template_folder='templates')
app.secret_key = 'supersecretkey'


db = pymysql.connect(host="localhost", user="root", passwd="6527", db="notice_db", charset="utf8")
cur = db.cursor()




@app.route('/')
def index():
    cur.execute("SELECT * from board")
    dataList = cur.fetchall()
    
    print('session: ', session)

    if "username" in session:
        cur.execute("SELECT * from userInfo WHERE username = %s", (session['username']))
        user = cur.fetchall()
        return render_template('index.html', data_list=dataList, userInfo=user)
    
    return render_template('index.html', data_list=dataList, userInfo='0')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_login = request.form['username']
        password_login = request.form['password']

        cur.execute("SELECT * from userInfo WHERE username = %s AND password = %s", (username_login, password_login))
        user = cur.fetchone()
        
        if user:
            session['username'] = username_login
            return redirect('/')

    return render_template('login.html')
    



@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        username = request.form['username_signup']
        password = request.form['password_signup']
        name = request.form['name']
        birth = request.form['birth']
        phone = request.form['phone']
        school = request.form['school']

        cur.execute("INSERT INTO userInfo (username, password, name, birth, phone, school, img) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                    (username, password, name, birth, phone, school, "default_profile.jpg"))
        db.commit()
    
        return redirect('/login')
    return render_template('sign_up.html')



@app.route('/logout')
def logout():
    session.pop('username', None)

    return redirect('/')



@app.route('/find_idpw', methods=['GET', 'POST'])
def find_idpw():
    if request.method == 'POST':
        name_idpw = request.form['name_idpw']
        birth_idpw = request.form['birth_idpw']
        phone_idpw = request.form['phone_idpw']

        cur.execute("SELECT * from userInfo WHERE name = %s AND birth = %s AND phone = %s", (name_idpw, birth_idpw, phone_idpw))
        find_idpw = cur.fetchone()
        
        return render_template('find_idpw.html', data_list=find_idpw)
        
    return render_template('find_idpw.html', data_list='0')



@app.route('/context/<int:num>')
def context(num):
    cur.execute("SELECT * from board WHERE num = %s", num)
    dataList = cur.fetchone()
    
    if dataList[4] != '공개':
        return render_template('public_pw.html', data_list=dataList)
        
    if "username" in session:
        return render_template('context.html', data_list=dataList, userInfo='1')
    else:
        return render_template('context.html', data_list=dataList, userInfo='0')



@app.route('/context/private', methods=['POST'])
def public_pw():
    private_pw = request.form['private_pw']
    private_num = request.form['private_num']
    
    cur.execute("SELECT * from board WHERE num = %s", private_num)
    dataList = cur.fetchone()
    
    if dataList[5] == private_pw:
        if "username" in session:
            return render_template('context.html', data_list=dataList, userInfo='1')
        else:
            return render_template('context.html', data_list=dataList, userInfo='0')

    return render_template('public_pw.html')



@app.route('/write', methods=['GET', 'POST'])
def write():
    if request.method == 'POST':
        title = request.form['title']
        context = request.form['context']
        public = request.form['public_state']
        public_pw = request.form['public_pw']
        file = request.files['chooseFile']
    
        print(file.filename)
    
        file.save('./static/file/' + secure_filename(file.filename))
    
        cur.execute("SELECT * from board")
        data = cur.fetchall()
        
        if public == '공개':
            if len(data) == 0:
                cur.execute("INSERT INTO board (num, title, writer, context, public, file) VALUES (%s, %s, %s, %s, %s, %s)", 
                            (1, title, session['username'], context, public, file.filename))
    
            else:
                cur.execute("SELECT MAX(num) from board")
                lastNum = cur.fetchall()
                lastnum = lastNum[0][0]
                cur.execute("INSERT INTO board (num, title, writer, context, public, file) VALUES (%s, %s, %s, %s, %s, %s)", 
                        (lastnum + 1, title, session['username'], context, public, file.filename))
        else:
            if len(data) == 0:
                cur.execute("INSERT INTO board (num, title, writer, context, public, public_pw, file) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                            (1, title, session['username'], context, public, public_pw, file.filename))
    
            else:
                cur.execute("SELECT MAX(num) from board")
                lastNum = cur.fetchall()
                lastnum = lastNum[0][0]
                cur.execute("INSERT INTO board (num, title, writer, context, public, public_pw, file) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                        (lastnum + 1, title, session['username'], context, public, public_pw, file.filename))
        
        db.commit() 
    
        return redirect('/')
    return render_template('write.html')



@app.route("/download", methods = ['POST'])
def download():
    return send_file('./static/file/' + request.form['file'], download_name = request.form['file'], as_attachment=True)
 


@app.route('/context/<int:num>/delete')
def delete_notice(num):
    cur.execute("DELETE FROM board WHERE num = %s", num)
    
    cur.execute("SELECT * from board")
    data = cur.fetchall()

    if len(data) != 0:
        cur.execute("SELECT MAX(num) from board")
        lastNum = cur.fetchall()
        lastnum = lastNum[0][0]
    
        while (num <= lastnum):
            cur.execute("UPDATE board SET num = %s WHERE num = %s", (num, num + 1))
            num = num + 1
        
    db.commit()
    
    return redirect('/')



@app.route('/search')
def search():
    return render_template('search.html')



@app.route('/search/title', methods=['POST'])
def search_title():
    titleSearch = request.form.get('title_search', '')
    if titleSearch == '':
       return render_template('search_result.html')
    else:
        cur.execute("SELECT * from board WHERE title LIKE %s", ('%' + titleSearch + '%'))
        titleResult = cur.fetchall()
        return render_template('search_result.html', data_list=titleResult)



@app.route('/search/context', methods=['POST'])
def search_context():
    contextSearch = request.form.get('context_search', '')
    if contextSearch == '':
       return render_template('search_result.html')
    else:
        cur.execute("SELECT * from board WHERE context LIKE %s", ('%' + contextSearch + '%'))
        contextResult = cur.fetchall()
    
    return render_template('search_result.html', data_list=contextResult)



@app.route('/search/titleContext', methods=['POST'])
def search_titleContext():
    titleContextSearch = request.form.get('titleContext_search', '')
    if titleContextSearch == '':
       return render_template('search_result.html')
    else:
        cur.execute("SELECT * from board WHERE title LIKE %s OR context LIKE %s", 
                ('%' + titleContextSearch + '%', '%' + titleContextSearch + '%'))
        titleContext_Result = cur.fetchall()

    return render_template('search_result.html', data_list=titleContext_Result)



@app.route('/modify/<int:num1>')
def modify(num1):
    return render_template('modify.html', data_list=num1)



@app.route('/modify_data', methods=['POST'])
def modify_data():
    numModify = request.form['num_modify']
    titleModify = request.form['title_modify']
    contextModify = request.form['context_modify']
    
    if len(titleModify) != 0:
        cur.execute("UPDATE board SET title = %s WHERE num = %s", (titleModify, numModify))
        
    if len(contextModify) != 0:
        cur.execute("UPDATE board SET context = %s WHERE num = %s", (contextModify, numModify))
        
    db.commit()
    
    return redirect('/')



@app.route('/profile/<username>/')
def profile(username):
    cur.execute("SELECT * from userInfo WHERE username = %s", (username))
    userProfile = cur.fetchall()
    
    cur.execute("SELECT * from board WHERE writer = %s", (username))
    userDatalist = cur.fetchall()
    print('img: ', userProfile[0][6])
    if session['username'] == username:
        me = 1
    else:
        me = 0
    
    return render_template('profile.html', user_profile = userProfile, data_list = userDatalist, use_me = me)



@app.route('/profile_modify', methods=['GET', 'POST'])
def profile_modify():
    if request.method == 'GET':
        cur.execute("SELECT * from userInfo WHERE username = %s", (session['username']))
        userProfile = cur.fetchall()
    
        return render_template('profile_modify.html', user_profile = userProfile)
    
    password = request.form['password']
    name = request.form['name']
    birth = request.form['birth']
    phone = request.form['phone']
    school = request.form['school']
    file = request.files['chooseFile']
    
    print(file)
    
    file.save('./static/img/' + secure_filename(file.filename))

    cur.execute("UPDATE userInfo SET password = %s WHERE username = %s", (password, session['username']))
    cur.execute("UPDATE userInfo SET name = %s WHERE username = %s", (name, session['username']))
    cur.execute("UPDATE userInfo SET birth = %s WHERE username = %s", (birth, session['username']))
    cur.execute("UPDATE userInfo SET phone = %s WHERE username = %s", (phone, session['username']))
    cur.execute("UPDATE userInfo SET school = %s WHERE username = %s", (school, session['username']))
    cur.execute("UPDATE userInfo SET img = %s WHERE username = %s", (file.filename, session['username']))

    db.commit()

    return redirect(url_for('profile', username = session['username']))


    



if __name__ == '__main__':
    app.run(debug=True)