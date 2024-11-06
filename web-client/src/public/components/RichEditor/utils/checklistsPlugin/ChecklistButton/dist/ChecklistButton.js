"use strict";
exports.__esModule = true;
exports.ChecklistButton = void 0;
/* eslint-disable jsx-a11y/control-has-associated-label */
/* eslint-disable jsx-a11y/no-static-element-interactions */
var react_1 = require("react");
var classnames_1 = require("classnames");
var react_intl_1 = require("react-intl");
var draft_js_1 = require("draft-js");
// @ts-ignore
var draft_js_checkable_list_item_1 = require("draft-js-checkable-list-item");
var icons_1 = require("../../../../icons");
var UI_1 = require("../../../../UI");
// import { ELearnMoreLinks } from '../../../../../constants/defaultValues';
var ButtonStyles_css_1 = require("../../../toolbarSettings/ButtonStyles.css");
exports.ChecklistButton = function (props) {
    var formatMessage = react_intl_1.useIntl().formatMessage;
    var toggleType = function (event) {
        event.preventDefault();
        var store = props.store;
        store.setEditorState(draft_js_1.RichUtils.toggleBlockType(store.getEditorState(), draft_js_checkable_list_item_1.CHECKABLE_LIST_ITEM));
    };
    var isActive = function () {
        var getEditorState = props.store.getEditorState;
        return draft_js_1.RichUtils.getCurrentBlockType(getEditorState()) === draft_js_checkable_list_item_1.CHECKABLE_LIST_ITEM;
    };
    var preventBubblingUp = function (event) {
        event.preventDefault();
    };
    return (react_1["default"].createElement(UI_1.Tooltip, { content: (react_1["default"].createElement(react_1["default"].Fragment, null, formatMessage({ id: 'editor.add-checklist-item' }))) },
        react_1["default"].createElement("div", { className: ButtonStyles_css_1["default"].buttonWrapper, onMouseDown: preventBubblingUp },
            react_1["default"].createElement("button", { className: classnames_1["default"](ButtonStyles_css_1["default"].button, isActive() && ButtonStyles_css_1["default"].active), onClick: toggleType, type: "button" },
                react_1["default"].createElement(icons_1.ChecklistIcon, null)))));
};
