from psycopg2.extras import RealDictCursor
import connection


@connection.connection_handler
def get_questions(cursor: RealDictCursor, search_phrase, limit):
    if search_phrase:
        query = """
        SELECT DISTINCT
               q.id,
               q.submission_time,
               q.view_number,
               q.vote_number,
               q.title,
               q.message,
               q.image
        FROM question AS q
        WHERE q.title LIKE %s OR q.message LIKE %s
        LIMIT %s;
        """
        cursor.execute(query, (f"%{search_phrase}%",
                               f"%{search_phrase}%", limit))
    else:
        query = "SELECT * FROM question LIMIT %s"
        cursor.execute(query, (limit,))
    return cursor.fetchall()


@connection.connection_handler
def get_answers(cursor: RealDictCursor):
    query = """
        SELECT *
        FROM answer
        """
    cursor.execute(query)
    return cursor.fetchall()


@connection.connection_handler
def get_last_question_id(cursor: RealDictCursor):
    questions = get_questions('', 1000)
    try:
        return questions[-1]["id"]
    except IndexError:
        return 0


@connection.connection_handler
def add_question(cursor: RealDictCursor, question):
    query = """
            INSERT INTO question (submission_time,
                                  view_number,
                                  vote_number,
                                  title,
                                  message,
                                  image,
                                  user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """
    cursor.execute(query, (question["submission_time"],
                           question["view_number"],
                           question["vote_number"],
                           question["title"],
                           question["message"],
                           question["image"],
                           question["user_id"]))


@connection.connection_handler
def add_answer(cursor: RealDictCursor, answer):
    query = """
            INSERT INTO answer (submission_time,
                                vote_number,
                                question_id,
                                message,
                                image,
                                user_id,
                                accepted)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """
    cursor.execute(query, (answer["submission_time"],
                           answer["vote_number"],
                           answer["question_id"],
                           answer["message"],
                           answer["image"],
                           answer["user_id"],
                           answer['accepted']))


@connection.connection_handler
def get_question_by_id(cursor: RealDictCursor, id):
    query = "SELECT * FROM question WHERE id=(%s)"
    cursor.execute(query, (id, ))
    return cursor.fetchone()


@connection.connection_handler
def get_answer_by_id(cursor: RealDictCursor, id):
    query = "SELECT * FROM answer WHERE id=(%s)"
    cursor.execute(query, (id, ))
    return cursor.fetchone()


@connection.connection_handler
def get_answers_by_question_id(cursor: RealDictCursor, question_id):
    query = """
        SELECT *
        FROM answer
        WHERE question_id=(%s)
        """
    cursor.execute(query, (question_id, ))
    return cursor.fetchall()


@connection.connection_handler
def delete_question(cursor: RealDictCursor, question_id):
    query = """
    DELETE FROM question_tag WHERE question_id = %s;
    DELETE FROM tag WHERE id = (SELECT tag_id FROM question_tag WHERE question_id = %s);
    DELETE FROM comment WHERE question_id = %s;
    DELETE FROM answer WHERE question_id = %s;
    DELETE FROM question WHERE id = %s;
    """
    cursor.execute(query, (question_id, question_id,
                           question_id, question_id, question_id))


@connection.connection_handler
def delete_answer(cursor: RealDictCursor, answer_id):
    query = """
    DELETE FROM comment WHERE answer_id = (%s);
    DELETE FROM answer WHERE id=(%s);
    """
    cursor.execute(query, (answer_id, answer_id))


@connection.connection_handler
def modify_question(cursor: RealDictCursor, question_id, modified_question):
    query = """
            UPDATE question SET submission_time=(%s),
                                view_number=(%s),
                                vote_number=(%s),
                                title=(%s),
                                message=(%s),
                                image=(%s)
            WHERE id=(%s)
            """
    cursor.execute(query, (modified_question["submission_time"],
                           modified_question["view_number"],
                           modified_question["vote_number"],
                           modified_question["title"],
                           modified_question["message"],
                           modified_question["image"],
                           question_id))


@connection.connection_handler
def modify_answer(cursor: RealDictCursor, answer_id, modified_answer):
    query = """
            UPDATE answer SET message=(%s) WHERE id=(%s)
            """
    cursor.execute(query, (modified_answer, answer_id))


@connection.connection_handler
def modify_comment(cursor: RealDictCursor, comment_id, modified_comment):
    query = """UPDATE comment SET message=(%s), submission_time=(%s) WHERE id=(%s)"""
    cursor.execute(query, (modified_comment['message'],
                           modified_comment['submission_time'],
                           comment_id))


@connection.connection_handler
def upvote_question(cursor: RealDictCursor, question_id):
    question = get_question_by_id(question_id)
    query = "UPDATE question SET vote_number = %s WHERE id = %s"
    cursor.execute(query, (question["vote_number"] + 1, question["id"]))


