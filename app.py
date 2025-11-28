# app.py
import os
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
)
from models import db, Topic, Image
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS



def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "change-me-in-production"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
        BASE_DIR, "knowledge.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "static/uploads")
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB per file

    db.init_app(app)

    with app.app_context():
        db.create_all()

    # ---------- Web routes ----------

    @app.route("/")
    def index():
        """Main page: search box, topic list, detail pane."""
        return render_template("index.html")

    @app.route("/topics/new", methods=["GET", "POST"])
    def create_topic():
        if request.method == "POST":
            title = (request.form.get("title") or "").strip()
            body = (request.form.get("body") or "").strip()

            errors = []
            if not title:
                errors.append("Title is required.")
            if not body:
                errors.append("Body is required.")

            if errors:
                for e in errors:
                    flash(e, "error")
                return render_template(
                    "topic_form.html",
                    mode="create",
                    topic={"title": title, "body": body},
                )

            topic = Topic(title=title, body=body)
            db.session.add(topic)
            db.session.flush()  # Flush to get topic.id assigned
            
            # Ensure upload folder exists
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            
            files = request.files.getlist("images")
            for index, file in enumerate(files):
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    file.save(save_path)

                    # Get title for this image if provided
                    title_key = f"image_title_new_{index}"
                    image_title = request.form.get(title_key, "").strip()
                    
                    img = Image(topic_id=topic.id, filename=filename, title=image_title)
                    db.session.add(img)
            db.session.commit()
            flash("Topic created successfully.", "success")
            return redirect(url_for("index"))

        return render_template("topic_form.html", mode="create", topic=None)

    @app.route("/topics/<int:topic_id>/edit", methods=["GET", "POST"])
    def edit_topic(topic_id):
        topic = Topic.query.get_or_404(topic_id)

        if request.method == "POST":
            title = (request.form.get("title") or "").strip()
            body = (request.form.get("body") or "").strip()

            errors = []
            if not title:
                errors.append("Title is required.")
            if not body:
                errors.append("Body is required.")

            if errors:
                for e in errors:
                    flash(e, "error")
                # Re-render form with user-entered values
                topic.title = title
                topic.body = body
                return render_template("topic_form.html", mode="edit", topic=topic)

            topic.title = title
            topic.body = body

            for img in topic.images:
                title_key = f"image_title_{img.id}"
                delete_key = f"delete_image_{img.id}"

                # ✓ Update image title
                if title_key in request.form:
                    img.title = request.form.get(title_key, "").strip()

                # ✓ Delete image file + DB entry
                if delete_key in request.form:
                    try:
                        os.remove(os.path.join(app.config["UPLOAD_FOLDER"], img.filename))
                    except FileNotFoundError:
                        pass
                    db.session.delete(img)

            # Ensure upload folder exists
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            
            files = request.files.getlist("images")
            for index, file in enumerate(files):
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    file.save(save_path)

                    # Get title for this image if provided
                    title_key = f"image_title_new_{index}"
                    image_title = request.form.get(title_key, "").strip()
                    
                    img = Image(topic_id=topic.id, filename=filename, title=image_title)
                    db.session.add(img)

            db.session.commit()
            flash("Topic updated successfully.", "success")
            return redirect(url_for("index"))

        return render_template("topic_form.html", mode="edit", topic=topic)

    @app.route("/topics/<int:topic_id>/delete", methods=["POST"])
    def delete_topic(topic_id):
        topic = Topic.query.get_or_404(topic_id)

        # 1. Delete image FILES (not handled by SQLAlchemy)
        for img in list(topic.images):
            try:
                os.remove(os.path.join(app.config["UPLOAD_FOLDER"], img.filename))
            except FileNotFoundError:
                pass

        # 2. Delete the topic (this cascades DB image deletes)
        db.session.delete(topic)
        db.session.commit()

        # 3. AJAX delete support
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": True})

        flash("Topic deleted successfully.", "success")
        return redirect(url_for("index"))


    # ---------- API routes ----------

    @app.route("/api/topics")
    def api_topics():
        """Return filtered list of topics (for search + list)."""
        q = (request.args.get("q") or "").strip().lower()
        query = Topic.query

        if q:
            query = query.filter(Topic.title.ilike(f"%{q}%"))

        topics = query.order_by(Topic.title.asc()).all()
        return jsonify([t.to_summary_dict() for t in topics])

    @app.route("/api/topics/<int:topic_id>")

    def api_topic_detail(topic_id):
        topic = Topic.query.get_or_404(topic_id)

        return jsonify({
            **topic.to_detail_dict(),
            "images": [
                {
                    "id": img.id,
                    "title": img.title,
                    "url": url_for('static', filename='uploads/' + img.filename),
                }
                for img in topic.images
            ]
        })

    return app


if __name__ == "__main__":
    app = create_app()
    # For local development
    app.run(debug=True)
