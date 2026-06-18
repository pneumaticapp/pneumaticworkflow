# План изменений API `/templates` (ветка `backend/fieldsets/45773__fieldsets`)

Относительно `master`.

---

## 1. Общая концепция

Главное изменение — **fieldsets** в kickoff и задачах шаблона. Shared fieldset создаётся через `/fieldsets`, в шаблоне — **привязка** по `shared_fieldset_id` (копия с новыми `api_name` для полей и правил).

**Модель привязки:**
- Запись: `shared_fieldset_id`, `order`, `title`, `description`, `api_name`
- Read-only из shared: `name`, `label_position`, `layout`, `rules`, `fields`
- Один shared fieldset можно подключить к разным kickoff/task в одном шаблоне

---

## 2. Изменения по эндпоинтам

### 2.1. `GET /templates`, `GET /templates/:id`, `GET /templates/titles-by-owners`

**API (ответ):** в `kickoff.fieldsets[]` (и в `tasks[].fieldsets[]` для `GET /templates/:id`) — полная структура привязки fieldset, не `{ api_name, order }`.

**Wiki — обновлено:**

| Файл | Что изменилось |
|------|----------------|
| `GET _templates.md` | `kickoff.fieldsets[]`: добавлены `shared_fieldset_id`, `title`, `label_position`, `layout`, `rules`, полный `fields[]` |
| `GET _templates__id.md` | `kickoff.fieldsets[]` и `tasks[].fieldsets[]`: заменена урезанная схема на полную (как выше) |
| `GET _templates_titles-by-owners.md` | `kickoff.fieldsets[]`: то же, что в list |

**Было в wiki:** `{ name, order, description, api_name, fields[] }` или `{ api_name, order }`.  
**Стало:** полный объект привязки с `shared_fieldset_id`, layout, rules (`sum_equal`) и вложенными полями.

---

### 2.2. `POST /templates`, `PUT /templates/:id`

**API (запрос):** в `kickoff.fieldsets[]` и `tasks[].fieldsets[]` — привязки по `shared_fieldset_id`, не `[int]`.

**Wiki — обновлено:**

| Файл | Что изменилось |
|------|----------------|
| `POST _templates.md` | Описание: привязки через `shared_fieldset_id`, ссылка на `/fieldsets`; схема запроса в kickoff/tasks; блок **Fieldsets (запрос)** |
| `PUT _templates__id.md` | `fieldsets: [int]` → объекты привязки в kickoff и tasks (редактирование и создание задачи); блок **Fieldsets (запрос)** с логикой полной замены списка |

**Было в wiki:** `fieldsets: [int]` или «список id FieldsetTemplate».  
**Стало:** `{ shared_fieldset_id, order, title?, description?, api_name? }`; в PUT — полная синхронизация списка привязок.

---

### 2.3. `GET /templates/:id/fields`

**API (ответ):** укороченная схема полей + `fieldsets[]` с `title`, `order`, `label_position`, `layout`, `is_hidden`.

**Wiki — обновлено:**

| Файл | Что изменилось |
|------|----------------|
| `GET _templates__id_fields.md` | Полная схема `kickoff`/`tasks` с `fieldsets[]`; добавлены `title`, `is_hidden`; комментарии к `label_position`/`layout`; примечания об укороченной схеме и сортировке |

**Было в wiki:** неполная схема fieldsets (без `title`, `is_hidden`).  
**Стало:** соответствует `FieldsetTemplateOnlyFieldsSerializer` / `FieldTemplateOnlyFieldsSerializer`.

---

### 2.4. `POST /templates/:id/clone`

**API:** копируются fieldsets kickoff/tasks; `shared_fieldset_id`, `order`, `title`, `description` сохраняются; `api_name` fieldsets/fields/rules пересоздаются.

**Wiki — обновлено:**

| Файл | Что изменилось |
|------|----------------|
| `POST _templates__id_clone.md` | Блок **Fieldsets при клонировании**: что сохраняется, что пересоздаётся; ссылка на ответ `GET /templates/:id` |

---

### 2.5. `POST /templates/:id/run`

**Запрос** — `kickoff` по-прежнему плоский `api_name → value`, но ключи включают **поля из fieldsets**.

**Ответ** — в `kickoff` появляется `fieldsets[]` (runtime `FieldSet`).

**Валидация:** правила `sum_equal` при старте workflow.

**Документация:** `POST _templates__id_run.md` — заменить `sum_max` на `sum_equal`, описать поля из fieldsets.

---

### 2.6. `GET /templates/export`

**Ответ** — `kickoff.fieldsets` и `tasks[].fieldsets` с `order`.

**Документация:** `GET _templates_export.md`.

---

### 2.7. `GET /templates/public`

**Ответ** — `kickoff.fieldsets[]` (полная схема через `FieldsetTemplateSerializer`).

