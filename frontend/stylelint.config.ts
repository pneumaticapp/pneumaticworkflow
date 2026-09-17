/** @type {import('stylelint').Config} */
export default {
  extends: ['stylelint-config-standard', 'stylelint-config-recess-order'],

  // ignoreFiles overrides the default node_modules ignore — keep it explicit.
  // Sass/vendor CSS lives only under assets (legacy Gogo) and is out of scope.
  ignoreFiles: ['src/public/assets/**'],

  // Same tokens PostCSS injects via @csstools/postcss-global-data.
  referenceFiles: 'src/public/assets/css/customMedia/customMedia.css',

  rules: {
    // CSS Modules + BEM (including `&` in nested selectors)
    'selector-class-pattern': '^&?[_a-z0-9]+(?:-[_a-z0-9]+)*(?:--[_a-z0-9]+(?:-[_a-z0-9]+)?)*$',
    'selector-pseudo-class-no-unknown': [true, { ignorePseudoClasses: ['global'] }],
    'property-no-unknown': [true, { ignoreProperties: ['composes', 'field-sizing', 'print-color-adjust'] }],
    // postcss-mixins (not CSS). Stylelint does not expand mixin bodies.
    'at-rule-no-unknown': [true, { ignoreAtRules: ['mixin', 'define-mixin'] }],
    'function-no-unknown': [true, { ignoreFunctions: ['mixin'] }],
    'no-unknown-custom-media': true,

    'declaration-no-important': true,
    'max-nesting-depth': 3,
    'selector-max-compound-selectors': 3,
    'selector-max-specificity': '0,4,0',
    'comment-word-disallowed-list': ['TODO', 'FIXME'],
    'declaration-block-no-redundant-longhand-properties': [true, { ignoreShorthands: ['inset', 'overflow'] }],

    // Nested :hover / :focus / :checked in CSS Modules is not source-order cascade.
    'selector-no-qualifying-type': null,
    'no-descending-specificity': null,
  },
};
