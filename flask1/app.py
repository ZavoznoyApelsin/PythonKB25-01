import codecs
from flask import Flask, jsonify, request

app = Flask(__name__)

VALID_STATUSES = ["cancelled", "completed", "in_progress", "pending"]
VALID_PRIORITIES = ["high", "low", "medium"]

tasks_db = []

def initialize_db():
    import this
    zen_encoded = this.s
    zen_text = codecs.decode(zen_encoded, 'rot_13')
    lines = [line.strip() for line in zen_text.split('\n') if line.strip()]
        
    tasks_db.clear()
        
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
            "priority": priority_val
        }
        tasks_db.append(task_data)


initialize_db()

@app.route('/api/v1/tasks', methods=['GET'])
def get_tasks_endpoint():
    query = request.args.get('query', default=None, type=str)
    sort_param = request.args.get('sort', default=None, type=str)
    order_param = request.args.get('order', default='id', type=str)
    order = sort_param if sort_param else order_param
    
    filter_status = request.args.get('status', default=None, type=str)
    filter_priority = request.args.get('priority', default=None, type=str)
    
    page = request.args.get('page', default=None, type=int)
    per_page = request.args.get('per_page', default=10, type=int)
    offset = request.args.get('offset', default=None, type=int)
    
    result = tasks_db.copy()
    
    if filter_status:
        result = [t for t in result if t["status"] == filter_status]
    if filter_priority:
        result = [t for t in result if t["priority"] == filter_priority]
    
    if query:
        q_low = query.lower()
        result = [t for t in result if q_low in t["title"].lower() or q_low in t["description"].lower()]
        
    reverse = False
    sort_field = order
    if order.startswith("-"):
        reverse = True
        sort_field = order[1:]
        
    valid_fields = ["id", "title", "description", "status", "priority"]
    if sort_field not in valid_fields:
        sort_field = "id"
        
    result.sort(key=lambda x: x[sort_field], reverse=reverse)
    
    if page is not None:
        start_idx = (page - 1) * per_page if page > 0 else 0
        end_idx = start_idx + per_page
    elif offset is not None:
        start_idx = offset
        end_idx = offset + 10
    else:
        start_idx = 0
        end_idx = 10
        
    paginated_result = result[start_idx:end_idx]
    return jsonify({"tasks": paginated_result}), 200

@app.route('/api/v1/tasks/<task_id>', methods=['GET'])
def get_single_task(task_id):
    try:
        numeric_id = int(task_id)
    except (ValueError, TypeError):
        numeric_id = task_id

    for task in tasks_db:
        if task["id"] == numeric_id:
            return jsonify(task), 200
            
    return jsonify({"error": "Задача не найдена"}), 404

@app.route('/api/v1/tasks', methods=['POST'])
def create_task():
    data = request.get_json(silent=True)
    if data is None or data == {}:
        return jsonify({"error": "Отсутствуют данные JSON"}), 400
    
    if "title" not in data:
        return jsonify({"error": "Пропущен обязательный параметр `title`"}), 400
    if "description" not in data:
        return jsonify({"error": "Пропущен обязательный параметр `description`"}), 400
        
    status_val = data.get("status", "pending")
    priority_val = data.get("priority", "medium")
    
    if status_val not in VALID_STATUSES:
        return jsonify({"error": "Поле `status` невалидно"}), 400
    if priority_val not in VALID_PRIORITIES:
        return jsonify({"error": "Поле `priority` невалидно"}), 400
        
    new_id = max([t["id"] for t in tasks_db], default=0) + 1
    new_task = {
        "id": new_id,
        "title": data["title"],
        "description": data["description"],
        "status": status_val,
        "priority": priority_val
    }
    tasks_db.append(new_task)
    return jsonify(new_task), 200

@app.route('/api/v1/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        numeric_id = int(task_id)
    except (ValueError, TypeError):
        numeric_id = task_id

    for task in tasks_db:
        if task["id"] == numeric_id:
            task["status"] = "cancelled"
            return jsonify(task), 200
            
    return jsonify({"error": "Задача не найдена"}), 404

@app.route('/api/v1/tasks/<task_id>', methods=['PATCH'])
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
        return jsonify({"error": "Задача не найдена"}), 404
        
    data = request.get_json(silent=True)
    if data is None or data == {}:
        return jsonify({"error": "Отсутствуют данные JSON"}), 400
    
    if "status" in data and data["status"] not in VALID_STATUSES:
        return jsonify({"error": "Поле `status` невалидно"}), 400
    if "priority" in data and data["priority"] not in VALID_PRIORITIES:
        return jsonify({"error": "Поле `priority` невалидно"}), 400
        
    for key in ["title", "description", "status", "priority"]:
        if key in data:
            target_task[key] = data[key]
            
    return jsonify(target_task), 200

if __name__ == '__main__':
    initialize_db()
    app.run(debug=True)
