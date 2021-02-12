from flask import Flask, render_template, request, session, flash
from werkzeug.utils import redirect
import data_handler
import util
import os
import bcrypt

app = Flask(__name__)
UPLOAD_FOLDER = "./static"
ALLOWED_EXTENSIONS = {'png', 'jpg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = b'_5#y2L"F4Q8znxec]/'


def hash_password(plain_text_password):
    hashed_bytes = bcrypt.hashpw(
        plain_text_password.encode('utf-8'), bcrypt.gensalt())
    return hashed_bytes.decode('utf-8')


def verify_password(plain_text_password, hashed_password):
    hashed_bytes_password = hashed_password.encode('utf-8')
    return bcrypt.checkpw(plain_text_password.encode('utf-8'), hashed_bytes_password)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
@app.route("/list")
def list_page():
    order = request.args.get('ordering')
    direction = request.args.get('direction')
    search_phrase = request.args.get('search')
    limit = request.args.get('limit')
    if order is None:
        order = 'id'
    if direction is None:
        direction = 'asc'
    if search_phrase is None:
        search_phrase = ''
    if limit is None:
        limit = 5
    questions = data_handler.get_questions(search_phrase, limit)
    if direction == 'asc':
        questions = sorted(questions, key=lambda x: x[order])
    else:
        questions = sorted(questions, key=lambda x: x[order], reverse=True)
    if 'username' in session:
        user_id = data_handler.get_user_id_by_username(session['username'])
        return render_template("list_questions.html", questions=questions, search_text=search_phrase, user_id=user_id)
    return render_template("list_questions.html", questions=questions, search_text=search_phrase)


@app.route("/register", methods=['GET', 'POST'])
def registration_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == "" or password == "":
            flash("both fields need to be filled out")
            return redirect("/register")
        if data_handler.username_taken(username):
            flash("the username is taken")
            return redirect("/register")
        hashed_password = hash_password(password)
        data_handler.add_user(username, hashed_password)
        return redirect("/login")
    return render_template("register.html")


@app.route("/login", methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == "" or password == "":
            flash("both fields need to be filled out")
            return redirect("/login")
        db_password = data_handler.get_password_by_username(username)
        if verify_password(password, db_password):
            session['username'] = username
            return redirect("/")
        else:
            flash("wrong password or username")
            return redirect("/login")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("username")
    return redirect("/")


@app.route("/users")
def users_page():
    users = data_handler.get_users()
    return render_template("users.html", users=users)


@app.route("/user/<int:id>")
def user_page(id: int):
    user = data_handler.get_user_by_id(id)
    questions = data_handler.get_questions_by_userid(id)
    answers = data_handler.get_answers_by_userid(id)
    comments = data_handler.get_comments_by_userid(id)
    return render_template("user.html", user=user, questions=questions, answers=answers, comments=comments)


@app.route("/question/<int:question_id>/new-tag", methods=['GET', 'POST'])
def add_tag_to_question_page(question_id: int):
    tags = data_handler.get_tags()
    question_tags = data_handler.get_tags_by_question_id(question_id)
    if request.method == 'POST':
        tagname = request.form['tagname']
        all_tags_name = []
        for i in tags:
            all_tags_name.append(i['name'])
        if tagname not in all_tags_name and tagname is not None and tagname != '':
            data_handler.add_tag(tagname)
        tagnames = []
        for i in question_tags:
            tagnames.append(i['name'])
        if tagname in tagnames:
            return render_template("add_tag_question.html", tags=tags,
                                   question_id=question_id, question_tags=question_tags)
        data_handler.add_tag_to_question(question_id, tagname)
        return redirect(f"/question/{question_id}")
    return render_template("add_tag_question.html", tags=tags, question_id=question_id, question_tags=question_tags)


@app.route("/tags")
def tags():
    tags = data_handler.get_tags_and_their_amounts()
    return render_template("tags.html", tags=tags)


@app.route("/question/<int:question_id>/tag/<int:tag_id>/delete")
def remove_tag_from_question(question_id: int, tag_id: int):
    data_handler.delete_tag_from_question(question_id, tag_id)
    return redirect(f"/question/{question_id}")


@app.route("/question/<int:question_id>")
def display_question_page(question_id: int):
    question = data_handler.get_question_by_id(question_id)
    data_handler.increase_view_number_of_question(question_id)
    answers = data_handler.get_answers_by_question_id(question_id)
    tags = data_handler.get_tags_by_question_id(question_id)
    comments = data_handler.get_comments_by_question_id(question_id)
    if 'username' in session:
        user_id = data_handler.get_user_id_by_username(session['username'])
        return render_template("display_question.html",
                               question=question,
                               answers=answers,
                               question_id=question_id,
                               tags=tags,
                               comments=comments,
                               user_id=user_id)
    return render_template("display_question.html",
                           question=question,
                           answers=answers,
                           question_id=question_id,
                           tags=tags,
                           comments=comments)


@app.route("/add_question", methods=['GET', 'POST'])
def add_question_page():
    if request.method == 'GET':
        return render_template("add_question.html")
    else:
        image = request.files['file']
        if allowed_file(image.filename):
            image.save(os.path.join(
                app.config['UPLOAD_FOLDER'], image.filename))
        new_question = {
            'id': 0,
            'submission_time': util.get_current_date(),
            'view_number': 0,
            'vote_number': 0,
            'title': request.form['title'].capitalize(),
            'message': request.form['message'].capitalize(),
            'image': image.filename,
            'user_id': data_handler.get_user_id_by_username(session['username'])
        }
        data_handler.add_question(new_question)
        return redirect(f"/question/{data_handler.get_last_question_id()}")


@app.route("/question/<int:question_id>/new-answer", methods=['GET', 'POST'])
def new_answer_page(question_id: int):
    if request.method == 'GET':
        return render_template("new_answer.html", question_id=question_id)
    else:
        image = request.files['file']
        if allowed_file(image.filename):
            image.save(os.path.join(
                app.config['UPLOAD_FOLDER'], image.filename))
        new_answer = {
            'id': 0,
            'submission_time': util.get_current_date(),
            'vote_number': 0,
            'question_id': question_id,
            'message': request.form['message'],
            'image': image.filename,
            'user_id': data_handler.get_user_id_by_username(session['username']),
            'accepted': False
        }
        data_handler.add_answer(new_answer)
        return redirect(f"/question/{question_id}")


@app.route("/question/<int:question_id>/delete")
def delete_question(question_id: int):
    data_handler.delete_question(question_id)
    return redirect('/list')


@app.route("/question/<int:question_id>/edit", methods=['GET', 'POST'])
def edit_question(question_id: int):
    question = data_handler.get_question_by_id(question_id)
    if request.method == 'GET':
        return render_template('edit_question.html', question=question, question_id=question_id)
    else:
        modified_question = {
            'id': question['id'],
            'submission_time': question['submission_time'],
            'view_number': question['view_number'],
            'vote_number': question['vote_number'],
            'title': request.form['title'],
            'message': request.form['message'],
            'image': question['image']
        }
        data_handler.modify_question(question_id, modified_question)
        return redirect(f'/question/{question_id}')


@app.route("/answer/<int:answer_id>/delete")
def delete_answer(answer_id: int):
    question_id = data_handler.get_question_id_from_answer_id(answer_id)
    data_handler.delete_answer(answer_id)
    return redirect(f"/question/{question_id}")


@app.route("/question/<int:question_id>/new-comment", methods=['GET', 'POST'])
def question_add_comment(question_id):
    if request.method == 'POST':
        message = request.form['message']
        new_comment = {
            'message': message,
            'submission_time': util.get_current_date(),
            'user_id': data_handler.get_user_id_by_username(session['username'])
        }
        data_handler.add_comment_to_question(question_id, new_comment)
        return redirect(f"/question/{question_id}")
    return render_template("add_comment_question.html", question_id=question_id)


@app.route("/answer/<int:answer_id>/new-comment", methods=['GET', 'POST'])
def answer_add_comment(answer_id):
    question_id = data_handler.get_question_id_from_answer_id(answer_id)
    if request.method == 'POST':
        message = request.form['message']
        new_comment = {
            'message': message,
            'submission_time': util.get_current_date(),
            'user_id': data_handler.get_user_id_by_username(session['username'])
        }
        data_handler.add_comment_to_answer(answer_id, new_comment)
        return redirect(f"/question/{question_id}")
    return render_template("add_comment_answer.html", answer_id=answer_id, question_id=question_id)


@app.route("/comment/<int:answer_id>")
def get_answer_comments(answer_id):
    question_id = data_handler.get_question_id_from_answer_id(answer_id)
    comments = data_handler.get_comments_by_answer_id(answer_id)
    user_id = data_handler.get_user_id_by_answer_id(answer_id)['user_id']
    return render_template("answer_comments.html", comments=comments, question_id=question_id, user_id=user_id)


@app.route("/comment/<int:comment_id>/edit", methods=['GET', 'POST'])
def edit_comment(comment_id):
    comment = data_handler.get_comment_by_id(comment_id)
    if request.method == 'POST':
        message = request.form['message']
        new_comment = {
            'message': message,
            'submission_time': util.get_current_date()
        }
        data_handler.modify_comment(comment_id, new_comment)
        data_handler.increase_edit_number_of_comment(comment_id)
        return redirect("/")
    return render_template("edit_comment.html", comment=comment)


@app.route("/comment/<int:comment_id>/delete")
def delete_comment(comment_id):
    data_handler.delete_comment_by_id(comment_id)
    return redirect("/")


@app.route("/answer/<int:answer_id>/edit", methods=['GET', 'POST'])
def edit_answer(answer_id):
    question_id = data_handler.get_question_id_from_answer_id(answer_id)
    if request.method == 'POST':
        message = request.form['message']
        data_handler.modify_answer(answer_id, message)
        return redirect(f"/question/{question_id}")
    answer = data_handler.get_answer_by_id(answer_id)
    current_message = answer['message']
    return render_template("edit_answer.html", answer_id=answer_id, message=current_message, question_id=question_id)


@app.route("/question/<int:question_id>/vote_up")
def question_vote_up(question_id: int):
    data_handler.upvote_question(question_id)
    question = data_handler.get_question_by_id(question_id)
    data_handler.gain_reputation(question['user_id'], 5)
    return redirect("/list")


@app.route("/question/<int:question_id>/vote_down")
def question_vote_down(question_id: int):
    data_handler.downvote_question(question_id)
    question = data_handler.get_question_by_id(question_id)
    data_handler.lose_reputation(question['user_id'], 2)
    return redirect("/list")


@app.route("/answer/<int:answer_id>/vote_up")
def answer_vote_up(answer_id: int):
    data_handler.upvote_answer(answer_id)
    question_id = data_handler.get_question_id_from_answer_id(answer_id)
    question = data_handler.get_question_by_id(question_id)
    data_handler.gain_reputation(question['user_id'], 10)
    return redirect(f"/question/{question_id}")


@app.route("/answer/<int:answer_id>/vote_down")
def answer_vote_down(answer_id: int):
    data_handler.downvote_answer(answer_id)
    question_id = data_handler.get_question_id_from_answer_id(answer_id)
    question = data_handler.get_question_by_id(question_id)
    data_handler.lose_reputation(question['user_id'], 2)
    return redirect(f"/question/{question_id}")


@app.route("/answer/<int:question_id>/<int:answer_id>/accept")
def accept_answer(question_id: int, answer_id: int):
    data_handler.accept_answer(answer_id)
    user_id = data_handler.get_user_id_by_answer_id(answer_id)
    data_handler.gain_reputation(user_id['user_id'], 15)
    return redirect(f"/question/{question_id}")


@app.route("/answer/<int:question_id>/<int:answer_id>/unaccept")
def unaccept_answer(question_id: int, answer_id: int):
    data_handler.unaccept_answer(answer_id)
    user_id = data_handler.get_user_id_by_answer_id(answer_id)
    data_handler.lose_reputation(user_id['user_id'], 15)
    return redirect(f"/question/{question_id}")


if __name__ == "__main__":
    app.run(debug=True)
