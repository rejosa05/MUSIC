from flask import Flask, render_template, request, session, redirect, url_for
from flask_mysqldb import MySQL

app = Flask(__name__)
mysql = MySQL(app)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'music'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

@app.route('/', methods=['GET', 'POST'])
def index():
	if 'username' in session:
		if session['username'] == 'admin':
			return redirect(url_for('admin'))
		else:
			return redirect(url_for('main'))
	else:
		if request.method == 'POST':
			username = request.form['username']
			password = request.form['password']

			cur = mysql.connection.cursor()
			result = cur.execute("SELECT * FROM login WHERE username = %s AND password = %s", [username, password])

			if result > 0:
				data = cur.fetchone()  
				user_id = data['user_id']

				session['username'] = username
				session['user_id'] = user_id

				if username == 'admin':
					return redirect(url_for('admin'))
				else:
					return redirect(url_for('main'))
			else:
				error = 'Username not found'
				return render_template('login.html', error=error)

		return render_template('login.html')

@app.route('/main')
def main():
	if 'username' in session:
		if session['username'] == 'admin':    
			return redirect(url_for('admin'))
		else:
			user_id = session['user_id']

			cur = mysql.connection.cursor()
			result = cur.execute("""
								SELECT
									u.f_name,
									u.m_name,
									u.l_name,
									u.email,
									u.b_day,
									l.username,
									l.`password`,
									gl.grade_level AS `grade_level`,
									s.`subject` AS subjects,
									so.title AS title,
									concat(ar.f_name, ' ', ar.l_name) AS ar_fullname,
									ar.contact_num,
									ge.`name` AS genre,
									ly.lyrics AS lyrics
								FROM
									grade_subject AS gs ,
									grade_levels AS gl ,
									subjects AS s ,
									songs AS so ,
									users AS u ,
									artists AS ar ,
									login AS l ,
									genres AS ge ,
									lyrics AS ly
								WHERE
									gs.grade_level_id = gl.grade_level_id AND
									gs.subject_id = s.subject_id AND
									gs.song_id = so.song_id AND
									gs.grade_level_id = u.grade_level_id AND
									so.artist_id = ar.artist_id AND
									so.genre_id = ge.genre_id AND
									so.lyrics_id = ly.lyrics_id AND
									u.user_id = l.user_id AND
									u.user_id = %s""", [user_id])
			datas = cur.fetchall()

			cur1 = mysql.connection.cursor()
			cur1.execute("""
								SELECT
									u.grade_level_id
								FROM
									users AS u
								WHERE
									u.user_id = %s""", [user_id])
			grade_level = cur1.fetchone()

			d = {}

			for data in datas:
				if data['ar_fullname'] not in d.keys():
					print (data)
					d.update({data['ar_fullname'] : {data['title']: {'lyrics': data['lyrics'], 'genre': data['genre'] + " Music"}}})
				elif data['title'] not in d[data['ar_fullname']].keys():  
					d[data['ar_fullname']].update({data['title']: {'lyrics': data['lyrics'], 'genre': data['genre'] + " Music"}})

			if result > 0:
				return render_template('main.html', datas=datas, grade_level=grade_level, d=d)
	else:
		return redirect(url_for('index'))

