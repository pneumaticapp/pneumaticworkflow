class Style {}

class Avatar {
  constructor(style, options) {
    this.seed = options.seed;
  }

  toString() {
    return `<svg data-seed="${this.seed}"></svg>`;
  }

  toDataUri() {
    return `data:image/svg+xml;utf8,${encodeURIComponent(this.toString())}`;
  }
}

module.exports = { Avatar, Style };
