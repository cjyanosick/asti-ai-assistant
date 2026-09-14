from storage import load_json, save_json

TASKS_FILE = "tasks.json"

def load_tasks():
    return load_json(TASKS_FILE, [])

def save_tasks(tasks):
    save_json(TASKS_FILE, tasks)

def add_task(text):
    tasks = load_tasks()
    next_id = max((t["id"] for t in tasks), default=0) + 1
    task = {"id": next_id, "text": text, "done": False}
    tasks.append(task)
    save_tasks(tasks)
    return task

def complete_task(task_id):
    tasks = load_tasks()

    for task in tasks:
        if task["id"] == task_id:
            task["done"] = True
            save_tasks(tasks)
            return True

    return False
