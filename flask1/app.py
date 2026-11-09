import codecs
from flask import Flask, jsonify, request

app = Flask(__name__)

VALID_STATUSES = ["cancelled", "completed", "in_progress", "pending"]
VALID_PRIORITIES = ["high", "low", "medium"]

tasks_db = []


def initialize_db():
    """Инициализация базы данных строками из Zen of Python с циклом статусов и приоритетов"""
    import this

    zen_encoded = this.s
    zen_text = codecs.decode(zen_encoded, "rot_13")

    lines = [line.strip() for line in zen_text.split("\n") if line.strip()]

    statuses_cycle = ["cancelled", "completed", "in_progress", "pending"]
    priorities_cycle = ["high", "low", "medium"]

    for idx, line in enumerate(lines, start=1):
        status_val = statuses_cycle[(idx - 1) % len(statuses_cycle)]
        priority_val = priorities_cycle[(idx - 1) % len(priorities_cycle)]

        task_data = {
            "id": idx,
            "title": "Zen of Python",
            "description": line,
            "status": status_val,
            "priority": priority_val,
        }
        tasks_db.append(task_data)


def get_tasks_lst():
    """Вспомогательная функция для получения списка задач"""
    try:
        query = request.args.get("query", default=None, type=str)
        order = request.args.get("order", default="id", type=str)
        offset = request.args.get("offset", default=0, type=int)
    except RuntimeError:
        query, order, offset = None, "id", 0

    result = tasks_db.copy()

    if query:
        q_low = query.lower()
        result = [
            t
            for t in result
            if q_low in t["title"].lower() or q_low in t["description"].lower()
        ]

    reverse = order.startswith("-")
    sort_field = order[1:] if reverse else order
    if sort_field not in ["id", "title", "description", "status", "priority"]:
        sort_field = "id"

    result.sort(key=lambda x: x[sort_field], reverse=reverse)
    paginated_result = result[offset : offset + 10]

    try:
        return jsonify({"tasks": paginated_result})
    except RuntimeError:
        return {"tasks": paginated_result}


@app.route("/api/v1/tasks", methods=["GET"])
def get_tasks(task_id=None):
    """Универсальная функция для получения списка или одной задачи по ID"""
    if task_id is not None:
        try:
            numeric_id = int(task_id)
        except (ValueError, TypeError):
            numeric_id = task_id

        for task in tasks_db:
            if task["id"] == numeric_id:
                try:
                    return jsonify(task), 200
                except RuntimeError:
                    return task
        try:
            return jsonify({"error": "Задача не найдена"}), 404
        except RuntimeError:
            return {"error": "Задача не найдена"}

    return get_tasks_lst()


@app.route("/api/v1/tasks/<task_id>", methods=["GET"])
def get_single_task_endpoint(task_id):
    return get_tasks(task_id)


@app.route("/api/v1/tasks", methods=["POST"])
def create_task():
    try:
        data = request.get_json(silent=True)
    except RuntimeError:
        data = None

    if data is None or data == {}:
        try:
            return jsonify({"error": "Отсутствуют данные JSON"}), 400
        except RuntimeError:
            return {"error": "Отсутствуют данные JSON"}

    if "title" not in data:
        try:
            return jsonify({"error": "Пропущен обязательный параметр `title`"}), 400
        except RuntimeError:
            return {"error": "Пропущен обязательный параметр `title`"}

    if "description" not in data:
        try:
            return (
                jsonify({"error": "Пропущен обязательный параметр `description`"}),
                400,
            )
        except RuntimeError:
            return {"error": "Пропущен обязательный параметр `description`"}

    status_val = data.get("status", "pending")
    priority_val = data.get("priority", "medium")

    if status_val not in VALID_STATUSES:
        try:
            return jsonify({"error": "Поле `status` невалидно"}), 400
        except RuntimeError:
            return {"error": "Поле `status` невалидно"}

    if priority_val not in VALID_PRIORITIES:
        try:
            return jsonify({"error": "Поле `priority` невалидно"}), 400
        except RuntimeError:
            return {"error": "Поле `priority` невалидно"}

    new_id = max([t["id"] for t in tasks_db], default=0) + 1

    new_task = {
        "id": new_id,
        "title": data["title"],
        "description": data["description"],
        "status": status_val,
        "priority": priority_val,
    }

    tasks_db.append(new_task)
    try:
        return jsonify(new_task), 200
    except RuntimeError:
        return new_task


@app.route("/api/v1/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    try:
        numeric_id = int(task_id)
    except (ValueError, TypeError):
        numeric_id = task_id

    for task in tasks_db:
        if task["id"] == numeric_id:
            task["status"] = "cancelled"
            try:
                return jsonify(task), 200
            except RuntimeError:
                return task
    try:
        return jsonify({"error": "Задача не найдена"}), 404
    except RuntimeError:
        return {"error": "Задача не найдена"}


@app.route("/api/v1/tasks/<task_id>", methods=["PATCH"])
def update_task(task_id):
    try:
        numeric_id = int(task_id)
    except (ValueError, TypeError):
        numeric_id = task_id

    target_task = None
    for task in tasks_db:
        if task["id"] == numeric_id:
            target_task = task
            break

    if not target_task:
        try:
            return jsonify({"error": "Задача не найдена"}), 404
        except RuntimeError:
            return {"error": "Задача не найдена"}

    try:
        data = request.get_json(silent=True)
    except RuntimeError:
        data = None

    if data is None or data == {}:
        try:
            return jsonify({"error": "Отсутствуют данные JSON"}), 400
        except RuntimeError:
            return {"error": "Отсутствуют данные JSON"}

    if "status" in data and data["status"] not in VALID_STATUSES:
        try:
            return jsonify({"error": "Поле `status` невалидно"}), 400
        except RuntimeError:
            return {"error": "Поле `status` невалидно"}

    if "priority" in data and data["priority"] not in VALID_PRIORITIES:
        try:
            return jsonify({"error": "Поле `priority` невалидно"}), 400
        except RuntimeError:
            return {"error": "Поле `priority` невалидно"}

    for key in ["title", "description", "status", "priority"]:
        if key in data:
            target_task[key] = data[key]

    try:
        return jsonify(target_task), 200
    except RuntimeError:
        return target_task


if __name__ == "__main__":
    initialize_db()
    app.run(debug=True)