@app.route('/admin')
def admin():
	if 'username' in session:
		if session['username'] == 'admin':
			cur = mysql.connection.cursor()
			cur.execute("""
						SELECT
							gs.id,
							gl.grade_level AS grade_level,
							s.subject AS subject,
							so.title AS title,
							concat(ar.f_name, ' ', ar.l_name) as artist_fullname,
							ge.name AS genre,
							ly.lyrics AS lyrics,
							s.subject_id,
							so.song_id
						FROM grade_levels AS gl
							LEFT JOIN grade_subject AS gs ON gs.grade_level_id = gl.grade_level_id
							LEFT JOIN subjects AS s ON s.subject_id = gs.subject_id
							LEFT JOIN songs AS so ON so.song_id = gs.song_id
							LEFT JOIN artists AS ar ON ar.artist_id = so.artist_id
							LEFT JOIN genres AS ge ON ge.genre_id = so.genre_id
							LEFT JOIN lyrics AS ly ON ly.lyrics_id = so.lyrics_id
						ORDER BY gl.grade_level_id""")
			subjectSongs = cur.fetchall()


			cur1 = mysql.connection.cursor()
			cur1.execute("""
						SELECT
							u.user_id AS id,
							u.f_name AS first_name,
							u.m_name AS middle_name,
							u.l_name AS last_name,
							u.email AS email,
							u.b_day AS birthday,
							gl.grade_level AS grade_level,
							gl.grade_level_id AS gl_id,
							l.username AS username,
							l.`password` AS password
						FROM
							users AS u ,
							grade_levels AS gl ,
							login AS l
						WHERE
							u.grade_level_id = gl.grade_level_id AND
							u.user_id = l.user_id""")
			students = cur1.fetchall()


			
			


			cur3 = mysql.connection.cursor()
			cur3.execute("""
						SELECT
							*,
							artist_id AS id,
							concat(artists.f_name, ' ', artists.l_name) as artist_fullname
						FROM
							artists""")
			artists = cur3.fetchall()


			cur4 = mysql.connection.cursor()
			cur4.execute("""
						SELECT
							*
						FROM
							grade_levels""")
			grade_level = cur4.fetchall()


			cur5 = mysql.connection.cursor()
			cur5.execute("""
						SELECT
							*
						FROM
							subjects""")
			subjects = cur5.fetchall()


			cur6 = mysql.connection.cursor()
			cur6.execute("""
						SELECT
							s.song_id AS id,
							l.lyrics_id AS ly_id,
							a.artist_id,
							g.genre_id,
							s.title,
							concat(a.f_name, ' ', a.l_name) as artist_fullname,
							g.`name` AS genre,
							l.lyrics
						FROM
							songs AS s ,
							artists AS a ,
							genres AS g ,
							lyrics AS l
						WHERE
							s.artist_id = a.artist_id AND
							s.genre_id = g.genre_id AND
							s.lyrics_id = l.lyrics_id""")
			songs = cur6.fetchall()

			return render_template('admin.html', subjectSongs=subjectSongs, students=students, artists=artists, grade_level=grade_level, subjects=subjects, songs=songs)
		else:
			return redirect(url_for('main'))
	else:
		return redirect(url_for('index'))

@app.route('/logout')
def logout():
	session.pop('logged_in', None)
	session.pop('username', None)
	session.pop('user_id', None)
	return redirect(url_for('index'))

#ADD, EDIT, DELETE

@app.route('/addSubject', methods=['GET', 'POST'])
def addSubject():
	if request.method == "POST":
		subject = request.form['add_subj_name']

		cur = mysql.connection.cursor()
		cur.execute("INSERT INTO subjects(subject) VALUES (%s)", [subject])
		mysql.connection.commit()
		cur.close()
  
		return redirect(url_for('admin'))

@app.route('/addGenre', methods=['GET', 'POST'])
def addGenre():
	if request.method == "POST":
		genre = request.form['add_genre_name']

		cur = mysql.connection.cursor()
		cur.execute("INSERT INTO genres(name) VALUES (%s)", [genre])
		mysql.connection.commit()
		cur.close()

		return redirect(url_for('admin'))

@app.route('/addArtist', methods=['GET', 'POST'])
def addArtist():
	if request.method == "POST":
		fname = request.form['add_artist_f_name']
		mname = request.form['add_artist_m_name']
		lname = request.form['add_artist_l_name']
		num = request.form['add_artist_num']

		cur = mysql.connection.cursor()
		cur.execute("INSERT INTO artists(f_name, m_name, l_name, contact_num) VALUES (%s, %s, %s, %s)", [fname, mname, lname, num])
		mysql.connection.commit()
		cur.close()

		return redirect(url_for('admin'))

@app.route('/addSong', methods=['GET', 'POST'])
def addSong():
	if request.method == "POST":
		title = request.form['add_song_title']
		artist = request.form['add_song_artist']
		genre = request.form['add_song_genre']
		ly = request.form['add_song_lyrics']

		cur1 = mysql.connection.cursor()
		cur1.execute("INSERT INTO lyrics(lyrics) VALUES (%s)", [ly])
		mysql.connection.commit()
		cur1.close()

		cur2 = mysql.connection.cursor()
		cur2.execute("SELECT lyrics_id FROM lyrics ORDER BY lyrics_id DESC LIMIT 1")
		lyrics = cur2.fetchone()
		cur2.close()

		cur3 = mysql.connection.cursor()
		cur3.execute("INSERT INTO songs(lyrics_id, artist_id, genre_id, title) VALUES (%s, %s, %s, %s)", [lyrics['lyrics_id'], artist, genre, title])
		mysql.connection.commit()
		cur3.close()

		return redirect(url_for('admin'))

