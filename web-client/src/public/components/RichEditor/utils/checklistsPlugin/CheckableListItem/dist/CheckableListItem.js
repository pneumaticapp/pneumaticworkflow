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
exports.__esModule = true;
exports.CheckableListItem = void 0;
var react_1 = require("react");
var draft_js_1 = require("draft-js");
var UI_1 = require("../../../../UI");
var CheckableListItem_css_1 = require("./CheckableListItem.css");
exports.CheckableListItem = function (props) {
    var offsetKey = props.offsetKey;
    return (react_1["default"].createElement("div", { className: CheckableListItem_css_1["default"]['checkable-list-item-block'], "data-offset-key": offsetKey },
        react_1["default"].createElement("div", { className: CheckableListItem_css_1["default"]['checkable-list-item-block__checkbox'], contentEditable: false, suppressContentEditableWarning: true },
            react_1["default"].createElement(UI_1.Checkbox, { containerClassName: CheckableListItem_css_1["default"]['checkable-list-item-block__checkbox-inner'], checked: false })),
        react_1["default"].createElement("div", { className: CheckableListItem_css_1["default"]['checkable-list-item-block__text'] },
            react_1["default"].createElement(draft_js_1.EditorBlock, __assign({}, props)))));
};
