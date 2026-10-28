class Style {}

class Avatar {
  constructor(style, options) {
    this.seed = options.seed;
  }

  toString() {
    return `<svg data-seed="${this.seed}"></svg>`;
  }
}

module.exports = { Avatar, Style };
