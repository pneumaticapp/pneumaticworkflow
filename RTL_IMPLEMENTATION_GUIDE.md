# RTL implementation guide for AI coding agents

## Purpose and activation

This is a repository-specific implementation specification for complete,
maintainable bidirectional UI support, including Arabic, in Pneumatic Workflow.
Read this document before implementing RTL. Reading it does not authorize code
changes: follow the user's current request and scope. If asked only to review or
plan, remain read-only. When implementation is requested, work through the
milestones and their validation gates; do not request routine permission at every
milestone when the work is already authorized.

The goal is to preserve the design's spacing, hierarchy, readability, and
interactions in both LTR and RTL. Correct RTL is a semantic adaptation of the UI,
not a horizontal reflection of every element.

Keep three concerns distinguishable in changes and evidence:

1. Direction support: layout, placement, interaction, and mixed-direction content.
2. Localization: catalogues, language selection, plurals, dates, and numbers.
3. Ministry of Housing branding: logos, colors, typography, and visual identity.

Complete the authorized concerns. Do not silently expand an RTL task into a
redesign or a framework upgrade. Branding can follow stable direction support;
repeat visual validation when the final branding font and assets are applied.

## Starting conditions and evidence limits

The source audit was performed on 2026-11-09 on `ministry-housing-branding`,
created from `master`. These are historical observations, not permanent facts.
Reinspect the current branch, instructions, dependencies, and working tree.

- The active frontend locales were English and Russian, both LTR.
- `ELocaleDirection.RightToLeft` existed, but the application did not centrally
  activate document direction.
- The Gogo Sass theme contained a substantial `.rtl` block. The theme import
  graph compiled repeated RTL rules and included many `!important` declarations.
  Its existence did not demonstrate support for the current custom components.
- A static scan found 689 physical-direction declarations in 180 of 267 scanned
  CSS files, excluding the vendor, font, and Sass theme directories. The scan
  did not include every shorthand, transform, or JavaScript calculation. These
  counts are an inventory signal, not a count of defects.
- Application CSS uses CSS Modules; legacy theme rules use global selectors.
  Check the emitted selectors and actual cascade rather than assuming they match.
- The bundled Bootstrap stylesheet identified itself as version 4.3.1.
- CSS and Sass had different webpack loader chains. Sass did not pass through
  `postcss-loader`; the PostCSS configuration contained no RTL transformation.
- Playwright, Storybook, and Jest infrastructure already existed. The inspected
  E2E tests did not provide RTL visual baselines.

This audit was source-based. It did not establish that any complete RTL screen
was visually correct in a running browser. Do not represent these observations
as implementation results or passing runtime tests.

## Repository map

Paths below are relative to the repository root. Revalidate them before editing.

