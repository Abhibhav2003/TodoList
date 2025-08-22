from flask import Flask, render_template, request, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from uuid import uuid4

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todos.db'
db = SQLAlchemy(app)

# --- Model ---
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(64), nullable=False)
    task = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False)

# --- Helpers ---
def _get_uid():
    return request.cookies.get("user_id") or str(uuid4())

def _with_cookie(resp, uid):
    if not request.cookies.get("user_id"):
        resp.set_cookie("user_id", uid, max_age=60*60*24*365*2, httponly=True, samesite="Lax")
    return resp

# --- Routes ---
@app.route("/")
def index():
    uid = _get_uid()
    todos = Todo.query.filter_by(uid=uid).all()
    resp = make_response(render_template("index.html", todos=todos))
    return _with_cookie(resp, uid)

@app.route("/add", methods=["POST"])
def add():
    uid = _get_uid()
    task = (request.form.get("todo") or "").strip()
    if task:
        db.session.add(Todo(uid=uid, task=task))
        db.session.commit()
    resp = make_response(redirect(url_for("index")))
    return _with_cookie(resp, uid)

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    uid = _get_uid()
    todo = Todo.query.filter_by(id=id, uid=uid).first_or_404()
    if request.method == "POST":
        todo.task = request.form["todo"]
        db.session.commit()
        resp = make_response(redirect(url_for("index")))
        return _with_cookie(resp, uid)
    resp = make_response(render_template("edit.html", todo=todo))
    return _with_cookie(resp, uid)

@app.route("/check/<int:id>")
def check(id):
    uid = _get_uid()
    todo = Todo.query.filter_by(id=id, uid=uid).first_or_404()
    todo.done = not todo.done
    db.session.commit()
    resp = make_response(redirect(url_for("index")))
    return _with_cookie(resp, uid)

@app.route("/delete/<int:id>")
def delete(id):
    uid = _get_uid()
    todo = Todo.query.filter_by(id=id, uid=uid).first_or_404()
    db.session.delete(todo)
    db.session.commit()
    resp = make_response(redirect(url_for("index")))
    return _with_cookie(resp, uid)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)