@app.route('/addGradeSubject', methods=['GET', 'POST'])
def addGradeSubject():
	if request.method == "POST":
		grade = request.form['add_subjSong_grade']
		subject = request.form['add_subjSong_subject']
		title = request.form['add_subjSong_title']

		cur = mysql.connection.cursor()
		cur.execute("INSERT INTO grade_subject(grade_level_id, subject_id, song_id) VALUES (%s, %s, %s)", [grade, subject, title])
		mysql.connection.commit()
		cur.close()

		return redirect(url_for('admin'))

@app.route('/addStudent', methods=['GET', 'POST'])
def addStudent():
	if request.method == "POST":
		fname = request.form['add_stud_first_name']
		mname = request.form['add_stud_middle_name']
		lname = request.form['add_stud_last_name']
		email = request.form['add_stud_email']
		birthdate = request.form['add_stud_birthdate']
		grade = request.form['add_stud_grade']
		username = request.form['add_stud_username']
		password = request.form['add_stud_password']
		user_type = 2

		cur1 = mysql.connection.cursor()
		cur1.execute("INSERT INTO users(grade_level_id, f_name, m_name, l_name, email, b_day) VALUES (%s, %s, %s, %s, %s, %s)", [grade, fname, mname, lname, email, birthdate])
		mysql.connection.commit()
		cur1.close()

		cur2 = mysql.connection.cursor()
		cur2.execute("SELECT user_id FROM users ORDER BY user_id DESC LIMIT 1")
		user = cur2.fetchone()
		cur2.close()

		cur3 = mysql.connection.cursor()
		cur3.execute("INSERT INTO login(user_id, user_type_id, username, password) VALUES (%s, %s, %s, %s)", [user['user_id'], user_type, username, password])
		mysql.connection.commit()
		cur3.close()

		return redirect(url_for('admin'))

#ADD END

@app.route('/editSubject', methods=['GET', 'POST'])
def editSubject():
	if request.method == "POST":
		id = request.form['edit_subj_id']
		subject = request.form['subj_name']

		cur = mysql.connection.cursor()
		cur.execute("UPDATE subjects SET subject = %s WHERE subject_id = %s", [subject, id])
		mysql.connection.commit()
		cur.close()

		return redirect(url_for('admin'))

@app.route('/editGenre', methods=['GET', 'POST'])
def editGenre():
	if request.method == "POST":
		id = request.form['edit_genre_id']
		genre = request.form['genre_name']

		cur = mysql.connection.cursor()
		cur.execute("UPDATE genres SET name = %s WHERE genre_id = %s", [genre, id])
		mysql.connection.commit()
		cur.close()

		return redirect(url_for('admin'))

@app.route('/editArtist', methods=['GET', 'POST'])
def editArtist():
	if request.method == "POST":
		id = request.form['edit_artist_id']
		fname = request.form['artist_f_name']
		mname = request.form['artist_m_name']
		lname = request.form['artist_l_name']
		num = request.form['artist_num']

		cur = mysql.connection.cursor()
		cur.execute("UPDATE artists SET f_name = %s, m_name = %s, l_name = %s, contact_num = %s WHERE artist_id = %s", [fname, mname, lname, num, id])
		mysql.connection.commit()
		cur.close()

		return redirect(url_for('admin'))

@app.route('/editSong', methods=['GET', 'POST'])
def editSong():
	if request.method == "POST":
		id = request.form['edit_song_id']
		title = request.form['song_title']
		artist = request.form['song_artist']
		genre = request.form['song_genre']

		lyId = request.form['edit_song_lyrics_id']
		lyrics = request.form['song_lyrics']

		cur1 = mysql.connection.cursor()
		cur1.execute("UPDATE songs SET artist_id = %s, genre_id = %s, title = %s WHERE song_id = %s", [artist, genre, title, id])
		mysql.connection.commit()
		cur1.close()

		cur2 = mysql.connection.cursor()
		cur2.execute("UPDATE lyrics SET lyrics = %s WHERE lyrics_id = %s", [lyrics, lyId])
		mysql.connection.commit()
		cur2.close()

		return redirect(url_for('admin'))

