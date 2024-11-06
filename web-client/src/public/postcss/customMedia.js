const { MOBILE_MAX_WIDTH_BREAKPOINT, DESKTOP_MIN_WIDTH_BREAKPOINT } = require('../constants/breakpoints');

module.exports = {
	customMedia: {
		'--mobile': `(max-width: ${MOBILE_MAX_WIDTH_BREAKPOINT}px)`,
		'--desktop': `(min-width: ${DESKTOP_MIN_WIDTH_BREAKPOINT}px)`,
	}
};
