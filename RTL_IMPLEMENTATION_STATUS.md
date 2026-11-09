# Syrian Arabic and RTL implementation

Implementation and verification record for the current branch. This accompanies
`RTL_IMPLEMENTATION_GUIDE.md`; it does not turn the guide's untested release gates
into completed checks.

## Direction and layout

- The persisted/API language is `ar-sy`; HTML and Intl use `ar-SY`, and Django
  catalogues use `ar_SY`. Existing frontend aliases `ar`, `ar_SY` and `ar-SY`
  resolve to Syrian Arabic.
- Server-rendered application and public-form HTML receive `lang` and `dir`.
  The browser reconciles its supported language before React renders and updates
  document direction and Moment together when the language changes.
- Authored spacing, borders, positioning and alignment use CSS logical properties.
  Existing dimensions, breakpoints, colors and page structure are retained.
  The dormant Gogo `.rtl` theme is not enabled; there is no automatic stylesheet
  mirror or blanket transform.
- Shared controls handle select direction, popover placement, modal motion,
  slider direction and table resizing at their owning component boundaries.
  Popper placements are resolved once; Floating UI's native RTL handling is retained.
- The workflow graph keeps its coordinate system while its cards and controls use
  the selected language. Rich-text prose uses native content direction; technical
  URLs, code, email and telephone values retain readable LTR direction.
- Native `:dir()` is intentional for mixed content with `dir="auto"`.
  PostCSS must not rewrite it to ancestor attribute selectors.

## Arabic and typography

- `frontend/src/public/lang/locales/ar-SY.ts` contains explicit Arabic messages,
  with ICU arguments checked against English. Arabic plural forms are used for
  the task counters that previously relied on three-form language rules.
- User-facing strings encountered outside the dictionary were moved into the
  existing React Intl flow, including browser page titles. Analytics identifiers
  stay stable. User-authored workflow names, descriptions and other stored content
  are preserved.
- The four supplied Hayyakum Allah WOFF2 files are self-hosted as real weights
  300, 400, 500 and 700. Arabic selects this family through shared font variables;
  English retains the original font families.
- Moment and date-fns use Syrian month names. Display dates remain parseable
  after a language change. API dates and durations retain machine-readable ASCII
  formatting. The user's timezone and first-day-of-week preferences are retained;
  `Asia/Damascus` is an available timezone.
- The backend accepts `ar-sy` without changing its existing Russian-language
  deployment policy. Migration `0147_user_language_ar_sy` updates the language
  choices. Thirteen `ar_SY` catalogues provide 359 translated messages.
- Browser API requests include normalized `Accept-Language` unless the caller
  supplies it. Backend authentication still uses the stored user language.

## Running the changed application

1. To make Syrian Arabic the deployment default, set this in the local `.env`:

   ```dotenv
   LANGUAGE_CODE=ar-sy
   ```

   Keep `en` if the default should remain English. No credentials or other local
   settings need changing for RTL.

2. Rebuild and recreate the Compose services from the repository root:

   ```powershell
   docker compose up -d --build
   ```

   The existing backend startup runs migrations and compiles translation catalogues.
   This implementation has not restarted or rebuilt the user's Compose services.

3. Existing users select **العربية (سوريا)** in their profile, save, then refresh.
   A legacy stored `ar` value is normalized for frontend rendering, but the backend
   must receive the canonical saved `ar-sy` value to activate the Syrian catalogue.
   Changing the deployment default does not overwrite existing users' preferences.

## Verification performed

- Production webpack compilation, with normal minification enabled: passed.
  Existing Sass deprecations and asset-size warnings remain.
- Source TypeScript check: `tsc --noEmit --skipLibCheck` passed. A plain
  `tsc --noEmit` still reports the installed react-datepicker declaration problems
  (`PropsWithChildren` and `react-onclickoutside`); application source checks pass.
- Focused Jest groups cover locale resolution, ICU catalogue completeness,
  Arabic display/API date separation, editable Syrian months, plurals, shared
  controls, editor behavior, rich-text rendering, table resizing and Axios headers.
  The final eight-suite integration/catalogue group passed 1,686 assertions/tests
  (many are per-message ICU checks). Editor/rich-text regressions passed 105 suites
  and 868 tests; the title-related group passed 40 suites and 318 tests. These
  groups overlap and must not be added into a unique full-suite total.
- Changed frontend source ESLint has no errors; existing warnings remain.
  Changed CSS/PCSS Stylelint and `git diff --check` passed.
- Backend language tests: six database-free tests passed:

  ```powershell
  docker compose exec -T backend python manage.py test src.accounts.tests.test_language --verbosity 1
  docker compose exec -T backend python manage.py compilemessages -l ar_SY
  ```

  Catalogue compilation passed. `makemigrations --check --dry-run` still reports
  unrelated existing model/migration drift; it reports no User.language drift.
  No unrelated migration was generated or applied during this work.

- Chrome checks cover real application pages in both directions and mobile/desktop
  widths, plus isolated editor, mixed-text, graph, popup and vendor-switch geometry.
  Isolated English CSS is compared against the explicitly selected earlier ref.
  All four font files were loaded in browser checks.
- Final anonymous production checks passed all 16 states: sign-in, forgot password,
  the missing-reset-link guard and the genuine missing-public-form error, each in
  English/Arabic at 1280/375 widths. They checked document language/direction,
  fonts, horizontal overflow, technical email direction and localized auth titles.
  No login, password reset request or successful public submission was performed.
- Isolated vendor checks passed all 16 switch states plus their thumb animations.
  Twenty-four real Tippy/Popper sidebar cases checked both placements, collision
  flips, arrow centering and dismissal, with unchanged earlier LTR geometry.

Standalone browser commands, authentication setup and their exact scope are in
[`frontend/tests/e2e/RTL_README.md`](frontend/tests/e2e/RTL_README.md). These `.cjs`
checks are not discovered by the default Playwright test glob.

## Remaining release checks and environment findings

- The authenticated page matrix has 25 loaded cases out of 32 planned cases.
  Additional profile and control checks cover both directions at 1440/390 widths.
  A new authenticated run is required after the final harness assertion changes;
  syntax checks do not substitute for that run.
- No saved preference, template save, task submission or other content mutation
  was exercised. The local account has no populated workflow/task/template data;
  synthetic geometry fixtures do not replace those real data cases.
- A successful public/embedded form submission, guest task, printed workflow,
  and Firefox/WebKit checks remain release gates. The anonymous public-form error
  state is tested separately and does not prove a successful form flow.
- The current backend returns 404 for `/navigation/menu/help-center` in both
  directions. A trailing slash on an invalid public-form token can leave the
  existing forms route without a response. These are recorded environment/existing
  routing findings; neither is treated as successful application coverage.
- Temporary test authentication expired. Automatic approval review rejected
  rotating privileged test-session credentials without explicit user approval;
  no replacement credential was created. The user explicitly chose to finish
  without a new session. Authenticated checks were therefore not resumed, and
  the remaining cases are recorded as unverified. They can be checked manually
  by the user after rebuilding, without creating an agent-managed session.

Screenshots and reports are local ignored test artifacts, not approved visual
baselines. This record does not claim zero defects on every page and browser.
