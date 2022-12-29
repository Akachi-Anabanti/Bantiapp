from . import fd
from flask import current_app, request, jsonify
from flask import render_template
import uuid
from app import pusher


@fd.route("/feeds")
def feed():
    return render_template("feed.html")


@fd.route("/quick")
def quick():
    return render_template("index.html")


@fd.route("/post", methods=["POST"])
def addPost():
    data = {
        "id": f"post-{uuid.uuid4().hex}",
        "content": request.form.get("content"),
        "title": request.form.get("title"),
        "status": "active",
        "event_name": "created",
    }
    pusher.trigger("blog", "post-added", data)
    return jsonify(data)


@fd.route("/post/<id>", methods=["PUT", "DELETE"])
def updatePost(id):
    data = {
        "id": id,
    }
    if request.method == "DELETE":
        data["event_name"] = ("deleted",)
        pusher.trigger("blog", "post-deleted", data)
    else:
        data["event_name"] = "deactivated"
        pusher.trigger("blog", "post-deactivated", data)

    return jsonify(data)
