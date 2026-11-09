import requests
import json

BASE_URL = "http://127.0.0.1:5000/api/v1/tasks"


def print_response(name, response):
    """Красиво выводим ответ"""
    print(f"\n{'='*60}")
    print(f"📋 {name}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")


# 1. ✅ GET все задачи (пейджинация, макс 10)
print("🔍 ТЕСТИРОВАНИЕ REST API")
response1 = requests.get(BASE_URL)
print_response("1. GET все задачи", response1)


# 2. ✅ GET с фильтрами
response2 = requests.get(BASE_URL, params={"status": "pending", "priority": "high"})
print_response("2. GET с фильтрами (status=pending&priority=high)", response2)

# 3. ✅ Поиск
response3 = requests.get(BASE_URL, params={"query": "Beautiful"})
print_response("3. Поиск по 'Beautiful'", response3)

# 4. ✅ Сортировка
response4 = requests.get(BASE_URL, params={"sort": "-priority"})
print_response("4. Сортировка по приоритету DESC", response4)

# 5. ✅ Пейджинация
response5 = requests.get(BASE_URL, params={"page": 1, "per_page": 5})
print_response("5. Пейджинация (page=1, per_page=5)", response5)

# 6. ✅ Создать задачу POST
new_task = {"title": "Тест", "description": "Лабораторная работа"}
headers = {"Content-Type": "application/json"}
response6 = requests.post(BASE_URL, json=new_task, headers=headers)
print_response("6. Создать задачу POST", response6)
new_task_id = response6.json().get("id", 999)

# 7. ✅ GET одна задача
response7 = requests.get(f"{BASE_URL}/{new_task_id}")
print_response(f"7. GET задача #{new_task_id}", response7)

# 8. ✅ PATCH (частичное обновление)
patch_data = {"status": "in_progress"}
response8 = requests.patch(
    f"{BASE_URL}/{new_task_id}", json=patch_data, headers=headers
)
print_response("8. PATCH (status=in_progress)", response8)

# # 9. ✅ PUT (полное обновление)
# put_data = {
#     "title": "Обновлено",
#     "description": "Полное обновление",
#     "status": "completed",
# }
# response9 = requests.put(f"{BASE_URL}/{new_task_id}", json=put_data, headers=headers)
# print_response("9. PUT (полное обновление)", response9)

# 10. ✅ DELETE (soft delete)
response10 = requests.delete(f"{BASE_URL}/{new_task_id}")
print_response("10. DELETE (soft delete)", response10)

# Проверка количества задач после удаления
response_final = requests.get(BASE_URL)
tasks_count = len(response_final.json().get("tasks", []))
print(f"\n🎉 ИТОГО: {tasks_count} активных задач (макс. 10) ✅")
