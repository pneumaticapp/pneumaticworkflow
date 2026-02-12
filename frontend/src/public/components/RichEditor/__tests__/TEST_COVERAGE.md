# Rich Editor – Test coverage

Summary of test cases and where they are implemented.

---

## Coverage in general

**100% coverage — нет.** Покрыты в основном контракт обёртки, утилиты, конвертеры (с моками), хуки ссылок и часть плагинов. Не покрыты или только частично:

| Что не покрыто | Причина |
|----------------|--------|
| Реальный Lexical-редактор в Jest | Монтирование зависает в JSDOM (scheduler/RAF). Тесты используют мок `../lexical` или пропущенные E2E-спеки. |
| Ввод текста, Undo/Redo, Backspace/Delete, каретка | Спеки есть в `RichEditor.integration.test.tsx`, но тесты **skipped** — нужен E2E. |
| LinkUrlForm (форма ввода URL) | Рендер в Jest зависает (portal/зависимости). Один тест skipped. |
| LinkTooltipPlugin, VariableTooltipPlugin | Нет юнит-тестов; логика привязана к DOM/editor. |
| Checklist: вставка, удаление, Enter, выход | Всё внутри `editor.update()` и нодах Lexical — в Jest только пустые кейсы в `checklistPluginUtils`. |
| VariableNode: clone, exportJSON, copy/paste | Создание ноды в Jest даёт Lexical #196. Покрыт только `getType()`. |
| Реальный LexicalRichEditor (без мока) | В `LexicalRichEditor.test.tsx` замокан сам компонент; контракт проверяется через мок. |

**Итог:** для редактора достижимо хорошее покрытие контракта и утилит; полное покрытие поведения (ввод, ссылки, чек-листы, тултипы) требует E2E (Playwright/Cypress) в браузере.

---

## Security / attack vectors

**Currently covered:**

| Area | File | What is tested |
|------|------|----------------|
| **Dangerous URL protocols** | `utils/__tests__/urlUtils.test.ts` | `isUrl()` returns false for `javascript:` and `data:` (normalizeUrl adds `https://` because protocol regex requires `://`; `new URL()` then fails). `normalizeUrl` behaviour for these inputs is covered. |
| **Malicious markdown** | `converters/__tests__/convertMarkdownToLexical.test.ts` | `applyMarkdownToEditor` does not throw on script-like content, `javascript:` in markdown, or very long input (resilience; actual XSS prevention relies on Lexical rendering content as text, not raw HTML). |

**Not covered by RichEditor tests:**

- **XSS in display**: The **RichText** component (different from RichEditor) uses `xss-filters` and has a test `clears xss` (script tag rendered as text). The Lexical RichEditor does not use raw `innerHTML` for user content; VariableNode and others render via React children (auto-escaped). No dedicated XSS test for the editor’s output.
- **Link click hijacking**: `urlUtils.isUrl()` already returns false for `javascript:` and `data:`; no separate test that LinkUrlForm blocks these at submit (integration).
- **Prototype pollution / JSON injection**: No tests for malicious `defaultValue` or payloads trying to break the editor state.
- **E2E**: No automated E2E tests that assert absence of script execution (e.g. in Playwright) for the editor.

**Recommendations:** Add `isSafeForLink(url)` (or use a allowlist of protocols) in link submission and test it; consider E2E checks that script tags in content are not executed.

---

## Links and tooltips

**Covered by unit tests:**

| Area | File | What is tested |
|------|------|----------------|
| **Link form state** | `LexicalRichEditor/hooks/__tests__/useLinkFormState.test.tsx` | Initial state closed; openLinkForm(rect, mode, ref) sets isOpen true and formMode; closeLinkForm() sets isOpen false. |
| **Link apply action** | `LexicalRichEditor/hooks/__tests__/useLinkActions.test.tsx` | applyLink(url) without linkText dispatches TOGGLE_LINK_COMMAND with url and calls onFormClose. |
| **URL validation** | `utils/__tests__/urlUtils.test.ts` | isUrl / normalizeUrl (LinkUrlForm uses these for validation). |

**Not covered (E2E recommended):**

