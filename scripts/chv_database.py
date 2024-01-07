# import sqlite3


thread_fields       = ['no', 'last_modified', 'replies', 'sub', 'com', 'thumbnail']
thread_posts_fields = ['thread_no', 'post_no']
post_fields         = ['no', 'com', 'sub', 'name', 'id', 'file', 'time', 'filename', 'ext', 'country', 'country_name']
post_replies_fields = ['post_no', 'reply_no' ]

thread_fields_comma         = ','.join(thread_fields)
thread_posts_fields_comma   = ','.join(thread_posts_fields)
post_fields_comma           = ','.join(post_fields)
post_replies_fields_comma   = ','.join(post_replies_fields)

thread_fields_question          = ','.join(['?' for _ in thread_fields])
thread_posts_fields_question    = ','.join(['?' for _ in thread_posts_fields])
post_fields_question            = ','.join(['?' for _ in post_fields])
post_replies_fields_question    = ','.join(['?' for _ in post_replies_fields])


# save a thread to db
def save_thread(db_connection, thread: dict):
    db_cursor = db_connection.cursor()

    # insert basic thread info into threads table
    thread_values = list()
    for thread_field in thread_fields:
        thread_values.append(thread[thread_field] if thread_field in thread else None)
    db_cursor.execute(f"""
        INSERT OR REPLACE INTO threads ({thread_fields_comma})
        VALUES ({thread_fields_question});
        """, thread_values)

    for post_no in thread['thread']:
        # insert post thread relation in thread_replies table
        db_cursor.execute(f"""
            INSERT OR REPLACE INTO thread_posts ({thread_posts_fields_comma})
            VALUES ({thread_posts_fields_question});
            """, [thread['no'], post_no])

        # insert post info into posts table
        post_values = list()
        for post_field in post_fields:
            post_values.append(thread['thread'][post_no][post_field] if post_field in thread['thread'][post_no] else None)
        db_cursor.execute(f"""
            INSERT OR REPLACE INTO posts ({post_fields_comma})
            VALUES ({post_fields_question});
            """, post_values)

        for succ in thread['thread'][post_no]['succ']:
            # insert succ into post_replies table
            db_cursor.execute(f"""
                INSERT OR REPLACE INTO post_replies ({post_replies_fields_comma})
                VALUES ({post_replies_fields_question});
                """, [post_no, succ])

        # should be duplicates, but still
        for pred in thread['thread'][post_no]['pred']:
            # insert pred into post_replies table
            db_cursor.execute(f"""
                INSERT OR REPLACE INTO post_replies ({post_replies_fields_comma})
                VALUES ({post_replies_fields_question});
                """, [pred, post_no])

    # if creating dicts is slow, may move to lists in the future

    db_connection.commit()
    return


# get threads from db
def get_threads(db_connection, thread_nos: list):
    db_cursor = db_connection.cursor()

    threads_dict = dict()
    for thread_no in thread_nos:
        # query the threads table to get basic thread info
        db_cursor.execute(f"""
            SELECT {thread_fields_comma}
            FROM threads
            WHERE no = ?;
            """, [thread_no])
        db_output = db_cursor.fetchall()
        if len(db_output) == 0:
            continue
        threads_dict[thread_no] = dict()
        for i in range(len(thread_fields)):
            if db_output[0][i] != None:
                threads_dict[thread_no][thread_fields[i]] = db_output[0][i]

        # query the thread_posts table to get posts in thread
        db_cursor.execute(f"""
            SELECT {thread_posts_fields_comma}
            FROM thread_posts
            WHERE thread_no = ?;
            """, [thread_no])
        db_output = db_cursor.fetchall()
        post_nos = [x[1] for x in db_output]
        threads_dict[thread_no]['replies'] = len(post_nos)

        threads_dict[thread_no]['thread'] = dict()
        for post_no in post_nos:
            # query the posts table to get post info
            db_cursor.execute(f"""
                SELECT {post_fields_comma}
                FROM posts
                WHERE no = ?;
                """, [post_no])
            db_output = db_cursor.fetchall()
            threads_dict[thread_no]['thread'][post_no] = dict()
            for i in range(len(post_fields)):
                if db_output[0][i] != None:
                    threads_dict[thread_no]['thread'][post_no][post_fields[i]] = db_output[0][i]

            # query the post_replies table to get succ
            db_cursor.execute(f"""
                SELECT {post_replies_fields_comma}
                FROM post_replies
                WHERE post_no = ?;
                """, [post_no])
            db_output = db_cursor.fetchall()
            succ_nos = [x[1] for x in db_output]
            threads_dict[thread_no]['thread'][post_no]['succ'] = succ_nos

            # query the post_replies table to get pred
            db_cursor.execute(f"""
                SELECT {post_replies_fields_comma}
                FROM post_replies
                WHERE reply_no = ?;
                """, [post_no])
            db_output = db_cursor.fetchall()
            pred_nos = [x[0] for x in db_output]
            threads_dict[thread_no]['thread'][post_no]['pred'] = pred_nos

    return threads_dict


