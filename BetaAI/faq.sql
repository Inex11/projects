-- Type for storing an embedding
CREATE TYPE FLOAT32_ARRAY AS VARRAY(3072) OF BINARY_FLOAT;

CREATE TABLE faq (
    faq_id NUMBER(7, 0) CONSTRAINT faq_id_pk PRIMARY KEY,
    question VARCHAR2(150) NOT NULL,
    answer VARCHAR2(500) NOT NULL,
    question_embedding FLOAT32_ARRAY NOT NULL
)
VARRAY question_embedding STORE AS BASICFILE LOB;