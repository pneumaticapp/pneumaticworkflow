# Frontend — React + TypeScript

## Stack

- React 17.0.2 + TypeScript 5.3.3
- Redux 4.0.4 + Redux Toolkit 2.9.1 + Redux Saga 1.0.5
- Express 4.18.2 (server-side rendering / API proxy)
- Webpack (dual bundles: main app + public forms)
- Axios 1.8.4 (HTTP client)
- React Router DOM 5.0.1
- Lexical 0.21.0 (rich text editor, replacing Draft.js)
- React Intl 6.6.2 (i18n: English + Russian)
- Sentry (error tracking), Firebase (push notifications)

## Project Structure

```
src/
├── index.ts                  # Express server entry point
├── server/                   # Express server (handlers, middleware, utils)
│   ├── handlers/             # OAuth, API proxy, main page renderer
│   └── middleware/           # Auth, SSO, subdomain routing
└── public/                   # Client-side React app
    ├── browser.tsx           # Main app entry point
    ├── forms.tsx             # Public forms entry point (separate bundle)
    ├── api/                  # API client layer (~126 endpoint files)
    ├── redux/                # Redux store (31 feature domains)
    │   └── [domain]/         # saga.ts, reducer.ts, actions.ts, types.ts
    ├── components/           # React components (~63 feature directories)
    ├── views/                # Page-level components (15 directories)
    ├── layout/               # Layout wrappers (17 directories)
    ├── types/                # TypeScript type definitions
    ├── utils/                # Utility functions
    ├── hooks/                # Custom React hooks
    ├── constants/            # Application constants
    └── lang/                 # i18n translations (en-US, ru-RU)
```

## Commands

```bash
# Development
npm run local                    # Start dev server (port 8000)
npm run build-client             # Dev webpack build
npm run build-client:prod        # Production webpack build

# Testing
npm test                         # Jest unit tests
npm run test:prod                # Tests with CI flags
npm run test:editor              # RichEditor component tests
npm run e2e                      # Playwright E2E tests
npm run e2e:ui                   # Playwright in UI mode
npm run e2e:headed               # Playwright headed mode

# Linting
npm run eslint                   # ESLint check
npm run stylelint                # CSS linting
npm run lint                     # Both eslint + stylelint

# Storybook
npm run storybook                # Component stories dev server
npm run chromatic                # Visual regression testing
```

## Code Style

- **ESLint**: airbnb-typescript + prettier — max line 140 chars
- **Prettier**: `.prettierrc.json` — single quotes, trailing commas, semicolons, 120 print width
- **Stylelint**: CSS/SCSS property ordering
- **Husky**: pre-commit hook runs lint-staged (auto-fix ESLint)

## Key Patterns

- **State management**: Redux Saga for side effects, Redux Toolkit for reducers
- **API layer**: Axios with interceptors — auto snake_case↔camelCase mapping, auth header injection
- **Routing**: React Router v5 with `ProtectedRoute`, enum-based route definitions (`ERoutes`)
- **Components**: Container + presentational, functional with hooks, lazy loading via `@loadable/component`
- **Forms**: Formik for form state management
- **AI Template Modal**: `TemplateAIModal` component — multi-line textarea for prompt input, generates templates via backend AI service
- **Config**: Server injects config via `window.__pneumaticConfig`, accessed via `getBrowserConfig()`

## Build

Webpack produces two bundles:
1. **Main** (`browser.tsx`): Full app for authenticated users
2. **Forms** (`forms.tsx`): Lightweight public forms app

Production builds use content hashing, CSS extraction, gzip compression, and Sentry sourcemap uploads.

## Testing

- **Unit**: Jest 29 + @testing-library/react + Enzyme (legacy)
- **Saga tests**: redux-saga-test-plan
- **E2E**: Playwright 1.58 — chromium, firefox, webkit, mobile
- Test config: `jest.config.js`, `playwright.config.ts`