@app.route('/editGradeSubject', methods=['GET', 'POST'])
def editGradeSubject():
	if request.method == "POST":
		id = request.form['edit_gs_id']
		subjId = request.form['subjSong_subject']
		songId = request.form['subjSong_title']

		cur = mysql.connection.cursor()
		cur.execute("UPDATE grade_subject SET subject_id = %s, song_id = %s WHERE id = %s", [subjId, songId, id])
		mysql.connection.commit()
		cur.close()

		return redirect(url_for('admin'))

@app.route('/editStudent', methods=['GET', 'POST'])
def editStudent():
	if request.method == "POST":
		id = request.form['stud_id']
		fname = request.form['stud_first_name']
		mname = request.form['stud_middle_name']
		lname = request.form['stud_last_name']
		email = request.form['stud_email']
		birthdate = request.form['stud_birthdate']
		grade = request.form['stud_grade']
		username = request.form['stud_username']
		password = request.form['stud_password']

		cur1 = mysql.connection.cursor()
		cur1.execute("""
					UPDATE
						users
					SET
						grade_level_id = %s,
						f_name = %s,
						m_name = %s,
						l_name = %s,
						email = %s,
						b_day = %s
					WHERE
						user_id = %s""", [grade, fname, mname, lname, email, birthdate, id])
		mysql.connection.commit()
		cur1.close()

		cur2 = mysql.connection.cursor()
		cur2.execute("UPDATE login SET username = %s, password = %s WHERE user_id = %s", [username, password, id])
		mysql.connection.commit()
		cur2.close()

		return redirect(url_for('admin'))

#EDIT END

@app.route('/deleteSubject', methods=['GET', 'POST'])
def deleteSubject():
	if request.method == "POST":
		id = request.form['del_subj_id']

		cur = mysql.connection.cursor()
		cur.execute("DELETE FROM subjects WHERE subject_id = %s", [id])
		mysql.connection.commit()
		cur.close()

		return redirect(url_for('admin'))

@app.route('/deleteGenre', methods=['GET', 'POST'])
def deleteGenre():
	if request.method == "POST":
		id = request.form['del_genre_id']

		cur = mysql.connection.cursor()
		cur.execute("DELETE FROM genres WHERE genre_id = %s", [id])
		mysql.connection.commit()
		cur.close()

		return redirect(url_for('admin'))

@app.route('/deleteArtist', methods=['GET', 'POST'])
def deleteArtist():
	if request.method == "POST":
		id = request.form['del_artist_id']

		cur = mysql.connection.cursor()
		cur.execute("DELETE FROM artists WHERE artist_id = %s", [id])
		mysql.connection.commit()
		cur.close()

		return redirect(url_for('admin'))

@app.route('/deleteSong', methods=['GET', 'POST'])
def deleteSong():
	if request.method == "POST":
		id = request.form['del_song_id']
		lyId = request.form['del_lyrics_id']

		cur = mysql.connection.cursor()
		cur.execute("DELETE FROM songs WHERE song_id = %s", [id])
		mysql.connection.commit()
		cur.close()

		cur = mysql.connection.cursor()
		cur.execute("DELETE FROM lyrics WHERE lyrics_id = %s", [lyId])
		mysql.connection.commit()
		cur.close()

		return redirect(url_for('admin'))

@app.route('/deleteGradeSubject', methods=['GET', 'POST'])
def deleteGradeSubject():
	if request.method == "POST":
		id = request.form['del_ss_id']

		cur = mysql.connection.cursor()
		cur.execute("DELETE FROM grade_subject WHERE id = %s", [id])
		mysql.connection.commit()
		cur.close()

		return redirect(url_for('admin'))

@app.route('/deleteStudent', methods=['GET', 'POST'])
def deleteStudent():
	if request.method == "POST":
		id = request.form['del_stud_id']

		cur = mysql.connection.cursor()
		cur.execute("DELETE FROM users WHERE user_id = %s", [id])
		mysql.connection.commit()
		cur.close()

		cur = mysql.connection.cursor()
		cur.execute("DELETE FROM login WHERE user_id = %s", [id])
		mysql.connection.commit()
		cur.close()

		return redirect(url_for('admin'))

if __name__ == '__main__':
	app.secret_key='secret123'
	app.run(debug = True)