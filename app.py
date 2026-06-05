from datetime import datetime
from flask import Flask, render_template, request, redirect, session, send_from_directory, flash
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash 
from werkzeug.utils import secure_filename
import sqlite3
import os
import uuid


app = Flask(__name__)
app.secret_key = "dev"

UPLOAD_FOLDER = "uploads"

ALLOWED_EXTENSIONS = {
    "pdf", "doc", "docx", "txt",
    "mp3", "wav", "aiff", "flac", "m4a",
    "mp4", "mov", "avi", "mkv"
}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


def get_db_connection():
    conn = sqlite3.connect("composerhub.db")
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    if "user_id" in session:
        return redirect("/dashboard")
    return render_template("index.html")


@app.route("/new_project", methods=["GET", "POST"])
def new_project():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")

        if not title:
            flash("Missing project title")
            return redirect(request.referrer or "/dashboard")

        conn = get_db_connection()

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn.execute(
            """
            INSERT INTO projects (user_id, title, description, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (session["user_id"], title, description, created_at)
        )

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("new_project.html")


@app.route("/project/<int:project_id>/add_cue", methods=["POST"])
def add_cue(project_id):
    if "user_id" not in session:
        return redirect("/login")

    title = request.form.get("title")
    start_timecode = request.form.get("start_timecode")
    duration = request.form.get("duration")
    notes = request.form.get("notes")

    if not title:
        flash("Missing cue title")
        return redirect(request.referrer or "/dashboard")

    conn = get_db_connection()

    project = conn.execute(
        "SELECT * FROM projects WHERE id = ? AND user_id = ?",
        (project_id, session["user_id"])
    ).fetchone()

    if project is None:
        conn.close()
        flash("Project not found")
        return redirect("/dashboard")

    conn.execute(
        """
        INSERT INTO cues (project_id, title, start_timecode, duration, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (project_id, title, start_timecode, duration, notes)
    )

    conn.commit()
    conn.close()

    return redirect(f"/project/{project_id}")


@app.route("/cue/<int:cue_id>/status", methods=["POST"])
def update_cue_status(cue_id):
    if "user_id" not in session:
        return redirect("/login")

    new_status = request.form.get("status")

    conn = get_db_connection()

    cue = conn.execute(
        """
        SELECT cues.*, projects.user_id
        FROM cues
        JOIN projects ON cues.project_id = projects.id
        WHERE cues.id = ?
        """,
        (cue_id,)
    ).fetchone()

    if cue is None:
        conn.close()
        flash("Cue not found")
        return redirect("/dashboard")

    if cue["user_id"] != session["user_id"]:
        conn.close()
        flash("Unauthorized")
        return redirect("/dashboard")

    conn.execute(
        "UPDATE cues SET status = ? WHERE id = ?",
        (new_status, cue_id)
    )

    conn.commit()
    conn.close()

    return redirect(f"/project/{cue['project_id']}")


@app.route("/cue/<int:cue_id>/edit", methods=["GET", "POST"])
def edit_cue(cue_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()

    cue = conn.execute(
        """
        SELECT cues.*, projects.user_id
        FROM cues
        JOIN projects ON cues.project_id = projects.id
        WHERE cues.id = ?
        """,
        (cue_id,)
    ).fetchone()

    if cue is None:
        conn.close()
        flash("Cue not found")
        return redirect("/dashboard")

    if cue["user_id"] != session["user_id"]:
        conn.close()
        flash("Unauthorized")
        return redirect("/dashboard")

    if request.method == "POST":
        title = request.form.get("title")
        start_timecode = request.form.get("start_timecode")
        duration = request.form.get("duration")
        notes = request.form.get("notes")
        status = request.form.get("status")

        if not title:
            conn.close()
            flash("Missing cue title")
            return redirect(request.referrer or f"/project/{cue['project_id']}")

        conn.execute(
            """
            UPDATE cues
            SET title = ?, start_timecode = ?, duration = ?, notes = ?, status = ?
            WHERE id = ?
            """,
            (title, start_timecode, duration, notes, status, cue_id)
        )

        conn.commit()
        conn.close()

        return redirect(f"/project/{cue['project_id']}")

    conn.close()

    return render_template("edit_cue.html", cue=cue)





@app.route("/cue/<int:cue_id>/delete", methods=["POST"])
def delete_cue(cue_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()

    cue = conn.execute(
        """
        SELECT cues.*, projects.user_id
        FROM cues
        JOIN projects ON cues.project_id = projects.id
        WHERE cues.id = ?
        """,
        (cue_id,)
    ).fetchone()

    if cue is None:
        conn.close()
        flash("Cue not found")
        return redirect("/dashboard")

    if cue["user_id"] != session["user_id"]:
        conn.close()
        flash("Unauthorized")
        return redirect("/dashboard")

    project_id = cue["project_id"]

    conn.execute(
        "DELETE FROM cues WHERE id = ?",
        (cue_id,)
    )

    conn.commit()
    conn.close()

    return redirect(f"/project/{project_id}")




@app.route("/project/<int:project_id>")
def project(project_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()

    project = conn.execute(
        "SELECT * FROM projects WHERE id = ? AND user_id = ?",
        (project_id, session["user_id"])
    ).fetchone()

    if project is None:
        conn.close()
        flash("Project not found")
        return redirect("/dashboard")

    cues = conn.execute(
        """
        SELECT * FROM cues 
        WHERE project_id = ? 
        ORDER BY start_timecode ASC
        """,
        (project_id,)
    ).fetchall()

    total_cues = len(cues)
    done_cues = sum(1 for cue in cues if cue["status"] == "Done")

    if total_cues > 0:
        progress_percent = int((done_cues / total_cues) * 100)
    else:
        progress_percent = 0


    project_files = conn.execute(
        "SELECT * FROM files WHERE project_id = ? AND cue_id IS NULL ORDER BY uploaded_at DESC",
        (project_id,)
    ).fetchall()

    cue_files = conn.execute(
        "SELECT * FROM files WHERE project_id = ? AND cue_id IS NOT NULL ORDER BY uploaded_at DESC",
        (project_id,)
    ).fetchall()

    conn.close()

    return render_template(
    "project.html",
    project=project,
    cues=cues,
    project_files=project_files,
    cue_files=cue_files,
    total_cues=total_cues,
    done_cues=done_cues,
    progress_percent=progress_percent
)



@app.route("/project/<int:project_id>/edit", methods=["GET", "POST"])
def edit_project(project_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()

    project = conn.execute(
        "SELECT * FROM projects WHERE id = ? AND user_id = ?",
        (project_id, session["user_id"])
    ).fetchone()

    if project is None:
        conn.close()
        flash("Project not found")
        return redirect("/dashboard")

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")

        if not title:
            conn.close()
            flash("Missing project title")
            return redirect(request.referrer or f"/project/{project_id}")

        conn.execute(
            "UPDATE projects SET title = ?, description = ? WHERE id = ? AND user_id = ?",
            (title, description, project_id, session["user_id"])
        )

        conn.commit()
        conn.close()

        return redirect(f"/project/{project_id}")

    conn.close()

    return render_template("edit_project.html", project=project)


@app.route("/project/<int:project_id>/delete", methods=["POST"])
def delete_project(project_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()

    conn.execute(
        "DELETE FROM projects WHERE id = ? AND user_id = ?",
        (project_id, session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")


@app.route("/project/<int:project_id>/upload", methods=["POST"])
def upload_project_file(project_id):
    if "user_id" not in session:
        return redirect("/login")

    file = request.files.get("file")

    if not file or file.filename == "":
        flash("No file selected")
        return redirect(request.referrer or f"/project/{project_id}")

    if not allowed_file(file.filename):
        flash("File type not allowed")
        return redirect(request.referrer or f"/project/{project_id}")

    conn = get_db_connection()

    project = conn.execute(
        "SELECT * FROM projects WHERE id = ? AND user_id = ?",
        (project_id, session["user_id"])
    ).fetchone()

    if project is None:
        conn.close()
        flash("Project not found")
        return redirect("/dashboard")

    original_filename = secure_filename(file.filename)
    extension = original_filename.rsplit(".", 1)[1].lower()
    stored_filename = f"{uuid.uuid4().hex}_{original_filename}"

    file.save(os.path.join(app.config["UPLOAD_FOLDER"], stored_filename))

    conn.execute(
        """
        INSERT INTO files (project_id, cue_id, original_filename, stored_filename, file_type)
        VALUES (?, NULL, ?, ?, ?)
        """,
        (project_id, original_filename, stored_filename, extension)
    )

    conn.commit()
    conn.close()

    return redirect(f"/project/{project_id}")


@app.route("/cue/<int:cue_id>/upload", methods=["POST"])
def upload_cue_file(cue_id):
    if "user_id" not in session:
        return redirect("/login")

    file = request.files.get("file")

    if not file or file.filename == "":
        flash("No file selected")
        return redirect(request.referrer or f"/project/{cue['project_id']}")

    if not allowed_file(file.filename):
        flash("File type not allowed")
        return redirect(request.referrer or f"/project/{cue['project_id']}")

    conn = get_db_connection()

    cue = conn.execute(
        """
        SELECT cues.*, projects.user_id
        FROM cues
        JOIN projects ON cues.project_id = projects.id
        WHERE cues.id = ?
        """,
        (cue_id,)
    ).fetchone()

    if cue is None:
        conn.close()
        flash("Cue not found")
        return redirect("/dashboard")

    if cue["user_id"] != session["user_id"]:
        conn.close()
        flash("Unauthorized")
        return redirect("/dashboard")

    original_filename = secure_filename(file.filename)
    extension = original_filename.rsplit(".", 1)[1].lower()
    stored_filename = f"{uuid.uuid4().hex}_{original_filename}"

    file.save(os.path.join(app.config["UPLOAD_FOLDER"], stored_filename))

    conn.execute(
        """
        INSERT INTO files (project_id, cue_id, original_filename, stored_filename, file_type)
        VALUES (?, ?, ?, ?, ?)
        """,
        (cue["project_id"], cue_id, original_filename, stored_filename, extension)
    )

    conn.commit()
    conn.close()

    return redirect(f"/project/{cue['project_id']}")


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    if "user_id" not in session:
        return redirect("/login")

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename,
        as_attachment=False
    )


@app.route("/file/<int:file_id>/delete", methods=["POST"])
def delete_file(file_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()

    file = conn.execute(
        """
        SELECT files.*, projects.user_id
        FROM files
        JOIN projects ON files.project_id = projects.id
        WHERE files.id = ?
        """,
        (file_id,)
    ).fetchone()

    if file is None:
        conn.close()
        flash("File not found")
        return redirect("/dashboard")

    if file["user_id"] != session["user_id"]:
        conn.close()
        flash("Unauthorized")
        return redirect("/dashboard")

    project_id = file["project_id"]
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], file["stored_filename"])

    conn.execute(
        "DELETE FROM files WHERE id = ?",
        (file_id,)
    )

    conn.commit()
    conn.close()

    if os.path.exists(file_path):
        os.remove(file_path)

    return redirect(f"/project/{project_id}")



@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()

    projects = conn.execute(
        "SELECT * FROM projects WHERE user_id = ? ORDER BY created_at DESC",
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template("dashboard.html", projects=projects)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            flash("Missing username")
            return redirect(request.referrer or "/register")

        if not password:
            flash("Missing password")
            return redirect(request.referrer or "/register")

        if len(password) < 6:
            flash("Password must be at least 6 characters long")
            return redirect(request.referrer or "/register")

        if password != confirmation:
            flash("Passwords do not match")
            return redirect(request.referrer or "/register")
        

        hash = generate_password_hash(password)

        conn = get_db_connection()

        try:
            conn.execute(
                "INSERT INTO users (username, hash) VALUES (?, ?)",
                (username, hash)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            flash("Username already exists")
            return redirect(request.referrer or "/register")

        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        conn.close()

        session["user_id"] = user["id"]

        return redirect("/dashboard")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            flash("Missing username")
            return redirect("/login")

        if not password:
            flash("Missing password")
            return redirect("/login")

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        conn.close()

        if user is None or not check_password_hash(user["hash"], password):
            flash("Invalid username or password")
            return redirect("/login")

        session.clear()
        session["user_id"] = user["id"]

        return redirect("/dashboard")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)