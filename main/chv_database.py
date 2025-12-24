import sqlite3


THREAD_FIELDS       = ['no', 'last_modified', 'replies', 'sub', 'com', 'thumbnail', 'images', 'is_archived', 'is_404d']
THREAD_POSTS_FIELDS = ['thread_no', 'post_no']
POST_FIELDS         = ['no', 'com', 'sub', 'name', 'id', 'file', 'time', 'filename', 'ext', 'country', 'country_name']
POST_REPLIES_FIELDS = ['post_no', 'reply_no' ]

THREAD_FIELDS_COMMA         = ','.join(THREAD_FIELDS)
THREAD_POSTS_FIELDS_COMMA   = ','.join(THREAD_POSTS_FIELDS)
POST_FIELDS_COMMA           = ','.join(POST_FIELDS)
POST_REPLIES_FIELDS_COMMA   = ','.join(POST_REPLIES_FIELDS)

THREAD_FIELDS_QUESTION          = ','.join(['?' for _ in THREAD_FIELDS])
THREAD_POSTS_FIELDS_QUESTION    = ','.join(['?' for _ in THREAD_POSTS_FIELDS])
POST_FIELDS_QUESTION            = ','.join(['?' for _ in POST_FIELDS])
POST_REPLIES_FIELDS_QUESTION    = ','.join(['?' for _ in POST_REPLIES_FIELDS])


# save a thread to db
def save_thread(db_connection, thread: dict):
    db_cursor = db_connection.cursor()

    # insert basic thread info into threads table
    thread_values = list()
    for thread_field in THREAD_FIELDS:
        thread_values.append(thread[thread_field] if thread_field in thread else None)
    db_cursor.execute(f"""
        INSERT OR REPLACE INTO threads ({THREAD_FIELDS_COMMA})
        VALUES ({THREAD_FIELDS_QUESTION});
        """, thread_values)

    for post_no in thread['thread']:
        # insert post thread relation in thread_replies table
        db_cursor.execute(f"""
            INSERT OR IGNORE INTO thread_posts ({THREAD_POSTS_FIELDS_COMMA})
            VALUES ({THREAD_POSTS_FIELDS_QUESTION});
            """, [thread['no'], post_no])

        # insert post info into posts table
        post_values = list()
        for post_field in POST_FIELDS:
            post_values.append(thread['thread'][post_no][post_field] if post_field in thread['thread'][post_no] else None)
        db_cursor.execute(f"""
            INSERT OR REPLACE INTO posts ({POST_FIELDS_COMMA})
            VALUES ({POST_FIELDS_QUESTION});
            """, post_values)

    # do this in another for loop so sql foreign key constraints are met
    for post_no in thread['thread']:
        for succ in thread['thread'][post_no]['succ']:
            # insert succ into post_replies table
            db_cursor.execute(f"""
                INSERT OR IGNORE INTO post_replies ({POST_REPLIES_FIELDS_COMMA})
                VALUES ({POST_REPLIES_FIELDS_QUESTION});
                """, [post_no, succ])

        # should be duplicates, but still
        for pred in thread['thread'][post_no]['pred']:
            # insert pred into post_replies table
            db_cursor.execute(f"""
                INSERT OR IGNORE INTO post_replies ({POST_REPLIES_FIELDS_COMMA})
                VALUES ({POST_REPLIES_FIELDS_QUESTION});
                """, [pred, post_no])

    db_connection.commit()
    return


# archive threads
def archive_threads(db_connection, thread_nos: list):
    db_cursor = db_connection.cursor()

    # set thread is_archived in threads table
    db_cursor.execute(f"""
        UPDATE threads
        SET is_archived = 1
        WHERE no in ({','.join(['?' for _ in thread_nos])});
        """, thread_nos)

    db_connection.commit()
    return


# 404 threads
def four_o_four_threads(db_connection, thread_nos: list):
    db_cursor = db_connection.cursor()

    # set thread is_404d in threads table
    db_cursor.execute(f"""
        UPDATE threads
        SET is_404d = 1
        WHERE no in ({','.join(['?' for _ in thread_nos])});
        """, thread_nos)

    db_connection.commit()
    return


# get non 404d yet threads
def non_four_o_four_threads(db_connection):
    db_cursor = db_connection.cursor()

    db_cursor.execute(f"""
        SELECT no
        FROM threads
        WHERE is_404d IS NULL
        """)

    db_output = [x[0] for x in db_cursor]
    return db_output


