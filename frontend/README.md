# Pneumatic web-client

### Configuration
Create a file ".env" with the following values in "frontend" directory:
```shell
# Frontend settings
MCS_RUN_ENV=prod
NODE_OPTIONS=--max-old-space-size=3072
BACKEND_PRIVATE_URL=http://localhost:8001/
BACKEND_URL=http://localhost:8001/
WSS_URL=ws://localhost:8001/
FORM_DOMAIN=form.localhost

# Project settings
SSL=no        # Disable using https
ENVIRONMENT=Production
LANGUAGE_CODE=en # Allowed langs: en, fr, de, es, ru
CAPTCHA=no   # Disable using captcha in forms
ANALYTICS=no # Disable any analytics integrations
BILLING=no   # Disable stripe integration
SIGNUP=yes   # Disable signup page
MS_AUTH=no   # Disable Microsoft auth
GOOGLE_AUTH=no # Disable Google auth
SSO_AUTH=no   # Disable SSO Auth0 auth
EMAIL=no      # Disable send emails
EMAIL_PROVIDER=
AI=no         # Disable AI template generation
AI_PROVIDER=
PUSH=no       # Disable push notifications
PUSH_PROVIDER=
STORAGE=no    # Disable file storage
STORAGE_PROVIDER=
```

### Installation
1. Install node.js v16 directly or use [nvm](https://github.com/nvm-sh/nvm).
3. Install packages with ``npm clean-install``. If an errors occurs, use ``npm i --legacy-peer-deps``
3. Run the development version with the command ``npm run local``
4. Run the production version with the command:
   * ``npm run build-client:prod``
   * ``pm2-runtime start pm2.json``

### Run tests
* `npm t`
