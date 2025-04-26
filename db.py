# db.py

from os import getenv
from dotenv import load_dotenv
from pgvector.peewee import VectorField
from peewee import PostgresqlDatabase, Model, TextField, ForeignKeyField

# --- Step 1: Load environment variables
load_dotenv()

# --- Step 2: Initialize database
db = PostgresqlDatabase(
    getenv("POSTGRES_DB_NAME"),
    host=getenv("POSTGRES_DB_HOST"),
    port=int(getenv("POSTGRES_DB_PORT")),
    user=getenv("POSTGRES_DB_USER"),
    password=getenv("POSTGRES_DB_PASSWORD"),
)

# --- Step 3: Define Models
class Documents(Model):
    name = TextField()

    class Meta:
        database = db
        db_table = 'documents'

class Tags(Model):
    name = TextField()

    class Meta:
        database = db
        db_table = 'tags'

class DocumentTags(Model):
    document_id = ForeignKeyField(Documents, backref="document_tags", on_delete='CASCADE')
    tag_id = ForeignKeyField(Tags, backref="document_tags", on_delete='CASCADE')

    class Meta:
        database = db
        db_table = 'document_tags'

class DocumentInformationChunks(Model):
    document_id = ForeignKeyField(Documents, backref="document_information_chunks", on_delete='CASCADE')
    chunk = TextField()
    embedding = VectorField(dimensions=1536)  # Vector field with 1536 dimensions

    class Meta:
        database = db
        db_table = 'document_information_chunks'

# --- Step 4: Setup database
def initialize_database():
    try:
        db.connect()
        print("✅ Successfully connected to the database!")

        db.create_tables([Documents, Tags, DocumentTags, DocumentInformationChunks], safe=True)
        DocumentInformationChunks.add_index('embedding vector_cosine_ops', using='diskann')

        print("✅ DiskANN index added successfully!")

    except Exception as e:
        print("❌ Error during database setup:", str(e))

# --- Step 5: Utility Functions
def set_diskann_query_rescore(query_rescore: int):
    """Set DiskANN query rescore value."""
    db.execute_sql(
        "SET diskann.query_rescore = %s;",
        (query_rescore,)
    )
    print(f"✅ diskann.query_rescore set to {query_rescore}")

def set_openai_api_key():
    """Set OpenAI API key in the database session."""
    openai_api_key = getenv("OPENAI_API_KEY")
    if openai_api_key:
        db.execute_sql(
            "SET ai.openai_api_key = %s;",
            (openai_api_key,)
        )
        print("✅ OpenAI API key set successfully!")
    else:
        print("⚠️ Warning: OPENAI_API_KEY not found in environment variables.")

# --- Step 6: Main block (Optional for running separately)
if __name__ == "__main__":
    initialize_database()
