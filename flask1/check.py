import requests

LONG_TITLE = "x" * 201

# ---------- снимок состояния до тестов (для восстановления) ----------
r = requests.get("http://localhost:5000/tasks", params={"per_page": 100})
assert r.status_code == 200, "сервер не отвечает на GET /tasks"
ids_before = {t["id"] for t in r.json()["items"]}
created_ids = []
print("=== Тесты Tasks API (http://localhost:5000) ===\n")

try:
    # ---------- 1. Корень: сервер жив, начальные значения на месте ----------
    r = requests.get("http://localhost:5000/")
    assert r.status_code == 200, f"GET / -> {r.status_code}, ожидался 200"
    assert r.json()["seed"] == len(ids_before), "seed не совпадает с числом задач"
    print("1. корень и seed ... ок")

    # ---------- 1.5. Подготовка: создаём 25 доп. задач для пагинации/сортировки ----------
    extra_titles = [
        "Alpha",
        "Bravo",
        "Charlie",
        "Delta",
        "Echo",
        "Foxtrot",
        "Golf",
        "Hotel",
        "India",
        "Juliet",
        "Kilo",
        "Lima",
        "Mike",
        "November",
        "Oscar",
        "Papa",
        "Quebec",
        "Romeo",
        "Sierra",
        "Tango",
        "Uniform",
        "Victor",
        "Whiskey",
        "X-ray",
        "Yankee",
    ]
    for i, title in enumerate(extra_titles):
        done = i % 3 == 0  # каждая третья — выполненная
        r = requests.post(
            "http://localhost:5000/tasks", json={"title": title, "done": done}
        )
        assert r.status_code == 201, f"подготовка: не удалось создать {title}"
        created_ids.append(r.json()["id"])

    # обновляем снимок после подготовки
    r = requests.get("http://localhost:5000/tasks", params={"per_page": 100})
    all_ids = {t["id"] for t in r.json()["items"]}
    assert len(all_ids) == len(ids_before) + len(
        extra_titles
    ), "ожидалось, что все доп. задачи созданы"
    print(f"1.5. подготовка: создано {len(extra_titles)} задач ... ок")

    # ---------- 2. Список по умолчанию: обёртка с мета-информацией ----------
    r = requests.get("http://localhost:5000/tasks")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == len(all_ids)
    assert body["per_page"] == 10
    assert body["pages"] > 1, "при 30+ задачах страниц должно быть > 1"
    assert len(body["items"]) == 10, "на первой странице должно быть 10 элементов"
    print("2. список по умолчанию ... ок")

    # ---------- 3. Пейджинация ----------
    r = requests.get("http://localhost:5000/tasks", params={"page": 1, "per_page": 5})
    assert r.status_code == 200
    assert len(r.json()["items"]) == 5

    r = requests.get("http://localhost:5000/tasks", params={"page": 2, "per_page": 5})
    assert r.status_code == 200
    assert len(r.json()["items"]) == 5

    # страницы не должны пересекаться
    page1_ids = {
        t["id"]
        for t in requests.get(
            "http://localhost:5000/tasks", params={"page": 1, "per_page": 5}
        ).json()["items"]
    }
    page2_ids = {
        t["id"]
        for t in requests.get(
            "http://localhost:5000/tasks", params={"page": 2, "per_page": 5}
        ).json()["items"]
    }
    assert not (page1_ids & page2_ids), "страницы не должны пересекаться"

    # за пределами — не ошибка, а пусто
    r = requests.get("http://localhost:5000/tasks", params={"page": 999, "per_page": 5})
    assert r.status_code == 200
    assert r.json()["items"] == []

    # невалидные параметры -> 400
    r = requests.get("http://localhost:5000/tasks", params={"page": 0})
    assert r.status_code == 400
    r = requests.get("http://localhost:5000/tasks", params={"page": -1})
    assert r.status_code == 400
    r = requests.get("http://localhost:5000/tasks", params={"page": "abc"})
    assert r.status_code == 400
    r = requests.get("http://localhost:5000/tasks", params={"per_page": 0})
    assert r.status_code == 400
    r = requests.get("http://localhost:5000/tasks", params={"per_page": 101})
    assert r.status_code == 400
    r = requests.get("http://localhost:5000/tasks", params={"per_page": "abc"})
    assert r.status_code == 400
    print("3. пейджинация ... ок")

    # ---------- 4. Сортировка: sort + order ----------
    # title asc
    r = requests.get(
        "http://localhost:5000/tasks",
        params={"sort": "title", "order": "asc", "per_page": 100},
    )
    assert r.status_code == 200
    titles = [t["title"] for t in r.json()["items"]]
    assert titles == sorted(titles), "список не отсортирован по title asc"

    # title desc
    r = requests.get(
        "http://localhost:5000/tasks",
        params={"sort": "title", "order": "desc", "per_page": 100},
    )
    titles_desc = [t["title"] for t in r.json()["items"]]
    assert titles_desc == sorted(
        titles_desc, reverse=True
    ), "список не отсортирован по title desc"

    # id asc
    r = requests.get(
        "http://localhost:5000/tasks",
        params={"sort": "id", "order": "asc", "per_page": 100},
    )
    ids_asc = [t["id"] for t in r.json()["items"]]
    assert ids_asc == sorted(ids_asc), "список не отсортирован по id asc"

    # id desc
    r = requests.get(
        "http://localhost:5000/tasks",
        params={"sort": "id", "order": "desc", "per_page": 100},
    )
    ids_desc = [t["id"] for t in r.json()["items"]]
    assert ids_desc == sorted(
        ids_desc, reverse=True
    ), "список не отсортирован по id desc"

    # created_at desc — самая свежая задача должна быть первой
    r = requests.get(
        "http://localhost:5000/tasks",
        params={"sort": "created_at", "order": "desc", "per_page": 1},
    )
    first_id = r.json()["items"][0]["id"]
    assert first_id == max(
        all_ids
    ), "последняя созданная должна быть первой в desc по created_at"

    # невалидные значения
    r = requests.get("http://localhost:5000/tasks", params={"sort": "foo"})
    assert r.status_code == 400
    r = requests.get("http://localhost:5000/tasks", params={"order": "up"})
    assert r.status_code == 400
    print("4. сортировка ... ок")

    # ---------- 5. Фильтры: done и поиск q ----------
    # done=true
    r = requests.get(
        "http://localhost:5000/tasks", params={"done": "true", "per_page": 100}
    )
    assert r.status_code == 200
    assert all(t["done"] for t in r.json()["items"])
    assert r.json()["total"] > 0
    assert r.json()["total"] < len(all_ids), "в seed+extra есть и выполненные, и нет"

    # done=false
    r = requests.get(
        "http://localhost:5000/tasks", params={"done": "false", "per_page": 100}
    )
    assert r.status_code == 200
    assert all(not t["done"] for t in r.json()["items"])

    # сумма done=true и done=false должна давать total
    total_done = requests.get(
        "http://localhost:5000/tasks", params={"done": "true", "per_page": 100}
    ).json()["total"]
    total_undone = requests.get(
        "http://localhost:5000/tasks", params={"done": "false", "per_page": 100}
    ).json()["total"]
    assert total_done + total_undone == len(
        all_ids
    ), "сумма done=true и done=false должна равняться total"

    # поиск q (регистронезависимо)
    r = requests.get("http://localhost:5000/tasks", params={"q": "alpha"})
    assert r.status_code == 200
    assert len(r.json()["items"]) == 1
    assert r.json()["items"][0]["title"] == "Alpha"

    r = requests.get("http://localhost:5000/tasks", params={"q": "ALPHA"})
    assert len(r.json()["items"]) == 1, "поиск должен быть регистронезависимым"

    # поиск по seed-задаче
    r = requests.get("http://localhost:5000/tasks", params={"q": "молоко"})
    assert len(r.json()["items"]) == 1
    assert "молоко" in r.json()["items"][0]["title"].lower()

    # комбинация фильтров: done=true + сортировка
    r = requests.get(
        "http://localhost:5000/tasks",
        params={"done": "true", "sort": "title", "order": "asc", "per_page": 100},
    )
    assert r.status_code == 200
    filt_titles = [t["title"] for t in r.json()["items"]]
    assert filt_titles == sorted(filt_titles), "фильтр+сортировка работают вместе"
    assert all(t["done"] for t in r.json()["items"])

    # невалидный done
    r = requests.get("http://localhost:5000/tasks", params={"done": "maybe"})
    assert r.status_code == 400
    print("5. фильтры ... ок")

    # ---------- 6. Создание: 201, монотонный id, значения по умолчанию ----------
    r = requests.post("http://localhost:5000/tasks", json={"title": "Новая задача"})
    assert r.status_code == 201, f"POST -> {r.status_code}, ожидался 201"
    tid = r.json()["id"]
    created_ids.append(tid)
    assert tid > max(all_ids), "id должен продолжать счётчик"
    assert r.json()["done"] is False
    print("6. создание ... ок")

    # ---------- 7. Контроль создания: дубликаты и валидация ----------
    r = requests.post(
        "http://localhost:5000/tasks", json={"title": "  Новая   задача "}
    )
    assert r.status_code == 409
    assert "error" in r.json()

    r = requests.post("http://localhost:5000/tasks", json={"done": True})
    assert r.status_code == 400

    r = requests.post("http://localhost:5000/tasks", json={"title": "   "})
    assert r.status_code == 422

    r = requests.post("http://localhost:5000/tasks", json={"title": LONG_TITLE})
    assert r.status_code == 422

    r = requests.post(
        "http://localhost:5000/tasks",
        data="not json",
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 400
    print("7. контроль создания ... ок")

    # ---------- 8. Чтение одной задачи ----------
    r = requests.get("http://localhost:5000/tasks/" + str(tid))
    assert r.status_code == 200
    assert r.json()["title"] == "Новая задача"

    r = requests.get("http://localhost:5000/tasks/999999")
    assert r.status_code == 404

    r = requests.get("http://localhost:5000/tasks/abc")
    assert r.status_code == 404
    print("8. чтение ... ок")

    # ---------- 9. Обновление: PUT заменяет, PATCH — частично ----------
    r = requests.put(
        "http://localhost:5000/tasks/" + str(tid),
        json={"title": "Новая задача", "done": True},
    )
    assert r.status_code == 200, f"PUT -> {r.status_code}"
    assert r.json()["done"] is True

    r = requests.put("http://localhost:5000/tasks/999999", json={"title": "x"})
    assert r.status_code == 404

    r = requests.patch("http://localhost:5000/tasks/" + str(tid), json={"done": False})
    assert r.status_code == 200
    assert r.json()["done"] is False
    assert r.json()["title"] == "Новая задача"

    r = requests.patch(
        "http://localhost:5000/tasks/" + str(tid), json={"title": "Alpha"}
    )
    assert r.status_code == 409

    r = requests.patch("http://localhost:5000/tasks/" + str(tid), json={"title": ""})
    assert r.status_code == 422
    print("9. обновление ... ок")

    # ---------- 10. Удаление: 204, идемпотентность, монотонность id ----------
    r = requests.delete("http://localhost:5000/tasks/" + str(tid))
    assert r.status_code == 204
    assert not r.content

    r = requests.delete("http://localhost:5000/tasks/" + str(tid))
    assert r.status_code == 404

    a = requests.post("http://localhost:5000/tasks", json={"title": "Задача А"}).json()[
        "id"
    ]
    b = requests.post("http://localhost:5000/tasks", json={"title": "Задача Б"}).json()[
        "id"
    ]
    created_ids += [a, b]
    assert b > a, "id не должны переиспользоваться после удаления"
    print("10. удаление ... ок")

    print("\nВсе тесты пройдены.")

finally:
    # ---------- восстановление состояния сервера ----------
    # удаляем всё, чего не было до прогона
    r = requests.get("http://localhost:5000/tasks", params={"per_page": 100})
    leftovers = [t["id"] for t in r.json()["items"] if t["id"] not in ids_before]
    for task_id in leftovers:
        requests.delete("http://localhost:5000/tasks/" + str(task_id))
    print(f"Состояние сервера восстановлено (удалено задач: {len(leftovers)}).")