"use strict";
exports.__esModule = true;
exports.setChecklistApiNames = void 0;
// @ts-ignore
var draft_js_modifiers_1 = require("draft-js-modifiers");
// @ts-ignore
var draft_js_checkable_list_item_1 = require("draft-js-checkable-list-item");
var createId_1 = require("../../../../utils/createId");
function setChecklistApiNames(editorState) {
    var resultEditorState = editorState;
    var currentListApiName = '';
    var contentState = editorState.getCurrentContent();
    var usedListsApiNames = [];
    var usedItemsApiNames = [];
    contentState.getBlockMap().forEach(function (block, key) {
        if (!key || !block || block.getType() !== draft_js_checkable_list_item_1.CHECKABLE_LIST_ITEM) {
            return;
        }
        if (!currentListApiName) {
            currentListApiName = getApiName(EApiNameType.Checklist, block, usedListsApiNames);
        }
        var itemApiName = getApiName(EApiNameType.ChecklistItem, block, usedItemsApiNames);
        usedItemsApiNames.push(itemApiName);
        resultEditorState = draft_js_modifiers_1.mergeBlockDataByKey(resultEditorState, key, {
            listApiName: currentListApiName,
            itemApiName: itemApiName
        });
        var nextBlock = contentState.getBlockAfter(key);
        if (!nextBlock || nextBlock.getType() !== draft_js_checkable_list_item_1.CHECKABLE_LIST_ITEM) {
            usedListsApiNames.push(currentListApiName);
            currentListApiName = '';
        }
    });
    return resultEditorState;
}
exports.setChecklistApiNames = setChecklistApiNames;
var EApiNameType;
(function (EApiNameType) {
    EApiNameType["Checklist"] = "checklist";
    EApiNameType["ChecklistItem"] = "checklist-item";
})(EApiNameType || (EApiNameType = {}));
var getApiName = function (type, block, usedApiNames) {
    var _a, _b;
    var getSetApiNameMap = (_a = {},
        _a[EApiNameType.Checklist] = function () { return block.getData().get('listApiName'); },
        _a[EApiNameType.ChecklistItem] = function () { return block.getData().get('itemApiName'); },
        _a);
    var createApiNameMap = (_b = {},
        _b[EApiNameType.Checklist] = function () { return createId_1.createUniqueId('clist-xxxyxx'); },
        _b[EApiNameType.ChecklistItem] = function () { return createId_1.createUniqueId('citem-xxxyxx'); },
        _b);
    var setApiName = getSetApiNameMap[type]();
    var createApiName = createApiNameMap[type];
    if (!setApiName) {
        return createApiName();
    }
    return usedApiNames.includes(setApiName) ? createApiName() : setApiName;
};
