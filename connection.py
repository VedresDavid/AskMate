import psycopg2
import psycopg2.extras


def get_connection_string():
    # rewrite user_name and password
    user_name = 'yourPostgresUsername'
    password = 'yourPostgresPassword'
    host = 'localhost'
    database_name = 'yourDBName'

    return 'postgresql://{user_name}:{password}@{host}/{database_name}'.format(
        user_name=user_name,
        password=password,
        host=host,
        database_name=database_name
    )


def open_database():
    try:
        connection = psycopg2.connect(get_connection_string())
        connection.autocommit = True
    except psycopg2.DatabaseError as exception:
        print('Database connection problem')
        raise exception
    return connection


def connection_handler(function):
    def wrapper(*args, **kwargs):
        connection = open_database()
        dict_cur = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        ret_value = function(dict_cur, *args, **kwargs)
        dict_cur.close()
        connection.close()
        return ret_value
    return wrapper
