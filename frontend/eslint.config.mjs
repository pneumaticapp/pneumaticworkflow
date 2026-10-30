import js from '@eslint/js';
import { defineConfig } from 'eslint/config';
import tseslint from 'typescript-eslint';
import jsxA11y from 'eslint-plugin-jsx-a11y';
import reactHooks from 'eslint-plugin-react-hooks';
import eslintReact from '@eslint-react/eslint-plugin';
import eslintConfigPrettier from 'eslint-config-prettier';
import { importX } from 'eslint-plugin-import-x';
import globals from 'globals';

export default defineConfig(
  {
    ignores: ['**/dist/**', 'src/**/*.stories.tsx', 'src/**/*.test.ts', 'src/**/*.test.tsx'],
  },

  {
    linterOptions: {
      reportUnusedDisableDirectives: 'error',
    },
  },

  // Shared: client + server
  {
    files: ['src/**/*.{ts,tsx}'],
    plugins: {
      'import-x': importX,
    },
    settings: {
      'import-x/extensions': ['.ts', '.tsx', '.js', '.jsx'],
      'import-x/cache': {
        lifetime: 'Infinity',
      },
      'import-x/resolver': {
        node: {
          extensions: ['.ts', '.tsx', '.js', '.jsx'],
        },
      },
    },
    extends: [js.configs.recommended, tseslint.configs.recommended],
    rules: {
      'import-x/no-duplicates': 'error',
      'import-x/no-cycle': ['warn', { ignoreExternal: true, maxDepth: 3 }],
      'no-undef': 'off',
      '@typescript-eslint/no-unused-vars': ['error', { args: 'none', ignoreRestSiblings: true, caughtErrors: 'none' }],
      'no-console': 'warn',
      'no-useless-assignment': 'off',

      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-empty-object-type': 'warn',
      '@typescript-eslint/no-unsafe-function-type': 'warn',
      '@typescript-eslint/no-wrapper-object-types': 'warn',
      '@typescript-eslint/ban-ts-comment': 'warn',
      '@typescript-eslint/no-require-imports': 'warn',
      '@typescript-eslint/no-namespace': 'warn',
      '@typescript-eslint/no-duplicate-enum-values': 'warn',
      'preserve-caught-error': 'warn',
    },
  },

  // Browser / React
  {
    files: ['src/public/**/*.{ts,tsx}'],
    plugins: {
      '@eslint-react': eslintReact,
    },
    extends: [jsxA11y.flatConfigs.recommended, reactHooks.configs.flat.recommended],
    languageOptions: {
      globals: globals.browser,
    },
    rules: {
      'jsx-a11y/no-autofocus': 'off',
      'no-param-reassign': 'off',
      'react-hooks/rules-of-hooks': 'warn',
      'react-hooks/exhaustive-deps': 'warn',
      'react-hooks/set-state-in-effect': 'off',
      'react-hooks/refs': 'off',
      'react-hooks/immutability': 'off',
      'react-hooks/use-memo': 'off',
      'react-hooks/purity': 'off',
      'react-hooks/set-state-in-render': 'off',
      'react-hooks/preserve-manual-memoization': 'off',
      '@eslint-react/no-missing-key': 'error',
      '@eslint-react/no-duplicate-key': 'error',
      '@eslint-react/dom-no-unknown-property': 'error',
      '@eslint-react/dom-no-void-elements-with-children': 'error',
      '@eslint-react/dom-no-string-style-prop': 'error',
    },
  },

  // Express / Node
  {
    files: ['src/server/**/*.ts', 'src/index.ts'],
    languageOptions: {
      globals: globals.node,
    },
  },

  eslintConfigPrettier,
);
