import sqlite3


thread_fields       = ['no', 'last_modified', 'replies', 'sub', 'com', 'thumbnail', 'images', 'is_archived', 'is_404d']
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
            INSERT OR IGNORE INTO thread_posts ({thread_posts_fields_comma})
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

    # do this in another for loop so sql foreign key constraints are met
    for post_no in thread['thread']:
        for succ in thread['thread'][post_no]['succ']:
            # insert succ into post_replies table
            db_cursor.execute(f"""
                INSERT OR IGNORE INTO post_replies ({post_replies_fields_comma})
                VALUES ({post_replies_fields_question});
                """, [post_no, succ])

        # should be duplicates, but still
        for pred in thread['thread'][post_no]['pred']:
            # insert pred into post_replies table
            db_cursor.execute(f"""
                INSERT OR IGNORE INTO post_replies ({post_replies_fields_comma})
                VALUES ({post_replies_fields_question});
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


# 404 a thread
def four_o_four_thread(db_connection, thread_no):
    db_cursor = db_connection.cursor()

    # set thread is_404d in threads table
    db_cursor.execute(f"""
        UPDATE threads
        SET is_404d = 1
        WHERE no = ?;
        """, thread_no)

    db_connection.commit()
    return


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
        SELECT no
        FROM threads
        WHERE NOT EXISTS (
            SELECT NULL
            FROM threads_not_to_nuke
            WHERE threads_not_to_nuke.no = threads.no
        );
        """)
    # db_output = db_cursor.fetchall()

    thread_nos_list = list()
    for thread in db_cursor:
        thread_nos_list.append(thread[0])

    db_cursor.execute(f"""
        DELETE FROM threads
        WHERE NOT EXISTS (
            SELECT NULL
            FROM threads_not_to_nuke
            WHERE threads_not_to_nuke.no = threads.no
        );
        """)

    db_connection.commit()
    return thread_nos_list


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
    for thread in db_cursor:
        threads_dict[thread[0]] = dict()
        for i in range(len(thread_fields)):
            if thread[i] != None:
                threads_dict[thread[0]][thread_fields[i]] = thread[i]

    return threads_dict


# get threads from db
def get_threads(db_connection, thread_nos: list):
    db_cursor = db_connection.cursor()

    # query the threads table to get basic thread info
    db_cursor.execute(f"""
        SELECT *
        FROM threads
            JOIN thread_posts
                ON threads.no = thread_posts.thread_no
            JOIN posts
                ON thread_posts.post_no = posts.no
            JOIN post_replies
                ON posts.no = post_replies.post_no
                    OR posts.no = post_replies.reply_no
        WHERE threads.no in ({','.join(['?' for _ in thread_nos])});
        """, thread_nos)
    # db_output = db_cursor.fetchall()

    threads_dict = dict()
    for thread in db_cursor:
        # get thread info
        thread_no_index = 0
        if thread[thread_no_index] not in threads_dict:
            threads_dict[thread[thread_no_index]] = dict()
            threads_dict[thread[thread_no_index]]['thread'] = dict()
            for i in range(len(thread_fields)):
                if thread[thread_no_index + i] != None:
                    threads_dict[thread[thread_no_index]][thread_fields[i]] = thread[thread_no_index + i]

        # get post info
        post_no_index = len(thread_fields) + len(thread_posts_fields)
        if thread[post_no_index] not in threads_dict[thread[thread_no_index]]['thread']:
            threads_dict[thread[thread_no_index]]['thread'][thread[post_no_index]] = dict()
            threads_dict[thread[thread_no_index]]['thread'][thread[post_no_index]]['succ'] = list()
            threads_dict[thread[thread_no_index]]['thread'][thread[post_no_index]]['pred'] = list()
            for i in range(len(post_fields)):
                if thread[post_no_index + i] != None:
                    threads_dict[thread[thread_no_index]]['thread'][thread[post_no_index]][post_fields[i]] = thread[post_no_index + i]

        # get pred and succ, without duplicate checking ("not in") since they are too expensive
        # on lists, besides there shouldn't be duplicates in the db. Instead just check if they are not post_no
        pred_no_index = len(thread_fields) + len(thread_posts_fields) + len(post_fields)
        succ_no_index = len(thread_fields) + len(thread_posts_fields) + len(post_fields) + 1
        if thread[pred_no_index] != thread[post_no_index] and thread[pred_no_index] != None:
            threads_dict[thread[thread_no_index]]['thread'][thread[post_no_index]]['pred'].append(thread[pred_no_index])
        if thread[succ_no_index] != thread[post_no_index] and thread[succ_no_index] != None:
            threads_dict[thread[thread_no_index]]['thread'][thread[post_no_index]]['succ'].append(thread[succ_no_index])

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