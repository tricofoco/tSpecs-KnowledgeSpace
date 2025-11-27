# models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Topic(db.Model):
    __tablename__ = "topics"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # ⭐ Correct relationship: no cascade deletes on parent loss,
    #   topic remains even if all images are deleted
    images = db.relationship(
        "Image",
        backref=db.backref("topic", lazy=True),
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def to_summary_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "updated_at": self.updated_at.isoformat(),
        }

    def to_detail_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

class Image(db.Model):
    __tablename__ = "images"

    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(
        db.Integer,
        db.ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=False
    )
    filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