| Area                              | Files or directories to inspect                                                                                                                                                                        | Why                                                                                                                                     |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------- |
| Server-rendered application shell | `frontend/src/server/handlers/mainHandler.ts`, `frontend/src/server/middleware/authMiddleware.ts`, `frontend/src/public/index.ejs`                                                                     | User language arrives through server locals; initial HTML must agree with client language resolution. Preserve authentication behavior. |
| Public forms shell                | `frontend/src/server/server.ts`, `frontend/src/public/forms.ejs`, `frontend/src/public/forms.tsx`                                                                                                      | Forms have their own rendering path and entry point. They previously selected `defaultLocale` directly.                                 |
| Client locale state               | `frontend/src/public/redux/settings/reducer.ts`, `frontend/src/public/constants/defaultValues.ts`, `frontend/src/public/types/redux.ts`, `frontend/src/public/lang/`                                   | Define supported locales, precedence, direction metadata, and catalogues coherently.                                                    |
| Application lifecycle             | `frontend/src/public/browser.tsx`, `frontend/src/public/components/App/App.tsx`                                                                                                                        | Initialization, language switching, error boundary, and Moment locale side effects.                                                     |
| Build and global styles           | `frontend/webpack.config.js`, `frontend/postcss.config.ts`, `frontend/src/public/assets/css/style.css`                                                                                                 | CSS Modules, vendor imports, loader ordering, and stylesheet cascade.                                                                   |
| Legacy theme                      | `frontend/src/public/assets/css/sass/themes/gogo.light.yellow.scss`, `frontend/src/public/assets/css/sass/_pneumatic-styles.scss`, `frontend/src/public/assets/css/sass/_gogo.style.scss`              | Repeated imports, global layout rules, dormant `.rtl` selectors, and specificity.                                                       |
| Shell and navigation              | `frontend/src/public/layout/`, `frontend/src/public/components/Sidebar/`, `frontend/src/public/components/TopNav/`                                                                                     | Sidebar offsets, collapsed and mobile states, navigation alignment.                                                                     |
| Shared controls                   | `frontend/src/public/components/UI/`                                                                                                                                                                   | Fix reusable behavior before patching individual pages.                                                                                 |
| Template editor                   | `frontend/src/public/components/TemplateEdit/`                                                                                                                                                         | Columns, insert-variable controls, field lists, and graph/line views.                                                                   |
| Rich text                         | `frontend/src/public/components/RichEditor/`                                                                                                                                                           | Paragraph direction, lists, checklists, floating forms, mentions, and serialization.                                                    |
| Workflow tables                   | `frontend/src/public/components/Workflows/WorkflowsTablePage/WorkflowsTable/`                                                                                                                          | Column ordering, resize handles, sticky controls, and horizontal scrolling.                                                             |
| Dates and serialization           | `frontend/src/public/hooks/useDatePickerSettings.ts`, `frontend/src/public/components/UI/form/DatePicker/`, `frontend/src/public/utils/dateTime.ts`, `frontend/src/public/utils/strings.ts`            | Visible localization must not corrupt machine-readable values.                                                                          |
| Portaled UI                       | `frontend/src/public/components/UI/BaseModal/`, `frontend/src/public/components/UI/SideModal/`, `frontend/src/public/components/NotificationsList/`, `frontend/src/public/components/FullscreenImage/` | Content can be mounted directly under `document.body`, outside a page wrapper.                                                          |
| Public and print output           | `frontend/src/public/components/PublicFormsApp/`, `frontend/src/public/assets/css/print/print.css`                                                                                                     | Separate entry points, embedding contexts, and printed workflow output.                                                                 |
| Test infrastructure               | `frontend/playwright.config.ts`, `frontend/tests/e2e/`, `frontend/jest.config.js`, `frontend/.storybook/`                                                                                              | Extend existing infrastructure; do not substitute source assertions for browser rendering evidence.                                     |
| Persisted language, when in scope | `backend/src/accounts/enums.py`, `backend/src/accounts/models.py`, `backend/src/accounts/serializers/user.py`, `backend/src/settings.py`                                                               | Frontend locale options and API validation must agree when introducing Arabic as a saved language.                                      |

## Architecture decisions

### One document direction, explicit local exceptions

- Resolve supported locale and direction from a shared, explicit definition.
  Normalize only supported aliases and provide a deterministic fallback.
- Preserve existing language precedence unless a change is required and explained.
  The audited client used saved user language, then environment configuration,
  then local storage, then the application default, checking support at each step.
- Account for the server not being able to read browser local storage. Design a
  deliberate first-paint reconciliation strategy; do not claim exact server/client
  agreement merely because both call similarly named functions.
- Set `lang` and `dir` on `<html>`, including initial server output where feasible.
  Avoid a visible LTR first paint followed by an RTL layout jump.
- Keep runtime switching, logout, reload, guest access, and public forms consistent.
- Use the document direction for portaled UI. A class on an inner application
  wrapper alone does not cover elements mounted under `body`.
- Local exceptions should express intent: technical text, independently directed
  user content, or a physical coordinate surface.
