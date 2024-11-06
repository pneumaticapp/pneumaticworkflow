'use strict';
Object.defineProperty(exports, '__esModule', { value: true });

module.exports = {
  process(src, path, config) {
    const relativePath = path.replace(config.rootDir, '');

    return {
      code: `module.exports = ${JSON.stringify(relativePath)}`,
    };
  },
};
