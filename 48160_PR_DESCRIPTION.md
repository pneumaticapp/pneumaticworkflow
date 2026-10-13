### 1. Release notes

Added AI agent support to the Team page: agents are created from the shared create modal (User / AI Agent tabs) and listed directly in the Team → Users list alongside people — with provider/model meta, an activation switch, and a 3-dot menu (Edit/Delete). Mixed user/agent rows use separate key namespaces, so equal numeric IDs cannot confuse React reconciliation during sorting. AI providers are managed under Integrations (skeleton loading, Formik-based create modal).

### 2. Context

- **Issue:** 48160 frontend [teams] add AI agent creation form
- **App Location:** Team → Users list (agent cards among people); create modal → AI Agent tab; Integrations → AI Providers
- **Related Changes:** Backend AI providers/agents API (tasks 46034/49034, branch `backend/ai/49034__ai_agents_2` merged in) provides `GET/POST /ai/providers`, `GET/POST /ai/agents`, `GET /ai/providers/:id/models`, `GET /ai/vendors`. The users list request keeps `is_ai=false` — agent cards come from the `/ai/agents` store, not from `/users`.

### 3. Solution & Implementation Details

- `Team/Users/CreatePerformerModal/` (renamed from `CreateUserModal`) — container `CreatePerformerModal` owns the tab logic; nested `CreateUserForm` and `CreateAIAgentForm`. Both forms stay mounted across tab switches (draft preservation); the agent form resets on the reopen edge via Formik `innerRef` (no extra helper component). Redux modal state names (`openCreateUserModal`, `isCreateUserModalOpen`) intentionally unchanged.
- `CreateAIAgentForm` — Formik form: name, provider dropdown (auto-preselected when the account has exactly one provider), model dropdown, system prompt via the new shared `UI/Fields/TextareaField/FormikTextareaField`, avatar upload (file goes to the file service immediately; the API stores a hosted URL) or initials from the name. Model loading: a stale model is cleared only on a real provider change (sync ref initializes from the current value, so returning to the tab keeps the picked model); models are refetched only when they belong to another provider, at most one request per provider per mount (`modelsRequestedForRef`) — a failed load neither loops nor blocks a retry on remount (`loadAIProviderModelsFailed` resets `models.providerId` to `null`).
- `Team/Users/` — agents render inside the Users list: `Users.tsx` converted from connect() to hooks (`container.ts` removed), dispatches `loadAIAgents` alongside the users fetch, and merges `ai.agents.list` with the team list applying the same active sort and search to the union. User and agent card keys have different prefixes because their IDs come from different tables. New `TeamAgent.tsx` card: photo/initials avatar, name, `provider · model` meta, inactive badge, labeled Active switch (no tooltip), 3-dot `Dropdown` with Edit (opens `EditAIAgentModal`, moved here) and Delete (confirmation modal). No Clone — the backend has no clone endpoint (out of scope). Skeletons show while users or agents load. The separate AI Agents tab, `/team/ai-agents/` route, and page are removed.
- `IntegrationsCommon/AIProviders/` — skeleton rows (`AIProvidersSkeleton` on `UI/Skeleton`) while loading; create modal rewritten on Formik (`FormikInputField`/`FormikDropdownList`), API key inputs are `type="password"`, the active tab pill has an orange background (`var(--pneumatic-color-orange)`) while the tab bar keeps the shared white background; vendor list is loaded through redux (`loadAIVendors` saga), notifications live in sagas; disabled delete button has `pointer-events: none` so its tooltip survives clicks; CSS rewritten to nested `&__` blocks.
- `redux/ai/` — store lists carry only `isLoading` (initial `true`, so no empty-state flash before the first fetch; the redundant `isLoaded` was removed; refetches keep `isLoading` false when a list already has items, so skeletons and the create gate don't flicker). Mutation sagas show a success notification only when the follow-up list refresh succeeded; refresh helpers ignore stale responses via per-list request counters.
- `utils/validators.ts` — shared `validateRequired` (`REQUIRED_RULES` + `validation.field-required` locale key) used by both AI forms; the per-form duplicates were removed.
- `api/getUsers.ts` — `isAi` param sent when `typeof isAi === 'boolean'`; the team people list requests `is_ai=false`.
- `UI/DropdownList` — `FormikDropdownList` marks the field touched on blur (deferred so react-select finishes the option click) and passes `null` instead of `undefined` for a cleared value.
- `UI/BaseModal` — `ModalHeader` title defaults to `h2` (was `p`, semantically invalid); page-scrollbar compensation is done via global `html { scrollbar-gutter: stable }` instead of JS body padding.
- `TeamLayout` — simplified route check via varargs `checkSomeRouteIsActive(ERoutes.Groups, ERoutes.GroupDetails)`.

### 4. What to Test

#### 4.1 Preconditions

- Backend with the AI API (46034/49034) running.
- Account admin; at least one AI provider configured on the Integrations page (for creation scenarios).

#### 4.2 Positive Scenarios / Testing Report

| # | Steps | Expected result | Chrome Desktop | Safari Desktop | Chrome Mobile | Safari Mobile |
|---|-------|-----------------|----------------|----------------|---------------|----------------|
| 1 | Team → open create modal → AI Agent tab | Form with name, provider, model, system prompt, avatar actions | [ ] | [ ] | [ ] | [ ] |
| 2 | Select provider → model dropdown | Models load for the provider; switching provider clears the picked model | [ ] | [ ] | [ ] | [ ] |
| 3 | Fill the form → Create | Agent created; success notification; agent card appears in the Team → Users list | [ ] | [ ] | [ ] | [ ] |
| 4 | Fill both tabs partially, switch tabs back and forth | Entered values and the generated password survive tab switches; picked model survives returning to the AI tab | [ ] | [ ] | [ ] | [ ] |
| 5 | Close and reopen the modal | Agent form is reset (no stale draft, no stale avatar upload landing) | [ ] | [ ] | [ ] | [ ] |
| 6 | Team → Users → agent card: toggle activation switch, open ⋯ menu → edit / delete | Switch has an "Active" label and no tooltip; actions live in a 3-dot dropdown like user cards; each action updates the list and shows a success notification | [ ] | [ ] | [ ] | [ ] |
| 7 | Account without providers → AI Agent tab | "Register a provider first" hint instead of the form; create gated | [ ] | [ ] | [ ] | [ ] |
| 8 | Integrations → AI Providers | Skeleton rows while loading; create modal (vendor/custom tabs, active tab highlighted orange) creates providers; API key masked | [ ] | [ ] | [ ] | [ ] |
| 9 | Team → Users with agents and people | Agent cards render among user cards; search and name sorting apply to both kinds | [ ] | [ ] | [ ] | [ ] |
| 10 | Open AI Agent tab, switch to User tab and back | Models are NOT refetched on tab return; picked provider/model stay | [ ] | [ ] | [ ] | [ ] |

#### 4.3 Negative Scenarios & Edge Cases

| # | Steps | Expected result | Chrome Desktop | Safari Desktop | Chrome Mobile | Safari Mobile |
|---|-------|-----------------|----------------|----------------|---------------|----------------|
| 1 | Submit with empty required fields | Submit disabled; after touching a field its required error is shown localized | [ ] | [ ] | [ ] | [ ] |
| 2 | Upload the same avatar file twice in a row | Second selection re-triggers the upload (file input is reset) | [ ] | [ ] | [ ] | [ ] |
| 3 | Upload avatar, then click Generate before the upload finishes | Stale upload cannot overwrite the generated initials (action id guard) | [ ] | [ ] | [ ] | [ ] |
| 4 | Delete a provider still used by an agent | API error (MSG_AI_0005) shown as a warning; provider stays | [ ] | [ ] | [ ] | [ ] |
| 5 | Simulate list-refresh failure after a successful create | Warning from the failed refresh is shown; no misleading success notification | [ ] | [ ] | [ ] | [ ] |
| 6 | Two rapid mutations in a row | A stale refresh response cannot resurrect a deleted provider or hide a new one (request-id guard) | [ ] | [ ] | [ ] | [ ] |
| 7 | Hover/click the disabled delete button on a used provider | Tooltip with the reason appears and does not disappear on click | [ ] | [ ] | [ ] | [ ] |
| 8 | Simulate a failing `GET /ai/providers/:id/models` response | One warning toast; no retry loop while the form stays open; reopening the modal retries the load once | [ ] | [ ] | [ ] | [ ] |
| 9 | Arrange a user and an agent with the same numeric ID; expand the user card and change name sort order | Both cards remain present; the user's expanded state survives the reorder | [ ] | [ ] | [ ] | [ ] |

#### 4.4 Verification Points

- Agents are excluded from the `/users` request (`is_ai=false`) and rendered from the `/ai/agents` store instead.
- The AI Agents tab and `/team/ai-agents/` route are gone; the old URL no longer resolves to a page.
- Model dropdown is disabled until a provider is picked; shows a loading placeholder while models load.
- Modal headers render `h2` titles; layout does not shift sideways when the modal locks page scroll.
- Create modal tabs: active tab pill has an orange background on the AI provider creation modal.
- Mixed user and agent cards retain their own React identity even when their numeric IDs coincide.

#### 4.5 API Verification

- `GET /ai/providers` → unpaginated list used for the gate and provider names.
- `GET /ai/vendors` → vendor options loaded via saga.
- `GET /ai/providers/:id/models` → model options `{name, slug}`.
- `POST /ai/agents` payload: `{name, providerId, model, systemPrompt, photo, isActive}`.
- `GET /users?...&is_ai=false` for the Team people list.

#### 4.6 What Was NOT Tested

- Live Team list not manually exercised: the local frontend redirects to sign-in, and no authenticated browser session was available. The collision/reorder path was exercised in the React component test.
- No live provider API request was performed in this review round. Backend review findings on PR #297 (vendor discovery, provider scoping/cache, agent completion) belong to backend tasks 46034/49034 and were not modified in this frontend-only round.

### 5. Affected Areas

| Area | Change | Chrome Desktop | Safari Desktop | Chrome Mobile | Safari Mobile |
|------|--------|----------------|----------------|---------------|----------------|
| Team → create modal | Renamed to CreatePerformerModal; container + 2 forms; AI Agent tab | [ ] | [ ] | [ ] | [ ] |
| Team → Users list | Agent cards among people; shared sort/search; distinct user/agent keys preserve card identity on reorder; agent edit/delete/toggle from the card | [ ] | [ ] | [ ] | [ ] |
| Integrations → AI Providers | Skeleton loading, Formik create modal, masked API key, saga-driven vendors | [ ] | [ ] | [ ] | [ ] |
| Team people list | `is_ai=false` filter | [ ] | [ ] | [ ] | [ ] |
| UI: DropdownList, BaseModal, TextareaField | Touched-on-blur, cleared value, h2 titles, scrollbar-gutter; new textarea field | [ ] | [ ] | [ ] | [ ] |
| Team navigation | AI Agents tab and `/team/ai-agents/` route removed | [ ] | [ ] | [ ] | [ ] |

### 6. Unit Tests

- `CreatePerformerModal/__tests__/CreatePerformerModal.test.tsx` — tab switching, draft preservation, reset on reopen, avatar races, localized required errors (`validation.field-required`), model reload only on provider change, submit payloads.
- `Team/Users/__tests__/TeamAgent.test.tsx` + `EditAIAgentModal.test.tsx` — agent card in the list (meta, unknown provider, inactive badge), toggle dispatches `updateAIAgent` preserving fields, edit opens the modal with the agent's values, delete confirms and dispatches.
- `Team/Users/__tests__/Users.test.tsx` — merged list order, shared search, skeleton while agents load, and state preservation when user and agent IDs collide across sort changes. Obsolete snapshot assertions and dispatch-wiring assertions removed; the snapshot file was deleted.
- `AIProviders/__tests__/AIProviders.test.tsx` + `CreateAIProviderModal.test.tsx` — skeleton loading, vendor/custom tab submit payloads, vendors loaded via dispatched action.
- Review round: `Users.test.tsx` 4/4 passed; `tsc --noEmit --skipLibCheck -p tsconfig.json` passed (bare `tsc` reports conflicting dependency declarations in `node_modules`); ESLint on `Users.tsx`, Prettier on both changed TSX files, and `git diff --check` passed. Earlier Team + AIProviders run: 49/49 passed.

### 7. Commits

Frontend (task 48160, oldest → newest):

- `f49beba43` — 48160 feat(team): add AI agent creation form
- `bbbfb42e6` — 48160 fix(team): keep create modal within viewport
- `60630b76e` — 48160 fix(team): align AI agent modal with design
- `5facd59f0` — 48160 fix(team): scroll AI agent modal as a page
- `f7d6ef0a9` — 48160 fix(team): refine create modal controls
- `2b71d6592` — 48160 fix(team): align AI agent avatar actions
- `c0796e738` — 48160 fix(team): uppercase avatar action labels
- `52836d516` — 48160 fix(team): adapt create modal height to active tab
- `a31603d6b` — 48160 fix(team): center create user modal
- `b2496b103` — 48160 fix(team): validate and handle AI agent creation
- `819897312` — 48160 fix(team): preserve create modal drafts
- `8a7c93b4a` — 48160 fix(team): scope dropdown required markers
- `7bab692ab` — 48160 fix(team): reset AI avatar file input
- `5282aa26c` — 48160 fix(team): prevent stale avatar and touch model
- `3a81ca374` — 48160 fix(team): reset AI agent form on reopen
- `57bd2b27e` — 48160 fix(team): invalidate avatar reads on reopen
- `c938adc9f` — 48160 fix(ai): skip success notification when list refresh fails
- `900569adc` — 48160 chore(ai): remove redundant comments
- `c09de8ad4` — 48160 fix(ui): default modal header title to h2
- `fe302d030` — 48160 refactor(ai): clean up ai store and review findings
- `0523ec2dd` — 48160 refactor(ai): skeleton, formik provider modal
- `ab6b1f3e0` — 48160 refactor(team): CreatePerformerModal split
- `f243f8f18` — 48160 fix(team): keep selected model on tab return
- `61ed4cfcf` — 48160 fix(providers): mask api key input
- `f7cee4c1b` — 48160 fix(ai): ignore stale list refresh responses
- `c26c62069` — 48160 fix(ai): show skeleton only on empty lists
- `e2b2fc42a` — 48160 fix(ai): orange active tab instead of bar
- `db2ff9c17` — 48160 fix(ui): use scrollbar-gutter for modal lock
- `169fc5c56` — 48160 refactor(utils): share required field validator
- `c435c1530` — 48160 fix(team): agent form review fixes
- `c320912e3` — 48160 refactor(team): agent card dropdown and empty state
- `191123791` — 48160 fix(ai): allow model reload retry after failure
- `1699dcb61` — 48160 fix(team): retry model load once per mount
- `965130914` — 48160 feat(team): move AI agents into users list
- `4dd72092` — 48160 fix(team): keep mixed user and agent cards distinct

Merged backend dependency (tasks 46034/49034, reviewed separately):

- `backend/ai/49034__ai_agents_2` through `4b083e464` (49034 fix(ai): retry task completion on TaskFieldException and pass previous attempt errors to the model); merged by `c08a4952e`.
- `8f2f1f980` — 48160 fix(ai): repair migration graph after 49034 merge (earlier backend change; not part of this frontend-only review round).