- Ensure initialization and error states outside `IntlProvider` can still render.
  Do not add provider-dependent hooks to such components without addressing scope.

### Logical CSS for application-owned layout

Prefer logical properties where the design means start/end:

| Existing physical intent                   | Direction-aware expression                     |
| ------------------------------------------ | ---------------------------------------------- |
| Space after an icon at inline start        | `margin-inline-end` or a suitable parent `gap` |
| Space reserved for a trailing field button | `padding-inline-end`                           |
| Trailing edge of a field or drawer         | `inset-inline-end`                             |
| Leading text alignment                     | `text-align: start`                            |
| Trailing text alignment                    | `text-align: end`                              |
| Separator at the end of a column           | `border-inline-end`                            |

Convert by design intent, not search-and-replace. Inspect asymmetric `margin`,
`padding`, border-radius shorthands, pseudo-elements, transforms, transitions,
keyframes, and responsive overrides as well as named left/right properties.

Examples requiring special care:

- `left: 50%` paired with `translateX(-50%)` is a centering equation. Preserve the
  pair or deliberately implement and test its replacement.
- Flexbox and Grid already respond to direction. Adding `row-reverse`, DOM
  reversal, or CSS ordering can produce a second reversal and accessibility issues.
- An input clear button and its reserved text padding must move together.
- A drawer's anchor, rounded corners, and entrance/exit motion must agree.
- Layout direction and content direction can differ. Apply `dir="auto"` to the
  text-bearing element, not indiscriminately to an icon-and-label layout wrapper.

Retain physical properties when they intentionally describe screen coordinates.
Document these exceptions so later automated cleanup does not break them.

### A bounded legacy compatibility layer

Inspect which legacy selectors actually affect the live UI and their specificity.
Use a small, deliberate compatibility layer for necessary global/vendor rules.
Do not enable the entire `.rtl` theme block without evaluating its effects.

Do not combine unreviewed legacy RTL overrides, blanket CSS mirroring, and manual
component flips. Each directional rule must have a clear owner.

A blanket RTL transform across all application and `node_modules` styles is not
the default strategy. If a build-time transform is justified for a bounded legacy
stylesheet, document its scope, exclusions, specificity, bundle impact, and
browser evidence. It must not reinterpret JavaScript-generated coordinates.

Review duplicate theme imports before changing them. A deduplication can alter
the cascade; keep that change narrow and compare LTR before and after. Do not
upgrade Bootstrap, Reactstrap, or the editor solely to deliver RTL.

### Direction-aware wrappers for third-party components

Use the versions actually installed, not assumptions from current online docs.
At audit time, key dependencies included Reactstrap 8, React Select 5, Popper 2
alongside Reactstrap's older placement API, React Flow 11, Lexical 0.21,
react-datepicker 7, and rc-slider 9.

- Configure React Select's `isRtl` in its shared wrapper; audit custom subcomponents.
- Distinguish logical menu alignment from physical popup placements. Resolve
  placement exactly once and preserve caller overrides with a clear contract.
- Check Reactstrap/Popper versions per wrapper before changing placement options.
  `start`/`end` are not automatically logical in every API/version.
- Test nested menus, fixed positioning, body portals, overflow containers, scrolling,
  viewport collision handling, and language changes while an overlay is open.
- Preserve positioning-library-owned inline styles and arrow geometry unless the
  positioning code itself is being changed coherently.
- Configure sliders' reverse behavior when the product semantics require it;
  test mouse, touch, and keyboard, including min/max meaning.
- Test date-picker navigation, weekday order, popup alignment, and clear controls.
- Audit custom scrollbar styles; do not move a scrollbar rail independently of
  the library's measurements or obscure content to suppress overflow.

### Preserve geometry and user content

Workflow tables:

- `utils/resizeUtils.ts` originally calculated `clientX - startX` without direction.
  If the resizing edge moves, make width delta reflect the active direction.
