from flask import Flask, request, redirect, jsonify, session, url_for
from supabase import create_client, Client
from dotenv import load_dotenv
import os

app = Flask(__name__)
app.secret_key = "sua-chave-secreta"

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route("/")
def index():
    user = session.get("user")
    if user:
        return jsonify({"message": f"Bem-vindo, {user['email']}! Explore a história do automobilismo!"})
    return jsonify({"message": "Faça login para explorar a história do automobilismo!"})

@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    username = data.get("username")
    favorite_car = data.get("favorite_car")
    response = supabase.auth.sign_up({"email": email, "password": password})
    if response.user:
        supabase.table("profiles").insert({
            "id": response.user.id,
            "email": email,
            "username": username,
            "favorite_car": favorite_car
        }).execute()
        return jsonify({"message": "Conta criada com sucesso!"})
    return jsonify({"error": str(response.error)}), 400

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    response = supabase.auth.sign_in_with_password({"email": email, "password": password})
    if response.user:
        session["user"] = {"email": response.user.email, "id": response.user.id}
        return jsonify({"message": "Login realizado com sucesso!"})
    return jsonify({"error": str(response.error)}), 400

@app.route("/login/google")
def login_google():
    response = supabase.auth.sign_in_with_oauth({"provider": "google"})
    return redirect(response.url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if code:
        response = supabase.auth.get_user(code)
        if response.user:
            session["user"] = {"email": response.user.email, "id": response.user.id}
            supabase.table("profiles").upsert({
                "id": response.user.id,
                "email": response.user.email,
                "username": response.user.email.split("@")[0],
                "favorite_car": "Nenhum ainda"
            }).execute()
            return redirect(url_for("index"))
    return jsonify({"error": "Falha na autenticação com Google"}), 400

@app.route("/logout")
def logout():
    supabase.auth.sign_out()
    session.pop("user", None)
    return jsonify({"message": "Logout realizado com sucesso!"})

@app.route("/profile")
def profile():
    user = session.get("user")
    if not user:
        return jsonify({"error": "Faça login primeiro!"}), 401
    response = supabase.table("profiles").select("*").eq("id", user["id"]).execute()
    return jsonify(response.data)

if __name__ == "__main__":
    app.run(debug=True)

    #SQL Comandos para configurar o esquema do banco de dados

# CREATE TABLE profiles (
#   id UUID REFERENCES auth.users(id) PRIMARY KEY,
#   email TEXT NOT NULL,
#   username TEXT NOT NULL,
#   favorite_car TEXT,
#   created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
# );

# ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

# CREATE POLICY "Usuários veem seu próprio perfil" ON profiles
# FOR SELECT
# USING (auth.uid() = id);

# CREATE POLICY "Usuários criam seu próprio perfil" ON profiles
# FOR INSERT
# WITH CHECK (auth.uid() = id);

# CREATE POLICY "Usuários editam seu próprio perfil" ON profiles
# FOR UPDATE
# USING (auth.uid() = id);

# CREATE POLICY "Usuários deletam seu próprio perfil" ON profiles
# FOR DELETE
# USING (auth.uid() = id);

# CREATE TABLE cars (
#   id SERIAL PRIMARY KEY,
#   model TEXT NOT NULL,
#   year INTEGER NOT NULL,
#   manufacturer TEXT NOT NULL,
#   history TEXT,
#   created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
# );

# ALTER TABLE cars ENABLE ROW LEVEL SECURITY;

# CREATE POLICY "Todos podem ver carros" ON cars
# FOR SELECT
# USING (true);

# CREATE TABLE user_favorites (
#   user_id UUID REFERENCES profiles(id),
#   car_id INTEGER REFERENCES cars(id),
#   PRIMARY KEY (user_id, car_id),
#   created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
# );

# ALTER TABLE user_favorites ENABLE ROW LEVEL SECURITY;

# CREATE POLICY "Usuários gerenciam seus próprios favoritos" ON user_favorites
# FOR ALL
# WITH CHECK (auth.uid() = user_id);