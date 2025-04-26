# openai_client.py
import os
import psycopg2
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(verbose=True, override=True)

api_key = os.getenv("OPENAI_API_KEY")
db_name = os.getenv("POSTGRES_DB_NAME")
db_user = os.getenv("POSTGRES_DB_USER")
db_password = os.getenv("POSTGRES_DB_PASSWORD")
db_host = os.getenv("POSTGRES_DB_HOST")
db_port = os.getenv("POSTGRES_DB_PORT")

print("🔍 Environment Variables Loaded:")
print("OPENAI_API_KEY =", "✅ Loaded" if api_key else "❌ Missing")
print(f"Postgres: {db_user}@{db_host}:{db_port}/{db_name}")

try:
    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host,
        port=db_port
    )
    cursor = conn.cursor()
    print("✅ Connected to PostgreSQL database!")

    cursor.execute("SET ai.openai_api_key = %s;", (api_key,))
    print("✅ API key set in DB session.")

except Exception as e:
    print("❌ ERROR connecting to DB:", e)

finally:
    if conn:
        cursor.close()
        conn.close()
        print("🔒 Connection closed.")

client = OpenAI()
try:
    response = client.chat.completions.create(
        model="gpt-4o-2024-05-13",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"}
        ]
    )
    print("\n✅ OpenAI GPT Response:")
    print(response.choices[0].message.content)
except Exception as e:
    print("❌ ERROR testing OpenAI:", e)
