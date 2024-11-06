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
exports.ExtraFieldCreatable = void 0;
/* eslint-disable */
/* prettier-ignore */
var React = require("react");
var classnames_1 = require("classnames");
var react_input_autosize_1 = require("react-input-autosize");
var DropdownList_1 = require("../../../UI/DropdownList");
var getEmptySelection_1 = require("../../KickoffRedux/utils/getEmptySelection");
var fitInputWidth_1 = require("../utils/fitInputWidth");
var getInputNameBackground_1 = require("../utils/getInputNameBackground");
var icons_1 = require("../../../icons");
var helpers_1 = require("../../../../utils/helpers");
var IntlMessages_1 = require("../../../IntlMessages");
var FieldWithName_1 = require("../utils/FieldWithName");
var getFieldValidator_1 = require("../utils/getFieldValidator");
var template_1 = require("../../../../types/template");
var validators_1 = require("../../../../utils/validators");
var KickoffRedux_css_1 = require("../../KickoffRedux/KickoffRedux.css");
var ExtraFieldCreatable_css_1 = require("./ExtraFieldCreatable.css");
var DEFAULT_OPTION_INPUT_WIDTH = 120;
var DEFAULT_FIELD_INPUT_WIDTH = 120;
/*
  TODO: Rename all {Creatable} to {Dropdown}
  Details: https://trello.com/c/RqrYD3lc/1154-extrafields-rename
*/
function ExtraFieldCreatable(_a) {
    var field = _a.field, isRequired = _a.field.isRequired, intl = _a.intl, _b = _a.descriptionPlaceholder, descriptionPlaceholder = _b === void 0 ? intl.formatMessage({ id: 'template.kick-off-form-field-description-placeholder' }) : _b, _c = _a.namePlaceholder, namePlaceholder = _c === void 0 ? intl.formatMessage({ id: 'template.kick-off-form-field-name-placeholder' }) : _c, _d = _a.mode, mode = _d === void 0 ? template_1.EExtraFieldMode.Kickoff : _d, editField = _a.editField, deleteField = _a.deleteField, _e = _a.isDisabled, isDisabled = _e === void 0 ? false : _e, labelBackgroundColor = _a.labelBackgroundColor, innerRef = _a.innerRef;
    var fieldNameInputRef = React.useRef(null);
    var optionInputsRefs = React.useRef([]);
    React.useEffect(function () {
        optionInputsRefs.current.forEach(function (input) { return fitInputWidth_1.fitInputWidth(input, DEFAULT_OPTION_INPUT_WIDTH); });
    }, [field.selections]);
    React.useEffect(function () {
        fitInputWidth_1.fitInputWidth(fieldNameInputRef.current, DEFAULT_FIELD_INPUT_WIDTH);
    }, []);
    var useCallback = React.useCallback, useState = React.useState, useMemo = React.useMemo;
    var selections = field.selections, description = field.description;
    var dropdownSelections = useMemo(function () { return (selections || [])
        .map(function (selection) { return (__assign(__assign({}, selection), { label: selection.value })); }); }, [selections]);
    var _f = useState(null), activeOptionIndex = _f[0], setActiveOptionIndex = _f[1];
    var handleSelectableChange = function (inputValue) {
        editField({
            value: String(inputValue.id),
            selections: selections === null || selections === void 0 ? void 0 : selections.map(function (selection) { return (__assign(__assign({}, selection), { isSelected: inputValue.id === selection.id })); })
        });
    };
    var fieldNameClassName = classnames_1["default"](getInputNameBackground_1.getInputNameBackground(labelBackgroundColor), KickoffRedux_css_1["default"]['kick-off-input__name']);
    var handleChangeName = useCallback(function (e) {
        fitInputWidth_1.fitInputWidth(e.target, DEFAULT_FIELD_INPUT_WIDTH);
        editField({ name: e.target.value });
    }, [editField]);
    var handleDeleteField = useCallback(function () {
        if (!deleteField) {
            return;
        }
        deleteField();
    }, [deleteField]);
    var handleChangeDescription = useCallback(function (e) {
        editField({ description: e.target.value });
    }, [editField]);
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
    var renderKickoffOption = function (_a, optionIndex) {
        var value = _a.value, id = _a.id;
        var isActive = optionIndex === activeOptionIndex;
        var errorMessageIntl = validators_1.validateCheckboxAndRadioField(value);
        var shouldShowError = Boolean(errorMessageIntl);
        return (React.createElement("li", { key: optionIndex, className: ExtraFieldCreatable_css_1["default"]['kickoff-create-field-option'], onMouseOver: function () { return setActiveOptionIndex(optionIndex); }, onMouseLeave: function () { return setActiveOptionIndex(null); } },
            React.createElement("div", { className: ExtraFieldCreatable_css_1["default"]['kickoff-create-field__input-container'] },
                React.createElement("input", { ref: function (el) { return optionInputsRefs.current[optionIndex] = el; }, className: ExtraFieldCreatable_css_1["default"]['kickoff-create-field-option__input'], onChange: handleChangeOption(optionIndex), placeholder: namePlaceholder, type: "text", value: value, disabled: isDisabled }),
                React.createElement("span", { className: ExtraFieldCreatable_css_1["default"]['measure'] }),
                isActive && !isDisabled && (React.createElement("div", { role: "button", className: ExtraFieldCreatable_css_1["default"]['kickoff-create-field-option__remove'], onClick: handleRemoveOption(optionIndex) },
                    React.createElement(icons_1.RemoveIcon, null)))),
            shouldShowError &&
                React.createElement("p", { className: ExtraFieldCreatable_css_1["default"]['kickoff-create-field__error-text'] },
                    React.createElement(IntlMessages_1.IntlMessages, { id: errorMessageIntl }))));
    };
    var renderKickoffField = function () { return (React.createElement(FieldWithName_1.FieldWithName, { inputClassName: ExtraFieldCreatable_css_1["default"]['kickoff-dropdown-field'], labelBackgroundColor: labelBackgroundColor, field: field, descriptionPlaceholder: descriptionPlaceholder, namePlaceholder: namePlaceholder, mode: mode, handleChangeName: handleChangeName, handleChangeDescription: handleChangeDescription, validate: getFieldValidator_1.getFieldValidator(field, mode), isDisabled: isDisabled, icon: React.createElement(icons_1.ArrowDropdownIcon, null), innerRef: innerRef })); };
    var renderKickoffView = function () { return (React.createElement("div", { className: ExtraFieldCreatable_css_1["default"]['kickoff-create-field-container'] },
        renderKickoffField(),
        selections && (React.createElement("ul", { className: ExtraFieldCreatable_css_1["default"]['kickoff-create-field-options'] }, selections === null || selections === void 0 ? void 0 : selections.map(renderKickoffOption))),
        !isDisabled && (React.createElement("button", { type: "button", className: ExtraFieldCreatable_css_1["default"]['kickoff-create-field-add-option'], onClick: handleAddOption },
            React.createElement(IntlMessages_1.IntlMessages, { id: "template.kick-off-add-options" }))))); };
    var renderSelectableView = function () {
        var _a, _b;
        var displayValue = {
            label: (_b = (_a = field.selections) === null || _a === void 0 ? void 0 : _a.find(function (selection) { return Number(selection.id) === Number(field.value); })) === null || _b === void 0 ? void 0 : _b.value
        };
        return (React.createElement("div", { className: classnames_1["default"]('has-float-label', ExtraFieldCreatable_css_1["default"]['dropdown-container']), "data-autofocus-first-field": true },
            React.createElement(DropdownList_1.DropdownList, { options: dropdownSelections, onChange: handleSelectableChange, placeholder: description, isDisabled: isDisabled, isSearchable: false, value: displayValue }),
            React.createElement("div", { className: fieldNameClassName },
                React.createElement(react_input_autosize_1["default"], { inputRef: function (ref) { return fieldNameInputRef.current = ref; }, inputClassName: ExtraFieldCreatable_css_1["default"]['kickoff-create-field-name-input'], disabled: mode !== template_1.EExtraFieldMode.Kickoff || isDisabled, onChange: handleChangeName, placeholder: namePlaceholder, type: "text", value: field.name }),
                isRequired && React.createElement("span", { className: KickoffRedux_css_1["default"]['kick-off-required-sign'] }))));
    };
    var renderDropdownField = function () {
        var _a;
        var fieldsMap = (_a = {},
            _a[template_1.EExtraFieldMode.Kickoff] = renderKickoffView(),
            _a[template_1.EExtraFieldMode.ProcessRun] = renderSelectableView(),
            _a);
        return fieldsMap[mode];
    };
    return renderDropdownField();
}
exports.ExtraFieldCreatable = ExtraFieldCreatable;
