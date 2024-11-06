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
// @ts-ignore
var CheckableListItem_1 = require("./CheckableListItem");
var decorateComponentWithProps_1 = require("../../../../utils/decorateComponentWithProps");
var createBlockRendererFn_1 = require("./createBlockRendererFn");
var createBlockRenderMap_1 = require("./createBlockRenderMap");
var blockStyleFn_1 = require("./blockStyleFn");
var ChecklistButton_1 = require("./ChecklistButton");
var checkableListPlugin = function (config) {
    if (config === void 0) { config = {}; }
    var store = {
        getEditorState: null,
        setEditorState: null
    };
    var blockRendererConfig = __assign({ CheckableListItem: CheckableListItem_1.CheckableListItem }, config);
    var blockRenderMapConfig = {
        sameWrapperAsUnorderedListItem: !!config.sameWrapperAsUnorderedListItem
    };
    var buttonConfig = { store: store };
    return {
        initialize: function (_a) {
            var setEditorState = _a.setEditorState, getEditorState = _a.getEditorState;
            store.setEditorState = setEditorState;
            store.getEditorState = getEditorState;
        },
        blockRendererFn: createBlockRendererFn_1["default"](blockRendererConfig),
        blockRenderMap: createBlockRenderMap_1["default"](blockRenderMapConfig),
        ChecklistButton: decorateComponentWithProps_1.decorateComponentWithProps(ChecklistButton_1.ChecklistButton, buttonConfig),
        blockStyleFn: blockStyleFn_1["default"]
    };
};
exports["default"] = checkableListPlugin;