# delete very old threads and return their nos (so that their thumbnails can also be deleted!)
def delete_very_old_threads(db_connection, threads_keep_count: int):
    db_cursor = db_connection.cursor()

    db_cursor.execute(f"""
        DROP TABLE IF EXISTS threads_not_to_nuke;
        """)

    db_cursor.execute(f"""
        CREATE TABLE threads_not_to_nuke (
            no INTEGER PRIMARY KEY
        );
        """)

    db_cursor.execute(f"""
        INSERT INTO threads_not_to_nuke
        SELECT no
        FROM threads
        ORDER BY threads.last_modified DESC
        LIMIT {threads_keep_count};
        """)

    db_cursor.execute(f"""
        SELECT thread_posts.post_no
        FROM threads
        JOIN thread_posts
            ON thread_posts.thread_no = threads.no
        WHERE NOT EXISTS (
            SELECT NULL
            FROM threads_not_to_nuke
            WHERE threads_not_to_nuke.no = threads.no
        );
        """)
    # db_output = db_cursor.fetchall()

    post_nos_list = list()
    for post in db_cursor:
        post_nos_list.append(post[0])

    db_cursor.execute(f"""
        DELETE FROM threads
        WHERE NOT EXISTS (
            SELECT NULL
            FROM threads_not_to_nuke
            WHERE threads_not_to_nuke.no = threads.no
        );
        """)

    db_connection.commit()
    return post_nos_list


# get threads from db, only information from threads table
def get_threads_shallow(db_connection, thread_nos: list):
    db_cursor = db_connection.cursor()

    # query the threads table to get basic thread info
    db_cursor.execute(f"""
        SELECT *
        FROM threads
        WHERE threads.no in ({','.join(['?' for _ in thread_nos])});
        """, thread_nos)
    # db_output = db_cursor.fetchall()

    threads_dict = dict()
    THREAD_NO_INDEX = 0
    for each_row in db_cursor:
        # get thread info
        if each_row[THREAD_NO_INDEX] not in threads_dict:
            threads_dict[each_row[THREAD_NO_INDEX]] = dict()
            threads_dict[each_row[THREAD_NO_INDEX]]['thread'] = dict()
            for i in range(len(THREAD_FIELDS)):
                if each_row[THREAD_NO_INDEX + i] != None:
                    threads_dict[each_row[THREAD_NO_INDEX]][THREAD_FIELDS[i]] = each_row[THREAD_NO_INDEX + i]

    return threads_dict


# get threads from db
def get_threads(db_connection, thread_nos: list):
    # get threads shallow first
    threads_dict = get_threads_shallow(db_connection, thread_nos)

    db_cursor = db_connection.cursor()

    # get posts
    db_cursor.execute(f"""
        SELECT *
        FROM thread_posts
            JOIN posts
                ON thread_posts.post_no = posts.no
        WHERE thread_posts.thread_no in ({','.join(['?' for _ in thread_nos])});
        """, thread_nos)
    # db_output = db_cursor.fetchall()

    THREAD_NO_INDEX = 0
    POST_NO_INDEX = len(THREAD_POSTS_FIELDS)
    for each_row in db_cursor:
        # get post info
        if each_row[POST_NO_INDEX] not in threads_dict[each_row[THREAD_NO_INDEX]]['thread']:
            threads_dict[each_row[THREAD_NO_INDEX]]['thread'][each_row[POST_NO_INDEX]] = dict()
            threads_dict[each_row[THREAD_NO_INDEX]]['thread'][each_row[POST_NO_INDEX]]['succ'] = set()
            threads_dict[each_row[THREAD_NO_INDEX]]['thread'][each_row[POST_NO_INDEX]]['pred'] = set()
            for i in range(len(POST_FIELDS)):
                if each_row[POST_NO_INDEX + i] != None:
                    threads_dict[each_row[THREAD_NO_INDEX]]['thread'][each_row[POST_NO_INDEX]][POST_FIELDS[i]] = each_row[POST_NO_INDEX + i]

    # get pred and succ
    db_cursor.execute(f"""
        SELECT *
        FROM thread_posts
            JOIN post_replies
                ON thread_posts.post_no = post_replies.post_no
                    OR thread_posts.post_no = post_replies.reply_no
        WHERE thread_posts.thread_no in ({','.join(['?' for _ in thread_nos])});
        """, thread_nos)
    # db_output = db_cursor.fetchall()

    POST_NO_INDEX = 1
    PRED_NO_INDEX = len(THREAD_POSTS_FIELDS)
    SUCC_NO_INDEX = len(THREAD_POSTS_FIELDS) + 1
    for each_row in db_cursor:
        # don't check for duplicates since db has unique condition
        if each_row[PRED_NO_INDEX] != each_row[POST_NO_INDEX] and each_row[PRED_NO_INDEX] != None:
            # sometimes there might be references from an outside thread
            if each_row[POST_NO_INDEX] in threads_dict[each_row[THREAD_NO_INDEX]]['thread']:
                threads_dict[each_row[THREAD_NO_INDEX]]['thread'][each_row[POST_NO_INDEX]]['pred'].add(each_row[PRED_NO_INDEX])
        if each_row[SUCC_NO_INDEX] != each_row[POST_NO_INDEX] and each_row[SUCC_NO_INDEX] != None:
            # sometimes there might be references from an outside thread
            if each_row[POST_NO_INDEX] in threads_dict[each_row[THREAD_NO_INDEX]]['thread']:
                threads_dict[each_row[THREAD_NO_INDEX]]['thread'][each_row[POST_NO_INDEX]]['succ'].add(each_row[SUCC_NO_INDEX])

    # convert succ and pred sets to lists
    for each_thread_no, each_thread in threads_dict.items():
        if 'thread' in each_thread:
            for each_post_no, each_post in each_thread['thread'].items():
                each_post['succ'] = list(each_post['succ'])
                each_post['pred'] = list(each_post['pred'])

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
    # db_output = db_cursor.fetchall()
    db_output = [x[0] for x in db_cursor]
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
    # db_output = db_cursor.fetchall()
    db_output = [x[0] for x in db_cursor]
    return db_output