- Test growth and shrinkage in both directions, min width, persisted widths,
  reload, sticky controls, first/last-column borders, and horizontal scrolling.
- Account for RTL scroll offsets when doing arithmetic with `scrollLeft`.

Template graph:

- Treat React Flow's canvas, node coordinates, handles, edge paths, and stored
  positions as one coordinate system. Do not globally mirror them with CSS.
- An isolated physical canvas with localized card content is a valid approach.
  Keep surrounding toolbars, menus, panels, and labels direction-aware.
- Any requested graph-geometry mirroring is a separate deliberate algorithmic
  change with connection, collision, dragging, and persistence tests.

Rich editor and content:

- Lexical already detects paragraph direction. Preserve that behavior; verify
  list markers, checklist controls, indentation, placeholders, and empty paragraphs.
- Review `hooks/useFloatingFormPosition.ts`, `hooks/useLinkFormState.ts`, and
  mention positioning. They use DOM rectangles, physical `left`, and scroll offsets.
- Test mixed paragraphs, cursor movement, selection, copy/paste, mentions, links,
  variables, attachments, and undo/redo. Do not rewrite stored text to force direction.
- Content is converted through Markdown/plain-text converters. Test save/reload
  and rendered output as well as the in-editor view.
- Isolate unknown-direction inline values with suitable `bdi`/`dir="auto"`
  markup. Use explicit direction for known technical content where appropriate.
- Preserve the deliberate filename truncation behavior in `Attachments.css`;
  its existing RTL/LTR combination is not evidence of page-level RTL support.
- Mirror directional navigation icons intentionally. Preserve brand marks, photos,
  checkmarks, media content, and physical graph connectors according to meaning.

Typography and localization:

- Use a properly declared Arabic-capable font with verified weights, coverage,
  and fallback behavior. Prefer explicit font tokens; avoid disguising a system
  font as an unrelated existing font family to patch scattered styles.
- Inspect fixed control heights, line height, diacritics, letter spacing,
  truncation, wrapping, and long labels using the selected font.
- Do not use global `white-space: nowrap`, hidden page overflow, arbitrary width
  increases, or smaller fonts to hide layout defects.
- Keep visible date/number localization separate from API serialization.
  Moment's global locale can affect `.format()` and duration output: validate
  ASCII machine formats, ISO dates, editable time values, and round trips.
- When Arabic localization is included, use a separate catalogue, preserve ICU
  arguments/tags, implement Arabic plural categories, and translate visible
  hardcoded UI text. Do not overwrite English or translate stored user data.
- Check backend language choices, serializers, settings, and necessary migrations
  only when adding a persisted locale. Pure direction support does not itself
  require a database change. Preserve existing deployment language policies.

## Execution milestones and gates

Run milestones sequentially; shared primitives precede page-specific fixes.
Keep changes reviewable and separate unrelated cleanup. Commit or publish only
when requested. Do not restore a previously rejected implementation or stash
without an explicit reason within the current authorization.

| Milestone                           | Deliverable                                                                                                            | Required evidence before calling it complete                                                                |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| 0. Reinspect and establish baseline | Current branch/status, route/component inventory, existing LTR screenshots, known pre-existing failures                | Baseline behavior and test environment are recorded; user changes are preserved.                            |
| 1. Locale/direction contract        | Shared metadata, initial document attributes, runtime synchronization, entry-point coverage                            | First load, reload, language switching, signed-out and public-form cases agree with the defined precedence. |
| 2. Application shell                | Sidebar, main offsets, top navigation, collapsed/mobile states, bounded legacy compatibility                           | LTR remains visually consistent; RTL shell has correct anchors, spacing, and transitions.                   |
| 3. Shared controls                  | Inputs, buttons, selects, menus, tooltips, tabs, modals, drawers, shared typography                                    | Component cases pass in both directions, including long content and overlays near screen edges.             |
| 4. Template editor vertical slice   | Line editor, info column, fields, insert-variable controls, task sections, validation                                  | The complete page works with real Arabic and mixed content on desktop/mobile.                               |
| 5. Interaction-sensitive surfaces   | Table resizing/scrolling, rich editor, graph, floating forms, date pickers, sliders                                    | Browser interactions, geometry, serialization, and persistence work in both directions.                     |
| 6. Remaining routes and output      | Dashboard, tasks, workflows, team/groups, datasets/fieldsets, settings/profile, integrations, auth/guest, forms, print | Every supported route and applicable state has an evidence-backed status.                                   |
| 7. Regression and handoff           | Automated checks, reviewed visual baselines, final audit, documented exceptions                                        | Acceptance criteria below are met, or remaining gaps are explicitly reported as incomplete.                 |

