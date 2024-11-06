"use strict";
exports.__esModule = true;
exports.TaskForm = void 0;
var react_1 = require("react");
var react_intl_1 = require("react-intl");
var TaskDescriptionEditor_1 = require("./TaskDescriptionEditor");
var helpers_1 = require("../../../utils/helpers");
var types_1 = require("../types");
var OutputForm_1 = require("../OutputForm");
var ShowMore_1 = require("../../UI/ShowMore");
var TaskPerformers_1 = require("./TaskPerformers");
var Conditions_1 = require("./Conditions");
var InputWithVariables_1 = require("../InputWithVariables");
var DueDate_1 = require("./DueDate");
var getTaskVariables_1 = require("./utils/getTaskVariables");
var TemplateEdit_css_1 = require("../TemplateEdit.css");
function TaskForm(_a) {
    var _b;
    var listVariables = _a.listVariables, templateVariables = _a.templateVariables, task = _a.task, users = _a.users, isSubscribed = _a.isSubscribed, accountId = _a.accountId, scrollTarget = _a.scrollTarget, isTeamInvitesModalOpen = _a.isTeamInvitesModalOpen, tasks = _a.tasks, kickoff = _a.kickoff, patchTask = _a.patchTask;
    var formatMessage = react_intl_1.useIntl().formatMessage;
    if (!task)
        return null;
    var taskFormPartsRefs = (_b = {},
        _b[types_1.ETaskFormParts.AssignPerformers] = react_1.useRef(null),
        _b[types_1.ETaskFormParts.DueIn] = react_1.useRef(null),
        _b[types_1.ETaskFormParts.Fields] = react_1.useRef(null),
        _b[types_1.ETaskFormParts.Conditions] = react_1.useRef(null),
        _b);
    react_1.useLayoutEffect(function () {
        var _a;
        var scrollTo = (scrollTarget && ((_a = taskFormPartsRefs[scrollTarget]) === null || _a === void 0 ? void 0 : _a.current)) || wrapperRef.current;
        if (scrollTo) {
            helpers_1.scrollToElement(scrollTo);
        }
    }, []);
    var wrapperRef = react_1.useRef(null);
    var taskName = task.name || '';
    var setCurrentTask = function (changedFields) {
        patchTask({ taskUUID: task.uuid, changedFields: changedFields });
    };
    var handleTaskFieldChange = function (field) { return function (value) {
        var _a;
        setCurrentTask((_a = {}, _a[field] = value, _a));
    }; };
    var taskFormParts = [
        {
            formPartId: types_1.ETaskFormParts.AssignPerformers,
            title: 'tasks.task-assign-help',
            component: (react_1["default"].createElement(TaskPerformers_1.TaskPerformers, { users: users, task: task, variables: listVariables, setCurrentTask: setCurrentTask, isTeamInvitesModalOpen: isTeamInvitesModalOpen }))
        },
        {
            formPartId: types_1.ETaskFormParts.DueIn,
            title: 'tasks.task-due-date',
            component: (react_1["default"].createElement("div", { className: TemplateEdit_css_1["default"]['task-fields-wrapper'] },
                react_1["default"].createElement(DueDate_1.DueDate, { dueDate: task.rawDueDate, onChange: handleTaskFieldChange('rawDueDate'), currentTask: task, kickoff: kickoff, tasks: tasks })))
        },
        {
            formPartId: types_1.ETaskFormParts.Fields,
            title: 'tasks.task-outputs-create-help',
            component: (react_1["default"].createElement(OutputForm_1.OutputFormIntl, { fields: task.fields, onOutputChange: handleTaskFieldChange('fields'), isDisabled: false, show: types_1.ETaskFormParts.Fields === scrollTarget, accountId: accountId }))
        },
        {
            formPartId: types_1.ETaskFormParts.Conditions,
            title: 'templates.conditions.title',
            component: (react_1["default"].createElement(Conditions_1.Conditions, { isSubscribed: isSubscribed, conditions: task.conditions, variables: listVariables, users: users, onEdit: handleTaskFieldChange('conditions') }))
        },
    ];
    return (react_1["default"].createElement("div", { ref: wrapperRef, className: TemplateEdit_css_1["default"]['task_form'] },
        react_1["default"].createElement("div", { className: TemplateEdit_css_1["default"]['task_form-popover'] },
            react_1["default"].createElement("div", { className: TemplateEdit_css_1["default"]['task-fields-wrapper'] },
                react_1["default"].createElement(InputWithVariables_1.InputWithVariables, { placeholder: formatMessage({ id: 'tasks.task-task-name-placeholder' }), listVariables: getTaskVariables_1.getSingleLineVariables(listVariables), templateVariables: templateVariables, value: taskName, onChange: function (value) {
                        handleTaskFieldChange('name')(value);
                        return Promise.resolve(value);
                    }, className: TemplateEdit_css_1["default"]['task-name-field'], title: formatMessage({ id: 'tasks.task-task-name' }), toolipText: formatMessage({ id: 'tasks.task-description-button-tooltip' }) }),
                react_1["default"].createElement(TaskDescriptionEditor_1.TaskDescriptionEditor, { handleChange: function (value) {
                        handleTaskFieldChange('description')(value);
                        return Promise.resolve(value);
                    }, handleChangeChecklists: handleTaskFieldChange('checklists'), value: task.description || '', listVariables: listVariables, templateVariables: templateVariables, accountId: accountId })),
            taskFormParts.map(function (_a, index) {
                var title = _a.title, component = _a.component, formPartId = _a.formPartId;
                return (react_1["default"].createElement(ShowMore_1.ShowMore, { label: index + 1 + ". " + formatMessage({ id: title }), containerClassName: TemplateEdit_css_1["default"]['task-accordion-container'], isInitiallyVisible: formPartId === scrollTarget, key: title, innerRef: taskFormPartsRefs[formPartId] }, component));
            }))));
}
exports.TaskForm = TaskForm;
