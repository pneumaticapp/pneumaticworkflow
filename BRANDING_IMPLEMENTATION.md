# Masarat / مسارات — Ministry identity

Approved display identity for the Ministry of Public Works and Housing
(وزارة الأشغال العامة والإسكان, MOPWH). This change keeps the existing page
structure, responsive breakpoints, RTL behavior and Hayyakum Allah font files.

## Sources of truth

- `frontend/src/public/constants/branding.ts`: Arabic/English product and Ministry
  names and the application home path. It is shared with the Node renderer and
  intentionally contains no image imports.
- `frontend/src/public/assets/css/variables/color.css`: approved CSS palette and
  the existing component color aliases.
- `frontend/src/public/assets/css/sass/_branding.scss`: the same palette for the
  existing Sass theme, including its color calculations.
- `frontend/src/public/constants/brandColors.ts`: equivalent values for SVG/canvas
  consumers that require a concrete color. The palette regression test checks
  these three representations together.
- `frontend/src/public/components/Logo/brandAssets.ts`: frontend-only artwork
  imports. `BrandLockup` renders the supplied eagle with the product name and a
  separate Ministry line.
- `backend/src/branding.py`: backend display names used by admin, API metadata
  and default email rendering. Technical service/API identifiers stay stable.

| Family       | Approved colors                 |
| ------------ | ------------------------------- |
| Forest       | `#428177`, `#054239`, `#002623` |
| Golden Wheat | `#edebe0`, `#b9a779`, `#988561` |
| Deep Umber   | `#6b1f2a`, `#4a151e`, `#260f14` |
| Charcoal     | `#ffffff`, `#3d3a3b`, `#161616` |

HEX is the web source supplied for this implementation. Forest dark is the main
action color; white is its foreground. Gold accents use dark text, and active
sidebar items use gold on deep forest. Existing semantic information colors and
user-specific avatar colors retain their distinct roles. Soft status surfaces
are tints of the approved families.

Measured normal-text contrast includes primary/white **11.38:1**, forest/white
**4.53:1**, gold/dark charcoal **7.64:1**, wheat/charcoal **9.41:1** and
umber/white **11.32:1**. White on gold is **2.37:1** and is not used as the
normal-text pairing for gold actions.

## Artwork and fonts

- Runtime eagles: `frontend/src/public/assets/img/branding/logos/`.
- Flag: `frontend/src/public/assets/img/branding/flags/syrian-flag.svg`.
- Original logo collection: `docs/branding/source/Logos/`; all 90 original files
  were preserved and hash-checked. AppleDouble/system metadata stays on disk but
  is excluded by the scoped source-archive `.gitignore`.
- Supplied eagle paths, colors and proportions are preserved. Its original gold
  is `#b9a77a`; that artwork byte value is retained alongside the separately
  supplied UI gold `#b9a779`.
- The supplied flag retains its original green, white, black and red colors and
  its 900×600 / 3:2 proportions. It is prepared as an asset; no extra flag position
  was inserted into the existing page layout.
- Favicons are derived from the supplied eagle with a deep-forest background;
  the notification badge uses deep umber. PNG and multi-size ICO assets retain
  their existing dimensions. Regenerate them from `frontend/` with:

  ```powershell
  node scripts/generate-brand-favicons.cjs
  ```

- Hayyakum Allah files and weights are unchanged. Official eagles and lockups
  retain their orientation in both LTR and RTL.

## Display scope

The implementation covers shared/auth/system logos, browser titles and initial
HTML titles, locale dictionaries, public-form attribution/home links, CSS and
Sass identity colors, default SVG/chart colors, admin/API documentation, default
SMTP email branding and the static nginx 502 page. Storage API changes are
limited to its four display title/description strings.

Filled actions, radio marks, checkbox marks, selected dates and sidebar states
have explicit foreground/background pairings. Legacy class names such as
`button_yellow` and technical identifiers such as `PNEUMATIC_SUFFIX` remain
compatible; they do not select the visible display name. Analytics event labels
retain their existing identifiers.

Active workflow progress uses forest dark, completed progress uses forest and
overdue progress uses umber. These meaningful marks pass 3:1 contrast on white
and wheat-light tracks; the legacy `Yellow` enum name is retained for compatibility.
The separate duration palette uses dark wheat for its intermediate accent.

## Validation and limits

- Production webpack compilation with normal minification passed. Existing Sass
  deprecations and bundle-size warnings remain.
- Frontend source TypeScript passed with `--skipLibCheck`. The previously noted
  installed dependency declaration issues are outside this branding change.
- Focused controls/workflows/palette regressions: **32 suites / 225 tests**.
- Editor/rich-text/locale/title regressions: **32 suites / 1,884 tests**, including
  per-message ICU assertions and five snapshots. Brand/server-specific groups
  also passed; the groups overlap and are not a unique full-suite total.
- The CSS geometry audit against pre-brand commit `b1758f471` found unchanged
  non-color declarations in 28 existing component/library stylesheets. Logo
  fitting is checked separately within its existing fixed slots.
- Actual React/Chrome logo and populated auth-panel fixtures passed in both
  languages at mobile/desktop widths, including text/link contrast and artwork
  integrity. Static nginx 502 checks passed at 1280/375.
- Populated auth pages show the full 170×40 product/Ministry lockup inside the
  previous 40px-high band with its 80px margin. In one deliberately short Arabic
  copy fixture, this wider logo increases the intrinsic inner block by 3px and
  shifts its copy horizontally by 1.5px. Outer panels and vertical positions
  remain unchanged; the mark/text itself stays within its bounds.
- Backend/static checks passed for Python target syntax, Django template-tag
  balance, catalogue placeholders and original SVG integrity. The eight prepared
  database-free Django tests were **not run** because Docker's Linux-engine pipe
  is unavailable. `msgfmt`/runtime catalogue compilation must also be run when
  the backend is available.
- Anonymous production-browser comparisons use the real EJS/React production
  bundles with explicitly mocked anonymous GET responses. They create no login
  cookies, block writes/external requests and do not contact an application
  backend. They verify visual/client behavior, not backend/authentication success.
  Final comparisons passed **16/16 cases**, with **208 outer-panel measurements**
  and **0px maximum difference** from the preserved pre-brand build. Two separate
  empty-Page Arabic sign-in previews also passed at 1280/375 widths. The populated
  cases assert visible product and full Ministry text inside the logo band.
  See `frontend/tests/e2e/RTL_README.md` for reproducible commands and artifacts.

Existing database `Page`/`EmailTemplate` content, custom account logos, stored
user/workflow names and external CustomerIO templates are not rewritten. They
can still contain operator-selected or upstream branding. External provider,
support, legal, app-store and integration URLs are retained as their actual
destinations; no Ministry email address or public domain was invented.

## Applying the changes

When Docker Desktop is available, rebuild/recreate the services:

```powershell
docker compose up -d --build
```

The existing backend startup runs `collectstatic` and `compilemessages`. These
are needed for the admin/API eagle and updated email translations. No migration
or database-data change is part of this identity implementation.

When that runtime is available, run the prepared renderer/override regressions:

```powershell
docker compose exec -T backend python manage.py test src.notifications.tests.test_branding --verbosity 1
```

For real SMTP delivery, set the operator-owned sender address in `.env`:

```dotenv
DEFAULT_FROM_EMAIL=Masarat <no-reply@your-domain.example>
```

Replace the reserved example domain with your actual mail domain. Compose now
passes this setting to backend/Celery services. The local fallback is
`Masarat <webmaster@localhost>`; mail transport and explicit overrides are
preserved. No email was sent during validation, and no Docker service, account
or login session was created or restarted for this work.