# custom function to get threads
def get_thread_nos_custom_1(db_connection, reply_min_count: int, thread_count: int):
    db_cursor = db_connection.cursor()
    db_cursor.execute(f"""
        SELECT no
        FROM
        (
            SELECT no, replies
            FROM threads
            WHERE replies > {reply_min_count}
            ORDER BY last_modified DESC
            LIMIT {thread_count}
        )
        ORDER BY replies DESC;
        """)
    # db_output = db_cursor.fetchall()
    db_output = [x[0] for x in db_cursor]
    return db_output


# custom function to get threads
def get_thread_nos_custom_2(db_connection, last_modified_limit: int, thread_count: int):
    db_cursor = db_connection.cursor()
    db_cursor.execute(f"""
        SELECT no
        FROM
        (
            SELECT no, last_modified
            FROM threads
            WHERE last_modified > {last_modified_limit}
            ORDER BY replies DESC
            LIMIT {thread_count}
        )
        ORDER BY last_modified DESC;
        """)
    # db_output = db_cursor.fetchall()
    db_output = [x[0] for x in db_cursor]
    return db_output


def startup_boards_db(db_connection):
    # enable foreign keys
    db_connection.execute('''
    PRAGMA foreign_keys = ON;
    ''')

    # create tables if they didn't already exist

    db_connection.execute('''
    CREATE TABLE IF NOT EXISTS threads (
        no INTEGER PRIMARY KEY,

        last_modified INTEGER,
        replies INT,

        sub TEXT,
        com TEXT,
        thumbnail BLOB,

        images INT,

        is_archived INT,
        is_404d INT
    );
    ''')

    db_connection.execute('''
    CREATE INDEX IF NOT EXISTS threads_indexed_by_no
    ON threads (no);
    ''')

    db_connection.execute('''
    CREATE INDEX IF NOT EXISTS threads_indexed_by_last_modified
    ON threads (last_modified);
    ''')

    db_connection.execute('''
    CREATE TABLE IF NOT EXISTS thread_posts (
        thread_no INTEGER,
        post_no INTEGER,
        PRIMARY KEY (thread_no, post_no),
        UNIQUE (post_no),
        FOREIGN KEY (thread_no) REFERENCES threads (no) ON DELETE CASCADE
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
        country_name TEXT,

        FOREIGN KEY (no) REFERENCES thread_posts (post_no) ON DELETE CASCADE
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
        PRIMARY KEY (post_no, reply_no),
        FOREIGN KEY (post_no) REFERENCES posts (no) ON DELETE CASCADE,
        FOREIGN KEY (reply_no) REFERENCES posts (no) ON DELETE CASCADE
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

    # for updating old versions
    try:
        db_connection.execute(f"""
            ALTER TABLE threads
            ADD images INT;
            """)
        db_connection.commit()
    except Exception as e:
        # we don't really care
        pass

    try:
        db_connection.execute(f"""
            ALTER TABLE threads
            ADD is_archived INT;
            """)
        db_connection.commit()
    except Exception as e:
        # we don't really care
        pass

    try:
        db_connection.execute(f"""
            ALTER TABLE threads
            ADD is_404d INT;
            """)
        db_connection.commit()
    except Exception as e:
        # we don't really care
        pass

    # alter table to add foreign keys doesn't work in sqlite

    # try:
    #     db_connection.execute(f"""
    #         ALTER TABLE thread_posts
    #         ADD CONSTRAINT FOREIGN KEY (thread_no) REFERENCES threads (no) ON DELETE CASCADE;
    #         """)
    #     db_connection.commit()
    # except Exception as e:
    #     # we don't really care
    #     pass

    # try:
    #     db_connection.execute(f"""
    #         ALTER TABLE posts
    #         ADD CONSTRAINT FOREIGN KEY (no) REFERENCES thread_posts (post_no) ON DELETE CASCADE;
    #         """)
    #     db_connection.commit()
    # except Exception as e:
    #     # we don't really care
    #     pass

    # try:
    #     db_connection.execute(f"""
    #         ALTER TABLE post_replies
    #         ADD CONSTRAINT FOREIGN KEY (post_no) REFERENCES posts (no) ON DELETE CASCADE,
    #             CONSTRAINT FOREIGN KEY (reply_no) REFERENCES posts (no) ON DELETE CASCADE;
    #         """)
    #     db_connection.commit()
    # except Exception as e:
    #     # we don't really care
    #     pass

    return


if __name__ == '__main__':
    pass