@connection.connection_handler
def downvote_question(cursor: RealDictCursor, question_id):
    question = get_question_by_id(question_id)
    query = "UPDATE question SET vote_number = %s WHERE id = %s"
    cursor.execute(query, (question["vote_number"] - 1, question["id"]))


@connection.connection_handler
def upvote_answer(cursor: RealDictCursor, answer_id):
    answer = get_answer_by_id(answer_id)
    query = "UPDATE answer SET vote_number = %s WHERE id = %s"
    cursor.execute(query, (answer["vote_number"] + 1, answer["id"]))


@connection.connection_handler
def downvote_answer(cursor: RealDictCursor, answer_id):
    answer = get_answer_by_id(answer_id)
    query = "UPDATE answer SET vote_number = %s WHERE id = %s"
    cursor.execute(query, (answer["vote_number"] - 1, answer["id"]))


@connection.connection_handler
def increase_view_number_of_question(cursor: RealDictCursor, question_id):
    question = get_question_by_id(question_id)
    query = "UPDATE question SET view_number=(%s) WHERE id=(%s)"
    cursor.execute(query, (question["view_number"] + 1, question["id"]))


@connection.connection_handler
def get_question_id_from_answer_id(cursor: RealDictCursor, answer_id):
    query = "SELECT question_id FROM answer WHERE id = %s"
    cursor.execute(query, (answer_id, ))
    return cursor.fetchone()["question_id"]


@connection.connection_handler
def add_comment_to_answer(cursor: RealDictCursor, answer_id, comment):
    query = """
    INSERT INTO comment (answer_id,
                         message,
                         submission_time,
                         edited_count,
                         user_id)
    VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(query, (answer_id,
                           comment["message"],
                           comment["submission_time"],
                           0,
                           comment["user_id"]))


@connection.connection_handler
def add_comment_to_question(cursor: RealDictCursor, question_id, comment):
    query = """
    INSERT INTO comment (question_id,
                         message,
                         submission_time,
                         edited_count,
                         user_id)
    VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(query, (question_id,
                           comment["message"],
                           comment["submission_time"],
                           0,
                           comment["user_id"]))


@connection.connection_handler
def get_comments_by_question_id(cursor: RealDictCursor, question_id):
    query = """
    SELECT * FROM comment
    WHERE question_id = (%s)
    """
    cursor.execute(query, (question_id, ))
    return cursor.fetchall()


@connection.connection_handler
def get_comments_by_answer_id(cursor: RealDictCursor, answer_id):
    query = """
    SELECT * FROM comment
    WHERE answer_id = (%s)
    """
    cursor.execute(query, (answer_id, ))
    return cursor.fetchall()


@connection.connection_handler
def get_comment_by_id(cursor: RealDictCursor, comment_id):
    query = "SELECT * FROM comment WHERE id = %s;"
    cursor.execute(query, (comment_id, ))
    return cursor.fetchone()


@connection.connection_handler
def increase_edit_number_of_comment(cursor: RealDictCursor, comment_id):
    comment = get_comment_by_id(comment_id)
    query = "UPDATE comment SET edited_count=(%s) WHERE id=(%s)"
    cursor.execute(query, (comment["edited_count"] + 1, comment["id"]))


@connection.connection_handler
def get_answer_id_by_comment_id(cursor: RealDictCursor, comment_id):
    query = "SELECT answer_id FROM comment WHERE id=(%s)"
    cursor.execute(query, (comment_id, ))
    return cursor.fetchone()


@connection.connection_handler
def delete_comment_by_id(cursor: RealDictCursor, comment_id):
    query = "DELETE FROM comment WHERE id = %s"
    cursor.execute(query, (comment_id, ))


@connection.connection_handler
def display_5_latest_questions(cursor: RealDictCursor):
    query = """
    SELECT * FROM question
    ORDER BY submission_time DESC
    LIMIT 5
    """
    cursor.execute(query)
    return cursor.fetchall()


@connection.connection_handler
def get_tags(cursor: RealDictCursor):
    query = "SELECT * FROM tag"
    cursor.execute(query)
    return cursor.fetchall()


@connection.connection_handler
def add_tag(cursor: RealDictCursor, tag):
    query = """
    INSERT INTO tag (name) VALUES (%s)
    """
    cursor.execute(query, (tag, ))


@connection.connection_handler
def get_tag_id_by_name(cursor: RealDictCursor, tag_name):
    query = "SELECT id FROM tag WHERE name = %s"
    cursor.execute(query, (tag_name, ))
    return cursor.fetchone()


@connection.connection_handler
def add_tag_to_question(cursor: RealDictCursor, question_id, tag_name):
    query = """
    INSERT INTO question_tag (question_id,
                              tag_id)
    VALUES (%s, %s)
    """
    cursor.execute(query, (question_id, get_tag_id_by_name(tag_name)['id']))


