"use strict";
exports.__esModule = true;
exports.TaskDescriptionEditor = void 0;
var React = require("react");
var react_intl_1 = require("react-intl");
var _onverters_1 = require("../../RichEditor/utils/\u0441onverters");
var RichEditor_1 = require("../../RichEditor");
var variablesDecorator_1 = require("../utils/variablesDecorator");
var VariableList_1 = require("../VariableList");
var addVariableEntityToEditor_1 = require("../utils/addVariableEntityToEditor");
var TemplateEdit_css_1 = require("../TemplateEdit.css");
function TaskDescriptionEditor(_a) {
    var accountId = _a.accountId, listVariables = _a.listVariables, templateVariables = _a.templateVariables, value = _a.value, handleChange = _a.handleChange, handleChangeChecklists = _a.handleChangeChecklists;
    var editor = React.useRef(null);
    var formatMessage = react_intl_1.useIntl().formatMessage;
    var handleInsertVariable = function (apiName) { return function (e) {
        e.stopPropagation();
        if (!editor.current) {
            return;
        }
        var newVariable = listVariables === null || listVariables === void 0 ? void 0 : listVariables.find(function (variable) { return variable.apiName === apiName; });
        editor.current.onChange(addVariableEntityToEditor_1.addVariableEntityToEditor(editor.current.state.editorState, {
            title: newVariable === null || newVariable === void 0 ? void 0 : newVariable.title,
            subtitle: newVariable === null || newVariable === void 0 ? void 0 : newVariable.subtitle,
            apiName: apiName
        }));
    }; };
    return (React.createElement(RichEditor_1.RichEditorContainer, { ref: editor, title: formatMessage({ id: 'tasks.task-description-field' }), placeholder: formatMessage({ id: 'template.task-description-placeholder' }), initialState: _onverters_1.getInitialEditorState(value, templateVariables), handleChange: handleChange, handleChangeChecklists: handleChangeChecklists, decorators: [variablesDecorator_1.variablesDecorator], withChecklists: true, accountId: accountId },
        React.createElement(VariableList_1.VariableList, { variables: listVariables, onVariableClick: handleInsertVariable, className: TemplateEdit_css_1["default"]['task-description__variables'], tooltipText: "tasks.task-description-button-tooltip", focusEditor: function () { var _a; return (_a = editor.current) === null || _a === void 0 ? void 0 : _a.focus(); } })));
}
exports.TaskDescriptionEditor = TaskDescriptionEditor;