| Scenario | Where implemented |
|----------|-------------------|
| Link: form visible, URL input, submit valid/invalid, close button | `LinkUrlForm` — unit test file exists but hangs in Jest (heavy deps/portal). Prefer E2E. |
| Link: remove link | TOGGLE_LINK_COMMAND to remove link from selection |
| Link tooltip on hover | `LinkTooltipPlugin` |
| Variable tooltip on hover | `VariableTooltipPlugin` |

---

## Editor interaction (E2E specs)

**File:** `src/public/components/RichEditor/__tests__/RichEditor.integration.test.tsx`

These scenarios are **defined in Jest but skipped** because the real Lexical editor does not complete mount in JSDOM (scheduler/RAF). They should be run in a **real browser** (e.g. Playwright, Cypress).

| Scenario | What to check |
|----------|----------------|
| **Insert into empty** | Type text → DOM shows it; `handleChange` last arg (markdown) contains the text. |
| **Insert in middle** | `defaultValue="ab"` → move cursor left (ArrowLeft) → type "X" → DOM and markdown are "aXb"; focus stays in editor. |
| **Backspace** | Type "ab" → Backspace → DOM and data are "a"; focus in editor. |
| **Delete** | Type "ab" → ArrowLeft → Delete → DOM and data are "a"; focus in editor. |
| **Undo (3 steps)** | Type "1", "2", "3" → Ctrl+Z × 3 → content empty; focus in editor. |
| **Redo (3 steps)** | After undo → Ctrl+Shift+Z × 3 → content "123"; focus in editor. |
| **Cursor after each op** | After insert / Backspace / Delete / Undo / Redo: `document.activeElement` is the contenteditable; visible text matches expectation. |

**Selector:** `data-testid="rich-editor-contenteditable"` (ContentEditable). Use Testing Library `getByTestId` + `userEvent.type` / `userEvent.keyboard` (or Playwright `page.locator('[data-testid="rich-editor-contenteditable"]').fill()` / `press()`).

---

## 1. `RichEditor` (root / re-export)

**File:** `src/public/components/RichEditor/__tests__/RichEditor.test.tsx`

| Case | Description |
|------|-------------|
| Render | Renders without crashing; root has `data-testid="rich-editor-root"` |
| Ref API | Ref exposes `focus`, `insertVariable`, `getEditor` |
| Title | Renders title when provided; does not render title when undefined |
| ClassName | Applies custom `className` to root |
| Children | Renders children |
| Ref: focus | `ref.current.focus()` does not throw |
| Ref: getEditor | `ref.current.getEditor` is a function |
| Ref: insertVariable | `insertVariable('', '', '')` does not throw; `insertVariable('api_name', 'Title', 'Subtitle')` calls implementation with same args |
| Props | Accepts `defaultValue`, `placeholder`, `withToolbar`, `withChecklists`, `multiline` and renders |

**Usage in project (prop combinations):** Tests mirror real consumers; each renders and asserts root in document (and title/children when applicable).

| Consumer | Props covered |
|----------|----------------|
| **ReturnModal** | placeholder, handleChange, isModal |
| **Field (RichText)** | placeholder, defaultValue, handleChange, className, accountId |
| **WorkflowLogTaskComment** | placeholder, defaultValue, handleChange, submitIcon, cancelIcon, onSubmit, onCancel, accountId |
| **PopupCommentField** | placeholder, handleChange, onSubmit, className, accountId |
| **TaskDescriptionEditor** | ref, title, placeholder, defaultValue, handleChange, handleChangeChecklists, withChecklists, withToolbar, withMentions, mentions, templateVariables, accountId, children |

*Note: This file mocks the whole `../lexical` module, so it tests the wrapper contract, not the real LexicalRichEditor.*

---

## 2. `LexicalRichEditor` (contract)

**File:** `src/public/components/RichEditor/lexical/LexicalRichEditor/__tests__/LexicalRichEditor.test.tsx`

| Case | Description |
|------|-------------|
| Export | RichEditor is exported and is a function |
| Mount | Mounts when rendered with defaultProps |
| Title | Renders title when prop is passed |
| ClassName | Applies className to root |
| Ref | Ref exposes `focus`, `insertVariable`, `getEditor` |
| insertVariable | `insertVariable('', '', '')` does not throw |

*Note: Full LexicalRichEditor is mocked here (React context loss with heavy mocks). Real behaviour is covered by RichEditor.test.tsx (mocked lexical) and E2E.*

---

## 3. `EditorHeader`