**Рефакторинг:** `kickoff` через `SerializerMethodField` + `kickoff_instance`.

**Документация:** `Public/GET _templates_public.md`, `Public/POST _templates_public_run.md`.

---

### 2.8. Conditions (в теле `POST/PUT /templates`)

**Новые операторы предикатов** (`predicate_type: task`):
- `skipped`
- `completed_or_skipped`

**`start_task`:** разрешены `completed`, `skipped`, `completed_or_skipped`.

**Миграция черновиков:** `completed` → `completed_or_skipped`.

**Документация:** `POST _templates.md`, `PUT _templates__id.md` — операторы в `conditions`; при необходимости отдельная памятка.

---

### 2.9. Workflow name template

**Изменение:** в шаблон имени workflow можно подставлять поля из **fieldsets** kickoff (не только плоские `fields`).

**Документация:** памятка по шаблону имени workflow.

---

### 2.10. Без изменений URL

Эндпоинты без изменений контракта (кроме косвенных effects через fieldsets в run):
- `DELETE /templates/:id`
- `GET /templates/:id/steps`
- `GET /templates/:id/integrations`, `GET /templates/integrations`
- `POST /templates/by-steps`, `POST /templates/by-name`, `POST /templates/ai`
- `POST /templates/:id/discard-changes`
- `GET /templates/titles-by-*`
- Presets

**Удалённый эндпоинт:** `GET /templates/:id/fieldsets` — заменён на `/fieldsets` (уже вынесен в wiki).

---

## 3. Изменения схем полей

| Объект | Изменение |
|--------|-----------|
| `FieldTemplateListSerializer` | добавлен `default` |
| `FieldTemplateShortViewSerializer` | удалён |
| `FieldTemplateSerializer` | порядок полей в ответе |
| `KickoffListSerializer` | + `fieldsets` |
| `TaskTemplateSerializer` | + `fieldsets` |

---

## 4. Технические изменения (не для публичной wiki)

- `TemplateViewSet`: убраны `filter_backends` / `TemplateFilter` (фильтрация list через `TemplateListFilterSerializer` как раньше)
- `action_filterset_classes.list_fieldsets` — мёртвый код (action удалён)
- `FieldsetMixin` в `mixins.py`: `create_or_update_fieldsets`, `get_draft_fieldsets`

---

## 5. План обновления wiki

| Приоритет | Файл | Что сделать |
|-----------|------|-------------|
| P0 | `POST _templates.md` | ✅ схема `fieldsets` в kickoff/tasks + блок Fieldsets (запрос) |
| P0 | `PUT _templates__id.md` | ✅ схема fieldsets + полная замена списка; операторы `skipped` / `completed_or_skipped` уже в conditions |
| P0 | `GET _templates__id.md` | ✅ `fieldsets[]` в kickoff/tasks — полная схема |
| P0 | `GET _templates.md` | ✅ `fieldsets[]` в list response — полная схема |
| P0 | `GET _templates__id_fields.md` | ✅ `fieldsets[]` с `title`, `order`, `layout`, `label_position`, `is_hidden` |
| P1 | `POST _templates__id_run.md` | поля fieldsets в kickoff, `sum_equal` |
| P1 | `Public/GET _templates_public.md` | `kickoff.fieldsets` |
| P1 | `Public/POST _templates_public_run.md` | валидация fieldsets |
| P1 | `POST _templates__id_clone.md` | ✅ клонирование fieldsets |
| P1 | `GET _templates_export.md` | fieldsets в export |
| P2 | `GET _templates_titles-by-owners.md` | ✅ fieldsets в nested kickoff — полная схема |
| P2 | Памятка workflow name | поля из fieldsets |

**Уже сделано:** `/fieldsets` вынесен в `API/Public API/fieldsets/`.

---

## 6. Breaking changes для клиентов

1. **`fieldsets` в шаблоне** — не `[int]`, а объекты с `shared_fieldset_id`.
2. **Ответ fieldsets** — полная структура (поля, rules), не только id.
3. **Условия** — для task-предикатов предпочтителен `completed_or_skipped` вместо `completed`.
4. **`GET /templates/:id/fieldsets`** — удалён, использовать `/fieldsets`.
5. **Run/complete** — в kickoff нужно передавать значения полей из fieldsets по их `api_name`.

---

## 7. Порядок работ

1. Обновить схемы запроса/ответа в P0-файлах wiki.
2. Добавить cross-link: Templates → Fieldsets (`shared_fieldset_id`).
3. Обновить P1 (run, public, clone, export).
4. Пройтись по примерам JSON в тестах (`test_update/test_fieldsets.py`, `test_fields.py`, `test_clone/test_fieldsets.py`) как эталонам.
5. Проверить фронтенд-типы и API-клиенты на старую схему `fieldsets: [int]`.
