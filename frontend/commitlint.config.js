const COMMIT_TYPES = [
  'feat',
  'fix',
  'docs',
  'style',
  'refactor',
  'perf',
  'test',
  'build',
  'ci',
  'chore',
  'revert',
];

const ignores = [
  (message) => message.startsWith('Merge pull request'),
  (message) => message.startsWith('Merge branch'),
  (message) => message.startsWith('Revert '),
];

const rules = {
  'type-enum': [2, 'always', COMMIT_TYPES],
  'type-empty': [2, 'never'],
  'subject-empty': [2, 'never'],
  'subject-full-stop': [2, 'never', '.'],
  'subject-max-length': [2, 'always', 50],
  'subject-case': [0],
  'scope-case': [0],
};

const featureParserPreset = {
  parserOpts: {
    headerPattern: /^(\d+) (\w+)(?:\(([^)]+)\))?!?: (.+)$/,
    headerCorrespondence: ['ticket', 'type', 'scope', 'subject'],
  },
};

const isFeatureMode = process.env.COMMITLINT_MODE === 'feature';

module.exports = isFeatureMode
  ? {
      parserPreset: featureParserPreset,
      ignores,
      rules,
    }
  : {
      extends: ['@commitlint/config-conventional'],
      ignores,
      rules,
    };
