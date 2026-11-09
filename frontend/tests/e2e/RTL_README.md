# RTL browser checks

These `.cjs` files are standalone Node scripts. Default Playwright and Jest discovery,
including `npm run e2e`, does **not** run them. Run the commands below from `frontend/`
after installing the project's dependencies. They use an installed Google Chrome
(`channel: 'chrome'`); installing Playwright's bundled Chromium alone is insufficient.
`rtl-pages.cjs` also accepts `RTL_CHANNEL`.

## Isolated checks: no server or authentication

```powershell
# Replace this with an approved Git ref from before the changes being compared.
$env:RTL_BASELINE_REF = 'approved-ltr-base-ref'
node src/public/components/TemplateEdit/__tests__/rtl.geometry.cjs
node src/public/components/RichText/__tests__/rtl.geometry.cjs
node tests/e2e/rtl-sidebar.cjs
node tests/e2e/rtl-legacy.cjs
```

The two component checks and submenu check require an explicit `RTL_BASELINE_REF` and use `git show`
to read the earlier CSS. They never choose or approve a baseline automatically.
`HEAD` is appropriate only when it still contains the approved earlier CSS and the
changes under review are uncommitted. On a committed branch, select the earlier
approved commit; using the current commit would compare its CSS with itself.
The legacy widget check compares vendor CSS with and without the direction patch
and does not require a Git baseline. Component screenshots go to the OS temporary
directory; legacy results go to `test-results/rtl-legacy/`. The submenu fixture
loads the actual installed Tippy/Popper and source CSS without authentication,
checks both placements and edge flips, and verifies mouse-leave closes the popup.
Its report/screenshots go to `test-results/rtl-sidebar/`. Existing right-side
geometry is compared against the approved baseline; left-side arrow geometry is
checked against explicit border/center/dimension invariants.

## Anonymous production checks: no account or session

Start the production frontend and its backend before running this script. Restart
the owned frontend test server after rebuilding: its production EJS view cache can
otherwise reference asset hashes removed by the new build. Configure the server's
default `LANGUAGE_CODE=ar-sy` to verify native Arabic document attributes.

```powershell
$env:RTL_BASE_URL = 'http://localhost:8000'
$env:RTL_PUBLIC_API_URL = 'http://localhost:8001'
$env:RTL_LOCALES = 'en,ar-sy'
$env:RTL_WIDTHS = '1280,375'
node tests/e2e/rtl-public.cjs
```

The default run checks 16 states: sign-in, password-reset request, a missing reset
link's redirect, and a genuinely unavailable public form in both locales and at
both widths. `RTL_PUBLIC_ROUTES` can select `signin`, `forgot-password`,
`missing-reset-link`, or `missing-public-form`. The invalid public-form fixture is
`/forms/rtl-nonexistent-fixture` without a trailing slash; backend error responses
are real, and no successful public-form data is fabricated.

The script supplies no authentication state and never signs in, reads credentials,
requests a password reset, submits a form, or saves preferences. It uses fresh
contexts sequentially, blocks writes and external requests, and closes WebSockets
locally. English overrides the client environment locale and initial document
tag; Arabic also checks the unmodified server-rendered `lang` and `dir`.

Assertions cover document direction, localized auth browser titles, technical
email inputs, horizontal overflow, page errors, and all four local Arabic font
weights. English's configured body font remains unchanged; external Google Fonts
are intentionally blocked, so this is not an English font-rendering baseline.
CAPTCHA, OAuth, valid reset links, real form content, submissions, and realtime
delivery are outside this check. Reports/screenshots go to ignored
`test-results/rtl-public/`, or `RTL_OUTPUT_DIR` when supplied. `RTL_CHANNEL` can
override the installed Chrome channel. Review screenshots manually.

## Source application checks: manually supplied session

Start the edited frontend on the intended origin, with its backend reachable.
The default origin is `http://localhost:8000`. Supply an existing, isolated test
account's Playwright `storageState` JSON. The scripts never sign in or create tokens.
If a new state file is needed, the **user** can open a recorder and sign in manually:

```powershell
npx playwright codegen --channel=chrome --save-storage=tests/e2e/.auth/rtl-session.json http://localhost:8000
```

Close the recorder after manually signing in. Keep this file local and ignored;
it contains session credentials. Do not commit it, print it, or put passwords or
tokens in these scripts. Authentication must match the configured source origin.

```powershell
$env:RTL_BASE_URL = 'http://localhost:8000'
$env:RTL_AUTH_STATE = 'tests/e2e/.auth/rtl-session.json'
$env:RTL_LOCALES = 'en,ar-sy'
$env:RTL_WIDTHS = '1280,375'
node tests/e2e/rtl-pages.cjs

$env:RTL_LOCALE = 'ar-sy'
$env:RTL_WIDTH = '375'
$env:RTL_SCENARIO = 'profile'
node tests/e2e/rtl-controls.cjs
$env:RTL_SCENARIO = 'nested'
node tests/e2e/rtl-controls.cjs
```

Repeat both controls scenarios with `RTL_LOCALE=en` and at desktop width. Controls
accept `en`/`ar-sy` and `profile`/`nested`; `RTL_STORAGE_STATE` overrides
`RTL_AUTH_STATE` for this script if supplied. Relative state paths resolve from
`frontend/`. The page script supports an optional comma-separated `RTL_ROUTES`
filter containing `dashboard`, `tasks`, `templates`, `team`, `profile`,
`integrations`, `template-line-fixture`, or `template-graph-fixture`. Unknown or
empty selections fail; leave the variable unset to run every route.

The application checks intercept locale selection for inspection, block HTTP
mutations, and close WebSockets locally. They fail on page/request errors, pending
API content, wrong document direction, or missing required controls. One existing
help-center navigation endpoint's 404 is explicitly excluded. They do not verify
persisted preferences, authentication flows, saved content, or realtime delivery.
The nested-menu check uses a local dataset response fixture. Template create and
graph showcase routes use unsaved in-memory source fixtures.

Page screenshots and `report.json` go to `test-results/rtl-pages/` (override with
`RTL_OUTPUT_DIR`); controls screenshots go to ignored `tests/e2e/.auth/rtl-controls/`.
Review screenshots manually. These checks cover specific geometry and interactions;
they are not approved pixel baselines or a complete cross-browser release check.
Every command must exit with code zero before reporting it as passed. Changes to
authenticated assertions require a new authorized run; syntax checks alone do not
verify application behavior.
