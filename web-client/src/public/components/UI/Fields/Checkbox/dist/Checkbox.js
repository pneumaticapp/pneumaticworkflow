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
exports.FormikCheckbox = exports.Checkbox = void 0;
/* eslint-disable jsx-a11y/label-has-associated-control */
var React = require("react");
var classnames_1 = require("classnames");
var formik_1 = require("formik");
var Checkbox_css_1 = require("./Checkbox.css");
var styles_css_1 = require("../common/styles.css");
// A checkbox can be controlled either with "checked" or "triState" prop.
// The difference is that the triState prop provides an indeterminate checkbox state.
function Checkbox(_a) {
    var title = _a.title, isRequired = _a.isRequired, containerClassName = _a.containerClassName, labelClassName = _a.labelClassName, titleClassName = _a.titleClassName, checked = _a.checked, disabled = _a.disabled, triState = _a.triState, props = __rest(_a, ["title", "isRequired", "containerClassName", "labelClassName", "titleClassName", "checked", "disabled", "triState"]);
    var checkboxRef = React.useRef(null);
    React.useEffect(function () {
        if (!triState || !checkboxRef.current)
            return;
        var handleUpdateCheckboxTriState = function (checkbox) {
            var syncMap = {
                checked: function () {
                    checkbox.checked = true;
                    checkbox.indeterminate = false;
                },
                empty: function () {
                    checkbox.checked = false;
                    checkbox.indeterminate = false;
                },
                indeterminate: function () {
                    checkbox.checked = false;
                    checkbox.indeterminate = true;
                }
            };
            syncMap[triState]();
        };
        handleUpdateCheckboxTriState(checkboxRef.current);
    }, [triState]);
    var titleClassNames = classnames_1["default"](Checkbox_css_1["default"]['checkbox__title'], isRequired && styles_css_1["default"]['title_required'], titleClassName);
    return (React.createElement("div", { className: classnames_1["default"](Checkbox_css_1["default"]['checkbox__container'], containerClassName) },
        React.createElement("label", { className: classnames_1["default"](Checkbox_css_1["default"]['checkbox'], labelClassName) },
            React.createElement("input", __assign({ onClick: function (e) { return e.stopPropagation(); }, type: "checkbox", className: Checkbox_css_1["default"]['checkbox__input'], checked: checked, disabled: disabled }, props, { ref: checkboxRef })),
            React.createElement("div", { className: Checkbox_css_1["default"]['checkbox__box'] }),
            title && React.createElement("p", { className: titleClassNames }, title))));
}
exports.Checkbox = Checkbox;
function FormikCheckbox(_a) {
    var name = _a.name, restProps = __rest(_a, ["name"]);
    var field = formik_1.useField({ name: name, type: 'checkbox' })[0];
    return React.createElement(Checkbox, __assign({}, field, restProps));
}
exports.FormikCheckbox = FormikCheckbox;
