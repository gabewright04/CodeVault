from flask import Flask, render_template, request, jsonify
from database import engine, SessionLocal, get_db
import models
from datetime import datetime
import anthropic
import os

app = Flask(__name__)
models.Base.metadata.create_all(bind=engine)

LANGUAGE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".html": "HTML",
    ".css": "CSS",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".sql": "SQL",
    ".sh": "Shell",
    ".r": "R",
    ".md": "Markdown",
    ".json": "JSON",
    ".xml": "XML",
    ".yaml": "YAML",
    ".yml": "YAML",
}

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "your_api_key_here")

def get_ai_overview(filename, content, language):
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": f"In 2-3 sentences, give a plain English overview of what this {language} file does. Be concise and clear. File: {filename}\n\nCode:\n{content[:3000]}"
                }
            ]
        )
        return message.content[0].text
    except Exception as e:
        return f"AI overview unavailable: {str(e)}"

@app.route("/")
def index():
    db = SessionLocal()
    language = request.args.get("language", "")
    sort = request.args.get("sort", "newest")

    query = db.query(models.CodeFile)
    if language:
        query = query.filter(models.CodeFile.language == language)
    if sort == "oldest":
        query = query.order_by(models.CodeFile.date_imported.asc())
    else:
        query = query.order_by(models.CodeFile.date_imported.desc())

    files = query.all()
    languages = db.query(models.CodeFile.language).distinct().all()
    languages = [l[0] for l in languages]
    db.close()
    return render_template("index.html", files=files, languages=languages, selected_language=language, sort=sort)

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    notes = request.form.get("notes", "")

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    language = LANGUAGE_MAP.get(ext, "Unknown")
    content = file.read().decode("utf-8", errors="ignore")
    ai_overview = get_ai_overview(file.filename, content, language)

    db = SessionLocal()
    code_file = models.CodeFile(
        filename=file.filename,
        language=language,
        content=content,
        notes=notes,
        ai_overview=ai_overview,
        date_imported=datetime.utcnow()
    )
    db.add(code_file)
    db.commit()
    db.close()

    return jsonify({"success": True, "message": f"{file.filename} imported successfully!"})

@app.route("/file/<int:file_id>")
def view_file(file_id):
    db = SessionLocal()
    file = db.query(models.CodeFile).filter(models.CodeFile.id == file_id).first()
    db.close()
    if not file:
        return "File not found", 404
    return render_template("view.html", file=file)

@app.route("/file/<int:file_id>/delete", methods=["POST"])
def delete_file(file_id):
    db = SessionLocal()
    file = db.query(models.CodeFile).filter(models.CodeFile.id == file_id).first()
    if file:
        db.delete(file)
        db.commit()
    db.close()
    return jsonify({"success": True})

@app.route("/file/<int:file_id>/notes", methods=["POST"])
def update_notes(file_id):
    db = SessionLocal()
    file = db.query(models.CodeFile).filter(models.CodeFile.id == file_id).first()
    if file:
        file.notes = request.json.get("notes", "")
        db.commit()
    db.close()
    return jsonify({"success": True})

@app.route("/snippets")
def snippets():
    db = SessionLocal()
    tag_filter = request.args.get("tag", "")
    language_filter = request.args.get("language", "")
    search = request.args.get("search", "")

    query = db.query(models.Snippet)
    if tag_filter:
        query = query.filter(models.Snippet.tags.contains(tag_filter))
    if language_filter:
        query = query.filter(models.Snippet.language == language_filter)
    if search:
        query = query.filter(
            models.Snippet.title.contains(search) |
            models.Snippet.description.contains(search) |
            models.Snippet.code.contains(search)
        )

    all_snippets_list = query.order_by(models.Snippet.date_saved.desc()).all()
    all_tags = set()
    for s in db.query(models.Snippet).all():
        if s.tags:
            for t in s.tags.split(","):
                t = t.strip()
                if t:
                    all_tags.add(t)

    languages = db.query(models.Snippet.language).distinct().all()
    languages = [l[0] for l in languages]
    db.close()

    return render_template("snippets.html",
        snippets=all_snippets_list,
        all_tags=sorted(all_tags),
        languages=languages,
        selected_tag=tag_filter,
        selected_language=language_filter,
        search=search
    )

@app.route("/snippets/save", methods=["POST"])
def save_snippet():
    data = request.json
    db = SessionLocal()
    snippet = models.Snippet(
        title=data.get("title", "Untitled Snippet"),
        description=data.get("description", ""),
        code=data.get("code", ""),
        language=data.get("language", "Unknown"),
        tags=data.get("tags", ""),
        source_file=data.get("source_file", ""),
        source_file_id=data.get("source_file_id"),
        date_saved=datetime.utcnow()
    )
    db.add(snippet)
    db.commit()
    snippet_id = snippet.id
    db.close()
    return jsonify({"success": True, "id": snippet_id})

@app.route("/snippets/<int:snippet_id>/delete", methods=["POST"])
def delete_snippet(snippet_id):
    db = SessionLocal()
    snippet = db.query(models.Snippet).filter(models.Snippet.id == snippet_id).first()
    if snippet:
        db.delete(snippet)
        db.commit()
    db.close()
    return jsonify({"success": True})

@app.route("/snippets/<int:snippet_id>/edit", methods=["POST"])
def edit_snippet(snippet_id):
    data = request.json
    db = SessionLocal()
    snippet = db.query(models.Snippet).filter(models.Snippet.id == snippet_id).first()
    if snippet:
        snippet.title = data.get("title", snippet.title)
        snippet.description = data.get("description", snippet.description)
        snippet.tags = data.get("tags", snippet.tags)
        db.commit()
    db.close()
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(debug=True)