**File:** `src/public/components/RichEditor/lexical/LexicalRichEditor/EditorHeader/__tests__/EditorHeader.test.tsx`

| Case | Description |
|------|-------------|
| Export | Exports a component (function) |
| No title | Returns null when `title` is undefined or empty string |
| With title | Renders title text when provided |
| Root div | Renders root div with class when title is provided |

*Note: Real EditorHeader is mocked (React context in Jest). Contract is tested via mock.*

---

## 4. Utils: `getMentionData`

**File:** `src/public/components/RichEditor/utils/__tests__/getMentionData.test.ts`

| Case | Description |
|------|-------------|
| Status filter | Returns only users with `Active` status; empty when none active; all when all Active |
| Result shape | Maps user to `{ id, name }`; calls `getUserFullName` per active user |
| Empty name | Uses empty string for `name` when `getUserFullName` returns empty |
| Edge: empty input | Returns empty array for empty users array |
| Edge: no status | Ignores users without `status` |
| Edge: External | Treats `External` as non-Active (excluded) |

*Mocks:* `getUserFullName` (utils/users).

---

## 5. Utils: `getAttachmentEntityType`

**File:** `src/public/components/RichEditor/utils/__tests__/getAttachmentEntityType.test.ts`

| Case | Description |
|------|-------------|
| Null type | Returns `File` when `getAttachmentTypeByUrl` returns null |
| file / image / video | Returns `File`, `Image`, `Video` for types file, image, video |
| Delegation | Calls `getAttachmentTypeByUrl` with given url |
| Edge: empty url | Returns `File` for empty string url (getAttachmentTypeByUrl returns null) |
| Edge: unknown type | Returns `File` for unknown type in map |

*Mocks:* `getAttachmentTypeByUrl` (Attachments/utils/getAttachmentType).

---

## 6. Utils: `urlUtils` (normalizeUrl, isUrl)

**File:** `src/public/components/RichEditor/utils/__tests__/urlUtils.test.ts`

| Case | Description |
|------|-------------|
| normalizeUrl | Empty/whitespace → empty; no protocol → adds https://; with protocol → unchanged; trims; keeps path/query/subdomain |
| isUrl | true for valid URLs (with/without protocol, localhost, path); false for invalid/whitespace |
| Default export | Exposes `normalizeUrl` and `isUrl` |

---

## 7. Converters: `convertLexicalToMarkdown`

**File:** `src/public/components/RichEditor/lexical/converters/__tests__/convertLexicalToMarkdown.test.ts`

| Case | Description |
|------|-------------|
| read | Calls `editorState.read` with a callback |
| Result | Returns result of `$convertToMarkdownString` |
| Error in read | Returns empty string when callback throws; logs to console.error |
| Error in conversion | Returns empty string and logs when `$convertToMarkdownString` throws |
| read throws | Returns empty string when `read` itself throws |

*Mocks:* `@lexical/markdown` `$convertToMarkdownString`.

---

## 8. Converters: `applyMarkdownToEditor` (convertMarkdownToLexical)

**File:** `src/public/components/RichEditor/lexical/converters/__tests__/convertMarkdownToLexical.test.ts`

| Case | Description |
|------|-------------|
| prepareChecklistsForRendering | Called with given markdown |
| editor.update | Called with callback and default tag `history-merge`; custom tag passed via options.tag |
| $convertFromMarkdownString | Called with result of prepareChecklistsForRendering inside update |
| Error: prepare | On prepare error: logs to console.error, does not rethrow |
| Error: update callback | On convert error in update: logs, does not rethrow |
| templateVariables | When templateVariables passed, update is called and convert is invoked |

*Mocks:* `prepareChecklistsForRendering`, `@lexical/markdown` `$convertFromMarkdownString`, fake editor.update.

---

## 9. Converters: `variableMarkdown` (createVariableTransformer, getVariablePayload)

**File:** `src/public/components/RichEditor/lexical/converters/__tests__/variableMarkdown.test.ts`

| Case | Description |
|------|-------------|
| **Variable not found by apiName** | `getVariablePayload(apiName, [])` and unknown apiName: returns `{ apiName, title: apiName, subtitle: undefined }` (fallback so node still renders) |
| **Variable found by apiName** | `getVariablePayload(apiName, templateVariables)` when match exists: returns variable's title and subtitle |
| Transformer shape | Returns object with `type: 'text-match'` and `dependencies` array |
| export | Has `export` function |
| RegExp | Has `importRegExp` and `regExp` |

