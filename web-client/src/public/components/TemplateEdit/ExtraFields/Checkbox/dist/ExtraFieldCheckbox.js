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
var __spreadArrays = (this && this.__spreadArrays) || function () {
    for (var s = 0, i = 0, il = arguments.length; i < il; i++) s += arguments[i].length;
    for (var r = Array(s), k = 0, i = 0; i < il; i++)
        for (var a = arguments[i], j = 0, jl = a.length; j < jl; j++, k++)
            r[k] = a[j];
    return r;
};
exports.__esModule = true;
exports.ExtraFieldCheckbox = void 0;
/* eslint-disable */
/* prettier-ignore */
var classnames_1 = require("classnames");
var React = require("react");
var react_input_autosize_1 = require("react-input-autosize");
var getEmptySelection_1 = require("../../KickoffRedux/utils/getEmptySelection");
var validators_1 = require("../../../../utils/validators");
var IntlMessages_1 = require("../../../IntlMessages");
var template_1 = require("../../../../types/template");
var fitInputWidth_1 = require("../utils/fitInputWidth");
var icons_1 = require("../../../icons");
var Checkbox_1 = require("../../../UI/Fields/Checkbox");
var helpers_1 = require("../../../../utils/helpers");
var KickoffRedux_css_1 = require("../../KickoffRedux/KickoffRedux.css");
var ExtraFieldCheckbox_css_1 = require("./ExtraFieldCheckbox.css");
var DEFAULT_OPTION_INPUT_WIDTH = 120;
var DEFAULT_FIELD_INPUT_WIDTH = 120;
function ExtraFieldCheckbox(_a) {
    var _b = _a.field, selections = _b.selections, _c = _b.isRequired, isRequired = _c === void 0 ? false : _c, name = _b.name, value = _b.value, intl = _a.intl, _d = _a.namePlaceholder, namePlaceholder = _d === void 0 ? intl.formatMessage({ id: 'template.kick-off-form-field-name-placeholder' }) : _d, _e = _a.mode, mode = _e === void 0 ? template_1.EExtraFieldMode.Kickoff : _e, deleteField = _a.deleteField, editField = _a.editField, _f = _a.isDisabled, isDisabled = _f === void 0 ? false : _f;
    var selectedOptions = value;
    var fieldNameInputRef = React.useRef(null);
    var optionInputsRefs = React.useRef([]);
    var _g = React.useState(false), isFocused = _g[0], setIsFocused = _g[1];
    React.useEffect(function () {
        optionInputsRefs.current.forEach(function (input) { return fitInputWidth_1.fitInputWidth(input, DEFAULT_OPTION_INPUT_WIDTH); });
    }, [selections]);
    React.useEffect(function () {
        fitInputWidth_1.fitInputWidth(fieldNameInputRef.current, DEFAULT_FIELD_INPUT_WIDTH);
    }, []);
    var _h = React.useState(null), activeOptionIndex = _h[0], setActiveOptionIndex = _h[1];
    var fieldNameErrorMessage = validators_1.validateKickoffFieldName(name) || '';
    var isKickoffFieldNameValid = !Boolean(fieldNameErrorMessage);
    var renderKickoffField = function () {
        var fieldNameClassName = classnames_1["default"](ExtraFieldCheckbox_css_1["default"]['kickoff-create-field-name']);
        return (React.createElement("div", { className: ExtraFieldCheckbox_css_1["default"]['kickoff-create-field-container'] },
            React.createElement("div", { className: fieldNameClassName },
                React.createElement(react_input_autosize_1["default"], { inputRef: function (ref) { return fieldNameInputRef.current = ref; }, inputClassName: classnames_1["default"](ExtraFieldCheckbox_css_1["default"]['kickoff-create-field-name-input'], !isKickoffFieldNameValid && ExtraFieldCheckbox_css_1["default"]['kickoff-create-field-name-input_error']), onChange: handleChangeName, placeholder: namePlaceholder, type: "text", value: name, disabled: isDisabled, onFocus: function () { return setIsFocused(true); }, onBlur: function () { return setIsFocused(false); }, onKeyDown: function (event) {
                        if (event.key === "Enter") {
                            setIsFocused(false);
                            event.currentTarget.blur();
                        }
                    } }),
                isRequired && React.createElement("span", { className: KickoffRedux_css_1["default"]['kick-off-required-sign'] }),
                !isFocused && mode === template_1.EExtraFieldMode.Kickoff && (React.createElement("button", { onClick: function () { var _a; return (_a = fieldNameInputRef.current) === null || _a === void 0 ? void 0 : _a.focus(); }, className: classnames_1["default"](KickoffRedux_css_1["default"]['kick-off-edit-name'], ExtraFieldCheckbox_css_1["default"]['edit-name-button']) },
                    React.createElement(icons_1.PencilSmallIcon, null)))),
            !isKickoffFieldNameValid &&
                React.createElement("p", { className: ExtraFieldCheckbox_css_1["default"]['kickoff-create-field-container__error-message'] },
                    React.createElement(IntlMessages_1.IntlMessages, { id: fieldNameErrorMessage })),
            selections && (React.createElement("ul", { className: ExtraFieldCheckbox_css_1["default"]['kickoff-create-field-options'] }, selections === null || selections === void 0 ? void 0 : selections.map(renderKickoffOption))),
            !isDisabled && (React.createElement("button", { type: "button", className: ExtraFieldCheckbox_css_1["default"]['kickoff-create-field-add-option'], onClick: handleAddOption },
                React.createElement(IntlMessages_1.IntlMessages, { id: "template.kick-off-add-options" })))));
    };
    var renderKickoffOption = function (field, optionIndex) {
        var value = field.value;
        var isActive = optionIndex === activeOptionIndex;
        var errorMessageIntl = validators_1.validateCheckboxAndRadioField(value);
        var shouldShowError = Boolean(errorMessageIntl);
        return (React.createElement("li", { key: optionIndex, className: ExtraFieldCheckbox_css_1["default"]['kickoff-create-field-option'], onMouseOver: function () { return setActiveOptionIndex(optionIndex); }, onMouseLeave: function () { return setActiveOptionIndex(null); } },
            React.createElement("div", { className: ExtraFieldCheckbox_css_1["default"]['kickoff-create-field-option__labeled-checkbox'] },
                React.createElement(Checkbox_1.Checkbox, { title: "", checked: false, disabled: true, id: "extra-field-checkbox-" + optionIndex, containerClassName: ExtraFieldCheckbox_css_1["default"]['labeled-checkbox__checkbox'] }),
                React.createElement("input", { ref: function (el) { return optionInputsRefs.current[optionIndex] = el; }, className: ExtraFieldCheckbox_css_1["default"]['labeled-checkbox__input'], onChange: handleChangeOption(optionIndex), placeholder: namePlaceholder, type: "text", value: value, disabled: isDisabled }),
                React.createElement("span", { className: ExtraFieldCheckbox_css_1["default"]['measure'] }),
                isActive && !isDisabled && (React.createElement("div", { role: "button", className: ExtraFieldCheckbox_css_1["default"]['labeled-checkbox__remove'], onClick: handleRemoveOption(optionIndex) },
                    React.createElement(icons_1.RemoveIcon, null)))),
            shouldShowError &&
                React.createElement("p", { className: ExtraFieldCheckbox_css_1["default"]['kickoff-set-field-option__error-text'] },
                    React.createElement(IntlMessages_1.IntlMessages, { id: errorMessageIntl }))));
    };
    var handleChangeName = React.useCallback(function (e) {
        fitInputWidth_1.fitInputWidth(e.target, DEFAULT_FIELD_INPUT_WIDTH);
        editField({ name: e.target.value });
    }, [editField]);
    var handleDeleteField = React.useCallback(function () {
        if (!deleteField) {
            return;
        }
        deleteField();
    }, [deleteField]);
    var handleAddOption = function () {
        var newOptions = __spreadArrays(selections, [getEmptySelection_1.getEmptySelection()]);
        editField({ selections: newOptions });
    };
    var handleRemoveOption = function (optionIndex) { return function () {
        var newOptions = selections === null || selections === void 0 ? void 0 : selections.filter(function (_, index) { return index !== optionIndex; });
        var isNoOptions = !helpers_1.isArrayWithItems(newOptions);
        isNoOptions
            ? handleDeleteField()
            : editField({ selections: newOptions });
    }; };
    var handleChangeOption = function (optionIndex) { return function (event) {
        var newValue = event.target.value;
        var newOptions = selections === null || selections === void 0 ? void 0 : selections.map(function (option, index) {
            if (index === optionIndex) {
                return __assign(__assign({}, option), { value: newValue });
            }
            return option;
        });
        editField({ selections: newOptions });
    }; };
    var renderProcessRunOption = function (_a) {
        var optionId = _a.id, value = _a.value;
        var isChecked = selectedOptions && selectedOptions.includes(String(optionId));
        return (React.createElement("li", { key: optionId, className: ExtraFieldCheckbox_css_1["default"]['kickoff-set-field-option'] },
            React.createElement(Checkbox_1.Checkbox, { id: String(optionId), title: value, onChange: handleToggleOption(optionId), checked: isChecked })));
    };
    var renderProcessRunField = function () {
        if (!selections) {
            return null;
        }
        var fieldNameClassName = classnames_1["default"](ExtraFieldCheckbox_css_1["default"]['kickoff-set-field-name']);
        return (React.createElement("div", { className: ExtraFieldCheckbox_css_1["default"]['kickoff-set-field-container'], "data-autofocus-first-field": true },
            React.createElement("div", null,
                React.createElement("div", { className: fieldNameClassName }, name),
                isRequired && React.createElement("span", { className: KickoffRedux_css_1["default"]['kick-off-required-sign'] })),
            React.createElement("ul", { className: ExtraFieldCheckbox_css_1["default"]['kickoff-set-field-options'] }, selections.map(renderProcessRunOption))));
    };
    var handleToggleOption = function (optionId) { return function () {
        var isChecked = selectedOptions && !selectedOptions.includes(String(optionId));
        var newOptions = isChecked
            ? __spreadArrays(selectedOptions, [optionId]) : selectedOptions.filter(function (id) { return id !== String(optionId); });
        editField({ value: newOptions.map(String) });
    }; };
    var renderField = function () {
        var _a;
        var fieldsMap = (_a = {},
            _a[template_1.EExtraFieldMode.Kickoff] = renderKickoffField(),
            _a[template_1.EExtraFieldMode.ProcessRun] = renderProcessRunField(),
            _a);
        return fieldsMap[mode];
    };
    return renderField();
}
exports.ExtraFieldCheckbox = ExtraFieldCheckbox;
