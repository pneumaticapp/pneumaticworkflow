"use strict";
exports.__esModule = true;
exports.ExtraFieldDate = void 0;
/* eslint-disable */
/* prettier-ignore */
var classnames_1 = require("classnames");
var React = require("react");
var date_fns_1 = require("date-fns");
var react_datepicker_1 = require("react-datepicker");
require("react-datepicker/dist/react-datepicker.css");
var getFieldValidator_1 = require("../utils/getFieldValidator");
var getInputNameBackground_1 = require("../utils/getInputNameBackground");
var template_1 = require("../../../../types/template");
var icons_1 = require("../../../icons");
var FieldWithName_1 = require("../utils/FieldWithName");
var ExtraFieldDate_css_1 = require("./ExtraFieldDate.css");
var KickoffRedux_css_1 = require("../../KickoffRedux/KickoffRedux.css");
var DATE_STRING_TEMPLATE = 'MM/dd/yyyy';
var getStringFromDate = function (date) { return date_fns_1.format(date, DATE_STRING_TEMPLATE); };
var getDateFromString = function (dateStr) {
    if (!dateStr) {
        return null;
    }
    return date_fns_1.parse(dateStr, DATE_STRING_TEMPLATE, new Date());
};
function ExtraFieldDate(_a) {
    var field = _a.field, _b = _a.field, value = _b.value, name = _b.name, isRequired = _b.isRequired, intl = _a.intl, _c = _a.descriptionPlaceholder, descriptionPlaceholder = _c === void 0 ? intl.formatMessage({ id: 'template.kick-off-form-field-description-placeholder' }) : _c, _d = _a.namePlaceholder, namePlaceholder = _d === void 0 ? intl.formatMessage({ id: 'template.kick-off-form-field-name-placeholder' }) : _d, _e = _a.mode, mode = _e === void 0 ? template_1.EExtraFieldMode.Kickoff : _e, editField = _a.editField, _f = _a.isDisabled, isDisabled = _f === void 0 ? false : _f, labelBackgroundColor = _a.labelBackgroundColor, innerRef = _a.innerRef;
    var handleChangeName = React.useCallback(function (e) {
        editField({ name: e.target.value });
    }, [editField]);
    var handleChangeDescription = React.useCallback(function (e) {
        editField({ description: e.target.value });
    }, [editField]);
    var _g = React.useState(getDateFromString(value)), selectedDate = _g[0], setSelectedDate = _g[1];
    var handleChangeDate = function (date) {
        if (!date) {
            editField({ value: '' });
            setSelectedDate(null);
            return;
        }
        var strDate = getStringFromDate(date);
        editField({ value: strDate });
        setSelectedDate(date);
    };
    var renderProcessRunField = function () {
        var fieldNameClassName = classnames_1["default"](getInputNameBackground_1.getInputNameBackground(labelBackgroundColor), KickoffRedux_css_1["default"]['kick-off-input__name']);
        return (React.createElement("div", { className: classnames_1["default"](ExtraFieldDate_css_1["default"]['run-container'], KickoffRedux_css_1["default"]['kick-off-input__field']), "data-autofocus-first-field": true },
            React.createElement("div", { className: fieldNameClassName },
                React.createElement("div", { className: classnames_1["default"](KickoffRedux_css_1["default"]['kick-off-input__name-text'], 'extra-field-name') }, name),
                isRequired && React.createElement("span", { className: KickoffRedux_css_1["default"]['kick-off-required-sign'] })),
            React.createElement("div", { className: ExtraFieldDate_css_1["default"]['date-input-wrapper'] },
                React.createElement(react_datepicker_1["default"], { onChange: handleChangeDate, placeholderText: descriptionPlaceholder, selected: selectedDate, showPopperArrow: false }),
                React.createElement("div", { className: ExtraFieldDate_css_1["default"]['icon'] },
                    React.createElement(icons_1.DateIcon, null)))));
    };
    var renderField = function () {
        var _a;
        var fieldsMap = (_a = {},
            _a[template_1.EExtraFieldMode.Kickoff] = (React.createElement(FieldWithName_1.FieldWithName, { field: field, descriptionPlaceholder: descriptionPlaceholder, namePlaceholder: namePlaceholder, mode: mode, handleChangeName: handleChangeName, labelBackgroundColor: labelBackgroundColor, handleChangeDescription: handleChangeDescription, validate: getFieldValidator_1.getFieldValidator(field, mode), icon: React.createElement(icons_1.DateIcon, null), isDisabled: isDisabled, innerRef: innerRef })),
            _a[template_1.EExtraFieldMode.ProcessRun] = renderProcessRunField(),
            _a);
        return fieldsMap[mode];
    };
    return renderField();
}
exports.ExtraFieldDate = ExtraFieldDate;