*Note: `parseTextWithVariables` and node-creating paths are not unit-tested here (Lexical needs registered editor). Covered in integration/E2E.*

---

## 9b. Variable node (VariableNode)

**File:** `src/public/components/RichEditor/lexical/nodes/VariableNode/__tests__/VariableNode.test.ts`

| Case | Description |
|------|-------------|
| getType | Static `VariableNode.getType()` returns `'variable'` |

*Note: Creating VariableNode in Jest triggers Lexical error #196 (no registered editor). Insertion is tested via ref.insertVariable in RichEditor/LexicalRichEditor tests (mocked). Clone, exportJSON, copy/paste, delete are not unit-tested; cover in E2E.*

---

## 10. Checklists: `prepareChecklistsForAPI` & `extractChecklistsFromMarkdown`

**File:** `src/public/utils/checklists/__tests__/prepareChecklistsForAPI.test.ts`

| Case | Description |
|------|-------------|
| extractChecklistsFromMarkdown | Empty string → []; no tags → []; one item empty value; one item with value; multiple same list; different lists; apiName with hyphens; unclosed tag → [] |
| prepareChecklistsForAPI | Empty → []; one checklist one selection; groups same listApiName; splits different listApiName; preserves empty value; handles text around checklists |

---

## 11. Hook: `useAttachmentUpload`

**File:** `src/public/components/RichEditor/lexical/LexicalRichEditor/hooks/__tests__/useAttachmentUpload.test.tsx`

| Case | Description |
|------|-------------|
| Success | Calls `uploadFiles(files, accountId)`; dispatches `INSERT_ATTACHMENT_COMMAND` per uploaded item with url; type from `getAttachmentTypeByUrl` or `'file'`; skips items without url; clears input value in finally |
| Early return | No uploadFiles when files empty; accountId undefined/null; editorRef.current null |
| Error | On uploadFiles reject: calls `NotificationManager.warning`; still clears value in finally |

*Mocks:* `uploadFiles`, `getAttachmentTypeByUrl`, `NotificationManager`.

---

## 12. ChecklistPlugin: `checklistPluginUtils`

**File:** `src/public/components/RichEditor/lexical/plugins/ChecklistPlugin/__tests__/checklistPluginUtils.test.ts`

| Case | Description |
|------|-------------|
| removeDuplicateClipboardParagraphs | Returns empty array for empty input |
| nodesContainChecklist | Returns false for empty array |

**Checklist UX (insert, delete, new item, exit) — not covered by unit tests:**

| Scenario | Handler | Why not tested |
|----------|---------|----------------|
| **Insert checklist** | `INSERT_CHECKLIST_COMMAND` → createInsertChecklistHandler, insertChecklistAndSelectFirst / convertBlockToChecklist | Runs inside `editor.update()`, needs Lexical editor (error #196 in Jest). |
| **Delete (Backspace on empty item)** | KEY_BACKSPACE_COMMAND → createBackspaceHandler, getBackspaceOnEmptyChecklistPayload, applyBackspaceOnEmptyChecklist | Same: selection + nodes in editor state. |
| **New item (Enter in item)** | KEY_ENTER_COMMAND → createEnterKeyHandler (new ChecklistItemNode) | Same. |
| **Exit (Enter on empty item → paragraph)** | KEY_ENTER_COMMAND → getInsertParagraphFromEmptyChecklistPayload, applyInsertParagraphFromEmptyChecklist | Same. |

*Recommendation:* Cover these in E2E (e.g. Playwright): trigger INSERT_CHECKLIST_COMMAND or toolbar button, type, Enter (new line / exit), Backspace on empty item.

*Note: Lexical node creation requires editor (Lexical #196). Only empty-input behaviour is unit-tested; rest in integration/E2E.*

---

## Run

Run all editor-related tests:

```bash
npm test -- --testPathPattern="RichEditor|getMentionData|prepareChecklistsForAPI|convertLexicalToMarkdown|convertMarkdownToLexical|variableMarkdown|useAttachmentUpload|LexicalRichEditor|EditorHeader|getAttachmentEntityType|checklistPluginUtils|urlUtils|useLinkFormState|useLinkActions"
```
