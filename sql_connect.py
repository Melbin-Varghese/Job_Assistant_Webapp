from flask import Flask, render_template, request, redirect, url_for

from db_connection import get_connection

app = Flask(__name__, template_folder="templates")

db=get_connection()
cur=db.cursor()

@app.route("/")
def home():
    return redirect(url_for("register"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form["email"]
    password = request.form["password"]

    cur.execute(
        "SELECT fullname FROM users WHERE email = %s AND password = %s",
        (email, password)
    )
    user = cur.fetchone()

    if user:
        return redirect(url_for("dashboard", name=user[0]))
    else:
        return "Invalid email or password"

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    try:
        fullname = request.form["fullname"]
        email = request.form["email"]
        password = request.form["password"]
        mobile = request.form["mobile"]
        work_status = request.form["work_status"]

        sql = """
        INSERT INTO users
        (fullname, email, password, mobile, work_status)
        VALUES (%s, %s, %s, %s, %s)
        """

        cur.execute(sql, (fullname, email, password, mobile, work_status))
        db.commit()

        return redirect(url_for("login"))
    
    except Exception as e:
        return f"Database Error: {e}"
    
@app.route("/dashboard")
def dashboard():
    name = request.args.get("name")
    return render_template("USER.html", name=name)

if __name__ == "__main__":
    app.run(debug=True, port=5001)