@connection.connection_handler
def delete_tag_from_question(cursor: RealDictCursor, question_id, tag_id):
    query = """
    DELETE FROM question_tag WHERE question_id = %s AND tag_id = %s;
    """
    cursor.execute(query, (question_id, tag_id))


@connection.connection_handler
def get_tags_by_question_id(cursor: RealDictCursor, question_id):
    query = """SELECT t.name, t.id
               FROM tag AS t
               JOIN question_tag AS q ON t.id = q.tag_id
               WHERE q.question_id = %s"""
    cursor.execute(query, (question_id, ))
    return cursor.fetchall()


@connection.connection_handler
def add_user(cursor: RealDictCursor, username, password):
    query = """
    INSERT INTO users (username,
                       password,
                       question_count,
                       answer_count,
                       comment_count,
                       reputation)
    VALUES (%s, %s, 0, 0, 0, 0)
    """
    cursor.execute(query, (username, password))


@connection.connection_handler
def get_password_by_username(cursor: RealDictCursor, username):
    query = """SELECT password from users WHERE username=%s"""
    cursor.execute(query, (username, ))
    return cursor.fetchone()['password']


@connection.connection_handler
def username_taken(cursor: RealDictCursor, username):
    query = "SELECT COUNT(users.username) as count FROM users WHERE users.username = %s"
    cursor.execute(query, (username, ))
    count = cursor.fetchone()['count']
    if count == 0:
        return False
    return True


@connection.connection_handler
def get_users(cursor: RealDictCursor):
    query = "SELECT * FROM users"
    cursor.execute(query)
    return cursor.fetchall()


@connection.connection_handler
def get_user_by_username(cursor: RealDictCursor, username):
    query = "SELECT * FROM users WHERE username=%s"
    cursor.execute(query, (username, ))
    return cursor.fetchone()


@connection.connection_handler
def get_user_by_id(cursor: RealDictCursor, id):
    query = "SELECT * FROM users WHERE id=%s"
    cursor.execute(query, (id, ))
    return cursor.fetchone()


@connection.connection_handler
def get_user_id_by_username(cursor: RealDictCursor, username):
    return get_user_by_username(username)["id"]


@connection.connection_handler
def get_questions_by_userid(cursor: RealDictCursor, id):
    query = "SELECT * FROM question WHERE user_id=%s"
    cursor.execute(query, (id, ))
    return cursor.fetchall()


@connection.connection_handler
def get_answers_by_userid(cursor: RealDictCursor, id):
    query = "SELECT * FROM answer WHERE user_id=%s"
    cursor.execute(query, (id, ))
    return cursor.fetchall()


@connection.connection_handler
def get_comments_by_userid(cursor: RealDictCursor, id):
    query = "SELECT * FROM comment WHERE user_id=%s"
    cursor.execute(query, (id, ))
    return cursor.fetchall()


@connection.connection_handler
def get_tags_and_their_amounts(cursor: RealDictCursor):
    query = """SELECT tag.name AS name,
                      COUNT(question_tag.question_id) AS count
                FROM  tag
                JOIN  question_tag
                ON    question_tag.tag_id = tag.id
                GROUP BY tag.name"""
    cursor.execute(query)
    return cursor.fetchall()


@connection.connection_handler
def get_reputation(cursor: RealDictCursor, user_id: int):
    query = "SELECT reputation FROM users WHERE id=%s"
    cursor.execute(query, (user_id, ))
    return cursor.fetchone()


@connection.connection_handler
def gain_reputation(cursor: RealDictCursor, user_id: int, amount: int):
    current_rep = get_reputation(user_id)
    query = "UPDATE users SET reputation=%s WHERE id=%s"
    cursor.execute(query, (current_rep['reputation'] + amount, user_id))


@connection.connection_handler
def lose_reputation(cursor: RealDictCursor, user_id: int, amount: int):
    current_rep = get_reputation(user_id)
    query = "UPDATE users SET reputation=%s WHERE id=%s"
    cursor.execute(query, (current_rep['reputation'] - amount, user_id))


@connection.connection_handler
def accept_answer(cursor: RealDictCursor, answer_id: int):
    query = "UPDATE answer SET accepted=TRUE WHERE id=%s"
    cursor.execute(query, (answer_id, ))


@connection.connection_handler
def unaccept_answer(cursor: RealDictCursor, answer_id: int):
    query = "UPDATE answer SET accepted=FALSE WHERE id=%s"
    cursor.execute(query, (answer_id, ))


@connection.connection_handler
def get_user_id_by_answer_id(cursor: RealDictCursor, answer_id):
    query = "SELECT user_id FROM answer WHERE id=%s"
    cursor.execute(query, (answer_id, ))
    return cursor.fetchone()


@connection.connection_handler
def get_user_id_by_comment_id(cursor: RealDictCursor, comment_id):
    query = "SELECT user_id FROM comment WHERE id=%s"
    cursor.execute(query, (comment_id, ))
    return cursor.fetchone()
