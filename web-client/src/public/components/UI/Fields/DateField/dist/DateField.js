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
exports.DateField = void 0;
/* eslint-disable jsx-a11y/label-has-associated-control */
var React = require("react");
var classnames_1 = require("classnames");
var react_intl_1 = require("react-intl");
<<<<<<< HEAD
var react_datepicker_1 = require("react-datepicker");
require("react-datepicker/dist/react-datepicker.css");
var getForegroundClass_1 = require("../common/utils/getForegroundClass");
var DateField_css_1 = require("./DateField.css");
var styles_css_1 = require("../common/styles.css");
var icons_1 = require("../../../icons");
=======
var icons_1 = require("../../../icons");
var getForegroundClass_1 = require("../common/utils/getForegroundClass");
var DatePicker_1 = require("../../form/DatePicker");
var DateField_css_1 = require("./DateField.css");
var styles_css_1 = require("../common/styles.css");
>>>>>>> 3073__frontend_dates_translation
var inputContainerSizeClassMap = {
    sm: DateField_css_1["default"]['container_sm'],
    md: DateField_css_1["default"]['container_md'],
    lg: DateField_css_1["default"]['container_lg']
};
function DateField(_a) {
    var _b = _a.icon, icon = _b === void 0 ? React.createElement(icons_1.DateIcon, null) : _b, className = _a.className, title = _a.title, _c = _a.fieldSize, fieldSize = _c === void 0 ? 'lg' : _c, _d = _a.foregroundColor, foregroundColor = _d === void 0 ? 'white' : _d, errorMessage = _a.errorMessage, isRequired = _a.isRequired, children = _a.children, containerClassName = _a.containerClassName, disabled = _a.disabled, placeholder = _a.placeholder, value = _a.value, onChange = _a.onChange, 
    // tslint:disable-next-line: trailing-comma
    props = __rest(_a, ["icon", "className", "title", "fieldSize", "foregroundColor", "errorMessage", "isRequired", "children", "containerClassName", "disabled", "placeholder", "value", "onChange"]);
    var messages = react_intl_1.useIntl().messages;
    var normalizedErrorMessage = errorMessage && (messages[errorMessage] || errorMessage);
    var renderInput = function () {
        var inputClassName = classnames_1["default"](DateField_css_1["default"]['input-field'], icon && DateField_css_1["default"]['input-field_with-icon'], errorMessage && DateField_css_1["default"]['input-field_error'], className);
        return (React.createElement("div", { className: DateField_css_1["default"]['input-with-rigt-content-wrapper'] },
            React.createElement("div", { className: inputClassName },
<<<<<<< HEAD
                React.createElement(react_datepicker_1["default"], __assign({ onChange: onChange, placeholderText: placeholder, selected: value, showPopperArrow: false }, props))),
=======
                React.createElement(DatePicker_1.DatePicker, __assign({ onChange: onChange, placeholderText: placeholder, selected: value, showPopperArrow: false }, props))),
>>>>>>> 3073__frontend_dates_translation
            icon && React.createElement("div", { className: DateField_css_1["default"]['icon'] }, icon)));
    };
    var titleClassNames = classnames_1["default"](DateField_css_1["default"]['title'], getForegroundClass_1.getForegroundClass(foregroundColor), isRequired && styles_css_1["default"]['title_required']);
    return (React.createElement("label", { className: classnames_1["default"](DateField_css_1["default"]['container'], inputContainerSizeClassMap[fieldSize], disabled && DateField_css_1["default"]['container_disabled'], title && DateField_css_1["default"]['container_with-title'], containerClassName) },
        renderInput(),
        title && React.createElement("span", { className: titleClassNames }, title),
        normalizedErrorMessage && React.createElement("p", { className: DateField_css_1["default"]['error-text'] }, normalizedErrorMessage),
        children));
}
exports.DateField = DateField;