# get most recent threads
def get_thread_nos_by_last_modified(db_connection, thread_count: int):
    db_cursor = db_connection.cursor()
    db_cursor.execute(f"""
        SELECT no
        FROM threads
        ORDER BY last_modified DESC
        LIMIT {thread_count};
        """)
    db_output = db_cursor.fetchall()
    db_output = [x[0] for x in db_output]
    return db_output


# get most recent threads
def get_thread_nos_by_created(db_connection, thread_count: int):
    db_cursor = db_connection.cursor()
    db_cursor.execute(f"""
        SELECT t.no
        FROM threads AS t
        JOIN posts AS p
            ON t.no = p.no
        ORDER BY p.time DESC
        LIMIT {thread_count};
        """)
    db_output = db_cursor.fetchall()
    db_output = [x[0] for x in db_output]
    return db_output


# get most recent threads
def get_thread_nos_by_last_modified_ordered_by_replies(db_connection, thread_count: int):
    db_cursor = db_connection.cursor()
    db_cursor.execute(f"""
        SELECT no
        FROM
        (
            SELECT no, replies
            FROM threads
            WHERE replies > 10
            ORDER BY replies DESC
            LIMIT {thread_count}
        )
        ORDER BY replies;
        """)
    db_output = db_cursor.fetchall()
    db_output = [x[0] for x in db_output]
    return db_output


# create tables if they didn't already exist
def create_board_db(db_connection):
    db_connection.execute('''
    CREATE TABLE IF NOT EXISTS threads (
        no INTEGER PRIMARY KEY,

        last_modified INTEGER,
        replies INT,

        sub TEXT,
        com TEXT,
        thumbnail BLOB
    );
    ''')

    db_connection.execute('''
    CREATE INDEX IF NOT EXISTS threads_indexed_by_no
    ON threads (no); 
    ''')

    db_connection.execute('''
    CREATE TABLE IF NOT EXISTS thread_posts (
        thread_no INTEGER,
        post_no INTEGER,
        PRIMARY KEY (thread_no, post_no)
    );
    ''')

    db_connection.execute('''
    CREATE INDEX IF NOT EXISTS thread_posts_indexed_by_thread_no
    ON thread_posts (thread_no); 
    ''')

    db_connection.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        no INTEGER PRIMARY KEY,

        com TEXT,
        sub TEXT,

        name TEXT,
        id INTEGER,

        file TEXT,           
        time INTEGER,           
        filename TEXT,           
        ext TEXT,

        country TEXT,
        country_name TEXT
    );
    ''')

    db_connection.execute('''
    CREATE INDEX IF NOT EXISTS posts_indexed_by_no
    ON posts (no); 
    ''')

    db_connection.execute('''
    CREATE TABLE IF NOT EXISTS post_replies (
        post_no INTEGER,
        reply_no INTEGER,
        PRIMARY KEY (post_no, reply_no)
    );
    ''')

    db_connection.execute('''
    CREATE INDEX IF NOT EXISTS post_replies_indexed_by_post_no
    ON post_replies (post_no); 
    ''')

    db_connection.execute('''
    CREATE INDEX IF NOT EXISTS post_replies_indexed_by_reply_no
    ON post_replies (reply_no); 
    ''')

    # foreign keys may be added in the future

    db_connection.commit()
    return


if __name__ == '__main':
    pass