For route coverage, use the current router as the source of truth. Expand the
inventory if routes have changed; the list above is a starting point.

Track progress in a PR/task report, or update this guide's status only if asked.
Each tracked item should contain: route/component, affected states, LTR evidence,
RTL evidence, viewport/browser, implementation notes, test reference, and status
(`not inspected`, `in progress`, `verified`, or `blocked` with reason).

## Validation strategy

### Evidence layers

1. Static checks: type safety, lint, targeted catalogue/serialization checks, and
   narrowly useful checks for unintended physical CSS. Allow documented coordinate
   exceptions; do not ban every `left`/`right` token mechanically.
2. Component/logic tests: placement resolution, direction-sensitive resize math,
   locale resolution, plural arguments, date round trips, and reusable controls.
3. Real-browser interaction tests: keyboard, pointer, touch where applicable,
   overlays, scrolling, editing, saving, and reloading.
4. Reviewed visual comparisons: separate approved baselines for LTR and RTL.
   Never generate the RTL expected image by flipping the LTR screenshot.

Jest/jsdom and assertions that compiled CSS contains a declaration cannot prove
that an entire rendered page has no overlap or clipping. Screenshot comparisons
also cannot prove correct interaction; use both kinds of evidence.

### Reuse the existing test setup

- Extend `frontend/playwright.config.ts` and relevant `frontend/tests/e2e/` tests.
  It already defines Chromium, Firefox, WebKit, Mobile Chrome, and Mobile Safari.
- Existing global setup reads `E2E_LOGIN_EMAIL` and `E2E_LOGIN_PASSWORD` from the
  frontend environment file and writes authentication state under `tests/e2e/.auth/`.
  Use a designated test account/data; never expose or commit credentials/state.
- Avoid parallel tests racing to change a shared user's saved language or content.
  Use isolated accounts/data or an appropriate isolated test setup.
- Verify the tested origin and image actually serve the edited frontend. The
  Playwright default is port 8000; a running Docker site can use another origin.
- `E2E_USE_EXISTING_SERVER` skips starting the frontend server. Configure this
  intentionally. The existing `npm run local` can kill a process on port 8000.
- Extend Storybook's locale configuration and preview direction for component
  coverage. Apply direction in the preview document so body portals are covered.
- Use stable data, time, viewport, browser version, and font loading for screenshots.
  Review baseline differences; do not auto-accept every changed snapshot.

### Minimum scenario matrix

| Dimension         | Cases                                                                                                                                                                 |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Direction/content | English LTR, actual Arabic RTL, Arabic/English mixed content, unknown-direction user text                                                                             |
| Lifecycle         | Initial response, loading, reload, navigation, switching language, logout/login, guest access                                                                         |
| Width             | Narrow mobile, tablet, desktop, wide desktop, and both sides of each relevant breakpoint; application CSS uses 999/1000 px, while the theme/vendor CSS may use others |
| Navigation        | Sidebar expanded/collapsed, mobile open/close, nested menus, top navigation                                                                                           |
| Data state        | Loading, empty, populated, validation error, permission/disabled state, long and overflowing content                                                                  |
| Forms/content     | Clear/password buttons, date range, checkboxes/radios, mentions, variables, lists, files, URLs, emails, numbers                                                       |
| Interaction       | Mouse/touch as applicable, Tab/Shift+Tab, arrow keys, Escape, selection, resizing, dragging, horizontal scroll                                                        |
| Overlays          | Body portal, nested popup, scrolled container, screen-edge collision, open/close animation                                                                            |
| Output            | Save/reload, API formats, public/embedded form, print preview, exports with localized content where relevant                                                          |

