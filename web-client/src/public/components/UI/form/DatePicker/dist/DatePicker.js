"use strict";
var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
var __rest = (this && this.__rest) || function (s, e) {
    var t = {};
    for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p) && e.indexOf(p) < 0)
        t[p] = s[p];
    if (s != null && typeof Object.getOwnPropertySymbols === "function")
        for (var i = 0, p = Object.getOwnPropertySymbols(s); i < p.length; i++) {
            if (e.indexOf(p[i]) < 0 && Object.prototype.propertyIsEnumerable.call(s, p[i]))
                t[p[i]] = s[p[i]];
        }
    return t;
};
exports.__esModule = true;
exports.DatePickerComponent = void 0;
var react_1 = require("react");
var react_datepicker_1 = require("react-datepicker");
var locale_1 = require("date-fns/locale");
var moment_timezone_1 = require("moment-timezone");
require("react-datepicker/dist/react-datepicker.css");
require("../../../../assets/css/library/react-datepicker.css");
function DatePickerComponent(_a) {
    var _b;
    var dateFdw = _a.dateFdw, language = _a.language, timezone = _a.timezone, selected = _a.selected, onChange = _a.onChange, props = __rest(_a, ["dateFdw", "language", "timezone", "selected", "onChange"]);
    var mapLocale = (_b = {},
        _b["en" /* English */] = locale_1.enUS,
        _b["ru" /* Russian */] = locale_1.ru,
        _b);
    return (react_1["default"].createElement(react_datepicker_1["default"], __assign({}, props, { locale: mapLocale[language], selected: 
        // Removing the timezone so that the library does not format the date in the time zone set by the browser
        selected ? moment_timezone_1["default"](selected).tz(timezone, false).format('YYYY-MM-DDTHH:mm:ss') : null, calendarStartDay: dateFdw, utcOffset: timezone, 
        // Setting the selected date as the time zone date set by the user
        onChange: function (value) { return onChange(value ? moment_timezone_1["default"](value).tz(timezone, true).format() : null); } })));
}
exports.DatePickerComponent = DatePickerComponent;
