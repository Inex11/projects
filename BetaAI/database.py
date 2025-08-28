import oracledb


class Database:
    """Methods for working with the database."""

    def __init__(self, user, password, dsn):
        self._connection = oracledb.connect(
            user=user,
            password=password,
            dsn=dsn
        )

        self._cursor = self._connection.cursor()

    def add_question(self, question, answer, question_embedding):
        """Add question information into the database."""

        arr_t = self._connection.gettype("FLOAT32_ARRAY") # Array type
        arr_obj = arr_t.newobject() # array object

        # add a question embedding
        arr_obj.extend([float(num) for num in question_embedding])
        self._cursor.execute(
            """
                SELECT MIN(expected_id)
                FROM (
                SELECT ROW_NUMBER() OVER (ORDER BY faq_id) AS expected_id,
                        faq_id
                FROM faq
                ) t
                WHERE t.faq_id <> t.expected_id
            """
        )

        faq_id = self._cursor.fetchone()[0]
        if faq_id is not None: faq_id = int(faq_id)
        else:
            self._cursor.execute(
                "SELECT NVL(MAX(faq_id), 0) + 1 FROM faq"
            )
            faq_id = self._cursor.fetchone()[0]

        self._cursor.execute(
            """
                INSERT INTO faq (faq_id, question, answer, question_embedding)
                VALUES (:id, :q, :a, :qe)
            """,
            {
                'id': faq_id,
                'q': question,
                'a': answer,
                'qe': arr_obj
            }
        )
        
        self._connection.commit()

    def get_question(self, faq_id, parameter=1):
        """
        Get a question info from the database by ID.
        You can use the second parameter to get exactly what you want:
        Use 0 for id, 1 for question, 2 for answer and 3 for embedding.
        """

        self._cursor.execute(
            """
                SELECT * FROM faq
                WHERE faq_id = :id
            """,
            {
                'id': faq_id
            }
        )
        question = self._cursor.fetchone()

        if parameter == 3: return [num for num in question[3]]

        return question[parameter]

    def delete_question(self, faq_id):
        """Delete a question from the database by ID."""
        
        self._cursor.execute(
            """
                DELETE FROM faq
                WHERE faq_id = :id
            """,
            {
                'id': faq_id
            }
        )

        self._connection.commit()

    # def find(self, question, amount):
    #     """Return amount of questions similar to the your question."""

    #     self._cursor.execute(
    #         """
    #             SELECT faq_id, question
    #                 UTL_MATCH.JARO_WIN
    #         """
    #     )