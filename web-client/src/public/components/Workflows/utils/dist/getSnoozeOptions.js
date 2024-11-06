"use strict";
exports.__esModule = true;
exports.getSnoozeOptions = void 0;
var moment_timezone_1 = require("moment-timezone");
function getSnoozeOptions(formatMessage, timezone) {
    var today = moment_timezone_1["default"].tz(timezone);
    var snoozeSettings = [
        {
            title: formatMessage({ id: 'snooze.day' }),
            calcDate: function () { return today.add(1, 'day'); }
        },
        {
            title: formatMessage({ id: 'snooze.week' }),
            calcDate: function () { return today.add(1, 'week'); }
        },
        {
            title: formatMessage({ id: 'snooze.month' }),
            calcDate: function () { return today.add(1, 'month'); }
        },
    ];
    var snoozeOptions = snoozeSettings.map(function (_a) {
        var title = _a.title, calcDate = _a.calcDate;
        var date = calcDate();
        return {
            title: title,
            dateString: date.format('MMMM d'),
            dateISOString: date.format()
        };
    });
    return snoozeOptions;
}
exports.getSnoozeOptions = getSnoozeOptions;
