import os
import psycopg2

# ===== CONFIG =====
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
DATABASE_URL = os.getenv("DATABASE_PUBLIC_URL")  # ⚠️ ON UTILISE LA PUBLIC

# ===== CHECK VARIABLES =====
if not SERPAPI_KEY:
    raise Exception("❌ SERPAPI_KEY manquante !")

if not DATABASE_URL:
    raise Exception("❌ DATABASE_PUBLIC_URL manquante !")

print("✅ Variables OK")

# ===== DB CONNECTION =====
try:
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    cur = conn.cursor()
    print("✅ Connexion DB OK")
except Exception as e:
    print("❌ Erreur connexion DB :", e)
    raise

# ===== CREATE TABLE =====
try:
    cur.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id SERIAL PRIMARY KEY,
        name TEXT,
        company TEXT,
        email TEXT,
        linkedin TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    print("✅ Table créée")
except Exception as e:
    print("❌ Erreur création table :", e)
    raise

# ===== TEST INSERT =====
try:
    cur.execute("""
    INSERT INTO leads (name, company, email, linkedin)
    VALUES (%s, %s, %s, %s)
    """, ("Test User", "Test Company", "test@email.com", "https://linkedin.com"))
    
    conn.commit()
    print("✅ Insert OK")
except Exception as e:
    print("❌ Erreur insert :", e)
    raise

# ===== CLOSE =====
cur.close()
conn.close()

print("🚀 SCRIPT TERMINÉ SANS ERREUR")