Assert meaningful geometry as well as taking screenshots: field text must not
intersect its buttons, menus must remain usable within the viewport, required
controls must remain reachable, and widths/positions must obey their semantics.
Allow intentional horizontal scrolling in wide tables and coordinate canvases.

### Commands and reporting

Inspect the current package scripts before choosing checks. Useful existing
entry points from `frontend/` include:

```powershell
# Windows PowerShell examples; use npm instead of npm.cmd on other platforms.
npm.cmd test -- --runInBand --runTestsByPath <affected-test-files>
node node_modules/typescript/bin/tsc --noEmit --pretty false
npm.cmd run e2e -- --project=chromium
```

The test-file argument is a placeholder. Select real affected tests. Run the
broader supported-browser and page matrix as the rollout expands. Confirm that
configured projects actually ran and were not skipped.

Use the repository's appropriate production build process to verify final assets.
The audited production script uses POSIX environment assignment, so choose the
equivalent for the current shell. Inspect webpack's reported errors: the audited
`DonePlugin` could exit with code zero even when compilation reported errors.

Record baseline dependency errors separately. Do not silently disable checks or
describe `--skipLibCheck`, a build without minification, source-only checks, or
partial browser coverage as a full production pass.

If a browser/test environment is unavailable, continue useful authorized work
and report exactly which validation remains unavailable. Do not invent visual
evidence or declare the affected milestone verified.

## Completion criteria

- [ ] Locale and direction agree across initial HTML, client state, public forms,
      runtime switching, reload, guest/auth flows, and portaled UI.
- [ ] LTR baseline remains correct; intended RTL adaptation is reviewed visually.
- [ ] Every current route has a coverage status, including relevant responsive,
      loading, empty, error, and long-content states.
- [ ] Shared controls, table resizing, scrolling, overlays, editor interactions,
      graph geometry, and saved positions behave correctly in both directions.
- [ ] Mixed-direction content, the chosen Arabic font, dates/numbers, persisted
      values, and applicable print/export output are verified.
- [ ] No blanket icon/canvas mirroring, double reversal, or overflow masking is
      being used to conceal defects.
- [ ] Direction-sensitive rules have a clear owner; legacy/vendor exceptions and
      any bounded transformation are documented and covered by relevant checks.
- [ ] Meaningful tests, type/lint checks, and the production build are reported
      accurately; skipped, failing, and unavailable checks are distinguished.
- [ ] Translation completeness and linguistic review are reported separately
      from RTL layout correctness when localization is included.
- [ ] The final handoff states changed behavior, evidence, limitations, and any
      required deployment steps. No unverified promise of universal perfection.

Do not call the implementation complete merely because `dir="rtl"` is present,
the catalogue has every key, CSS assertions pass, or one screenshot looks right.

## Reference material

Use repository source and installed dependency types first. Consult official
documentation matching the installed version when behavior is uncertain.

- [W3C: Structural markup and right-to-left text](https://www.w3.org/International/questions/qa-html-dir)
- [W3C: Inline markup and bidirectional text](https://www.w3.org/International/articles/inline-bidi-markup/)
- [CSS Logical Properties and Values specification](https://www.w3.org/TR/css-logical-1/)
- [Playwright: Visual comparisons](https://playwright.dev/docs/test-snapshots)
- [React Select: Props](https://react-select.com/props)
- [React Flow: Handles](https://reactflow.dev/learn/customization/handles)

Online library documentation may describe a newer major version than this
repository uses. Verify compatibility before adopting an example.
