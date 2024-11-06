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
var __spreadArrays = (this && this.__spreadArrays) || function () {
    for (var s = 0, i = 0, il = arguments.length; i < il; i++) s += arguments[i].length;
    for (var r = Array(s), k = 0, i = 0; i < il; i++)
        for (var a = arguments[i], j = 0, jl = a.length; j < jl; j++, k++)
            r[k] = a[j];
    return r;
};
exports.__esModule = true;
exports.TaskCardWrapper = exports.TaskCard = exports.ETaskCardViewMode = void 0;
var react_1 = require("react");
var react_intl_1 = require("react-intl");
var classnames_1 = require("classnames");
var react_router_dom_1 = require("react-router-dom");
var throttle_debounce_1 = require("throttle-debounce");
var autoFocusFirstField_1 = require("../../utils/autoFocusFirstField");
var template_1 = require("../../types/template");
var strings_1 = require("../../utils/strings");
var actions_1 = require("../../redux/actions");
var ExtraFieldsHelper_1 = require("../TemplateEdit/ExtraFields/utils/ExtraFieldsHelper");
var routes_1 = require("../../utils/routes");
var Header_1 = require("../UI/Typeography/Header");
var RichText_1 = require("../RichText");
var UserData_1 = require("../UserData");
var users_1 = require("../../utils/users");
var ExtraFields_1 = require("../TemplateEdit/ExtraFields");
var helpers_1 = require("../../utils/helpers");
var useCheckDevice_1 = require("../../hooks/useCheckDevice");
var history_1 = require("../../utils/history");
var workflow_1 = require("../../types/workflow");
var getEditedFields_1 = require("../TemplateEdit/ExtraFields/utils/getEditedFields");
var IntlMessages_1 = require("../IntlMessages");
var Button_1 = require("../UI/Buttons/Button");
var WorkflowLog_1 = require("../Workflows/WorkflowLog");
var icons_1 = require("../icons");
var WorkflowLogSkeleton_1 = require("../Workflows/WorkflowLog/WorkflowLogSkeleton");
var UsersDropdown_1 = require("../common/form/UsersDropdown");
var analytics_1 = require("../../utils/analytics");
var UI_1 = require("../UI");
var storageOutputs_1 = require("./utils/storageOutputs");
var WorkflowInfo_1 = require("./WorkflowInfo");
var TaskCarkSkeleton_1 = require("./TaskCarkSkeleton");
var GuestsController_1 = require("./GuestsController");
var checklist_1 = require("./checklist");
var DueIn_1 = require("../DueIn");
var SubWorkflows_1 = require("./SubWorkflows");
var UserPerformer_1 = require("../common/UserPerformer");
var TaskCard_css_1 = require("./TaskCard.css");
var ETaskCardViewMode;
(function (ETaskCardViewMode) {
    ETaskCardViewMode["Single"] = "single";
    ETaskCardViewMode["List"] = "list";
    ETaskCardViewMode["Guest"] = "guest";
})(ETaskCardViewMode = exports.ETaskCardViewMode || (exports.ETaskCardViewMode = {}));
var MINIMIZED_LOG_MAX_EVENTS = 5;
function TaskCard(_a) {
    var task = _a.task, viewMode = _a.viewMode, workflowLog = _a.workflowLog, workflow = _a.workflow, isWorkflowLoading = _a.isWorkflowLoading, status = _a.status, accountId = _a.accountId, users = _a.users, authUser = _a.authUser, changeWorkflowLog = _a.changeWorkflowLog, setCurrentTask = _a.setCurrentTask, setTaskCompleted = _a.setTaskCompleted, setTaskReverted = _a.setTaskReverted, sendWorkflowLogComments = _a.sendWorkflowLogComments, changeWorkflowLogViewSettings = _a.changeWorkflowLogViewSettings, clearWorkflow = _a.clearWorkflow, addTaskPerformer = _a.addTaskPerformer, removeTaskPerformer = _a.removeTaskPerformer, openWorkflowLogPopup = _a.openWorkflowLogPopup, setDueDate = _a.setDueDate, deleteDueDate = _a.deleteDueDate, openSelectTemplateModal = _a.openSelectTemplateModal;
    var formatMessage = react_intl_1.useIntl().formatMessage;
    var isMobile = useCheckDevice_1.useCheckDevice().isMobile;
    var saveOutputsToStorageDebounced = throttle_debounce_1.debounce(300, storageOutputs_1.addOrUpdateStorageOutput);
    var guestsControllerRef = react_1.useRef(null);
    var wrapperRef = react_1.useRef(null);
    var workflowLinkRef = react_1.useRef(null);
    var _b = react_1.useState([]), outputValues = _b[0], setOutputValues = _b[1];
    var _c = react_1.useState(true), isLogMinimized = _c[0], setIsLogMinimized = _c[1];
    var toggleLog = function () { return setIsLogMinimized(!isLogMinimized); };
    react_1.useEffect(function () {
        autoFocusFirstField_1.autoFocusFirstField(wrapperRef.current);
        return function () {
            setCurrentTask(null);
            clearWorkflow();
        };
    }, []);
    react_1.useEffect(function () {
        var _a;
        (_a = guestsControllerRef.current) === null || _a === void 0 ? void 0 : _a.updateDropdownPosition();
    }, [task.performers.length]);
    react_1.useEffect(function () {
        var output = task.output, id = task.id;
        var storageOutput = storageOutputs_1.getOutputFromStorage(id);
        var outputFieldsWithValues = new ExtraFieldsHelper_1.ExtraFieldsHelper(output, storageOutput).getFieldsWithValues();
        setOutputValues(outputFieldsWithValues);
    }, [task.id]);
    var handleOpenWorkflowPopup = function (workflowId) { return function (e) {
        e.preventDefault();
        if (workflowId) {
            openWorkflowLogPopup({ workflowId: workflowId });
        }
    }; };
    var handleDelegateWorkflow = function () {
        openSelectTemplateModal({
            ancestorTaskId: task.id
        });
    };
    var renderHeader = function () {
        var name = task.name, id = task.id, dateStarted = task.dateStarted, _a = task.workflow, workflowName = _a.name, templateName = _a.templateName, isUrgent = task.isUrgent;
        var redirectToWorkflowUrl = (workflowLog === null || workflowLog === void 0 ? void 0 : workflowLog.workflowId) ? routes_1.getWorkflowDetailedRoute(workflowLog.workflowId) : '#';
        var redirectToTaskUrl = routes_1.getTaskDetailRoute(id);
        var showLinkToTaskDetail = !routes_1.isTaskDetailRoute(history_1.history.location.pathname);
        if (viewMode === ETaskCardViewMode.Guest) {
            return (react_1["default"].createElement(Header_1.Header, { size: "4", tag: "h1", className: TaskCard_css_1["default"]['guest-task-name'] }, name));
        }
        return (react_1["default"].createElement(react_1["default"].Fragment, null,
            react_1["default"].createElement("div", { className: TaskCard_css_1["default"]['pretitle'] },
                templateName,
                react_1["default"].createElement("div", { className: TaskCard_css_1["default"].dot }),
                react_1["default"].createElement(UI_1.Tooltip, { content: formatMessage({ id: 'workflows.name' }), containerClassName: TaskCard_css_1["default"]['workflow-name-container'] },
                    react_1["default"].createElement("span", null,
                        react_1["default"].createElement(react_router_dom_1.Link, { innerRef: workflowLinkRef, to: redirectToWorkflowUrl, onClick: handleOpenWorkflowPopup(workflowLog.workflowId), className: TaskCard_css_1["default"]['workflow-name'] }, strings_1.sanitizeText(workflowName))))),
            react_1["default"].createElement("div", { className: TaskCard_css_1["default"]['task-name-container'] },
                react_1["default"].createElement(Header_1.Header, { size: "4", tag: "h4" },
                    isUrgent ? (react_1["default"].createElement("div", { className: TaskCard_css_1["default"]['task-name__urgent-marker'] }, formatMessage({ id: 'workflows.card-urgent' }))) : null,
                    showLinkToTaskDetail ? react_1["default"].createElement(react_router_dom_1.Link, { to: redirectToTaskUrl }, strings_1.sanitizeText(name)) : strings_1.sanitizeText(name))),
            react_1["default"].createElement("span", { className: TaskCard_css_1["default"]['date'] }, strings_1.getDate(dateStarted))));
    };
    var renderPerformers = function () {
        var isPossibleToRemovePerformer = [
            task.performers.length > 1,
            viewMode !== ETaskCardViewMode.Guest,
            status !== actions_1.ETaskStatus.Completed,
            (workflow === null || workflow === void 0 ? void 0 : workflow.status) !== workflow_1.EWorkflowStatus.Finished,
        ].every(Boolean);
        return task.performers.map(function (userId) {
            return (react_1["default"].createElement(UserData_1.UserData, { key: "UserData" + userId, userId: userId }, function (user) {
                if (!user)
                    return null;
                return (react_1["default"].createElement(UserPerformer_1.UserPerformer, __assign({ user: __assign(__assign({}, user), { sourceId: String(user.id), value: String(user.id), label: users_1.getUserFullName(user) }), bgColor: UserPerformer_1.EBgColorTypes.Light }, (isPossibleToRemovePerformer && {
                    onClick: function () { return removeTaskPerformer({ taskId: task.id, userId: userId }); }
                }))));
            }));
        });
    };
    var renderPerformersControllers = function () {
        if (status === actions_1.ETaskStatus.Completed || (workflow === null || workflow === void 0 ? void 0 : workflow.status) === workflow_1.EWorkflowStatus.Finished)
            return null;
        var performerDropdownOption = users.map(function (item) {
            return __assign(__assign({}, item), { optionType: UsersDropdown_1.EOptionTypes.User, label: users_1.getUserFullName(item), value: String(item.id) });
        });
        var mapPerformersDropdownValue = users.filter(function (user) { return task.performers.find(function (id) { return user.id === id; }); });
        var performerDropdownValue = mapPerformersDropdownValue.map(function (item) {
            return __assign(__assign({}, item), { optionType: UsersDropdown_1.EOptionTypes.User, label: users_1.getUserFullName(item), value: String(item.id) });
        });
        var onUsersInvited = function (invitedUsers) {
            invitedUsers.forEach(function (user) { return addTaskPerformer({ taskId: task.id, userId: user.id }); });
        };
        var onRemoveTaskPerformer = function (_a) {
            var id = _a.id;
            removeTaskPerformer({ taskId: task.id, userId: id });
        };
        var onAddTaskPerformer = function (_a) {
            var id = _a.id;
            addTaskPerformer({ taskId: task.id, userId: id });
        };
        return (react_1["default"].createElement(react_1["default"].Fragment, null,
            authUser.isAdmin && (react_1["default"].createElement(UsersDropdown_1.UsersDropdown, { isMulti: true, controlSize: "sm", className: TaskCard_css_1["default"]['responsible'], placeholder: formatMessage({ id: 'user.search-field-placeholder' }), options: performerDropdownOption, value: performerDropdownValue, onChange: onAddTaskPerformer, onChangeSelected: onRemoveTaskPerformer, onUsersInvited: onUsersInvited, onClickInvite: function () { return analytics_1.trackInviteTeamInPage('Task card'); }, inviteLabel: formatMessage({ id: 'template.invite-team-member' }), title: formatMessage({ id: 'task.add-performer' }) })),
            viewMode !== ETaskCardViewMode.Guest && (react_1["default"].createElement(GuestsController_1.GuestController, { ref: guestsControllerRef, taskId: task.id, className: TaskCard_css_1["default"]['guest-dropdown'] }))));
    };
    var handleEditField = function (apiName) { return function (changedProps) {
        setOutputValues(function (prevOutputFields) {
            var newFields = getEditedFields_1.getEditedFields(prevOutputFields, apiName, changedProps);
            saveOutputsToStorageDebounced(task.id, newFields);
            return newFields;
        });
    }; };
    var renderOutputFields = function () {
        if (!helpers_1.isArrayWithItems(outputValues) || status === actions_1.ETaskStatus.Completed) {
            return null;
        }
        return (react_1["default"].createElement("div", { className: TaskCard_css_1["default"]['task-output'] },
            react_1["default"].createElement("p", { className: TaskCard_css_1["default"]['task-output__title'] },
                react_1["default"].createElement(IntlMessages_1.IntlMessages, { id: "tasks.task-outputs-fill-help" })), outputValues === null || outputValues === void 0 ? void 0 :
            outputValues.map(function (field) { return (react_1["default"].createElement(ExtraFields_1.ExtraFieldIntl, { key: field.apiName, field: field, editField: handleEditField(field.apiName), showDropdown: false, mode: template_1.EExtraFieldMode.ProcessRun, labelBackgroundColor: workflow_1.EInputNameBackgroundColor.OrchidWhite, namePlaceholder: field.name, descriptionPlaceholder: field.description, wrapperClassName: TaskCard_css_1["default"]['task-output__field'], accountId: accountId })); })));
    };
    var renderTaskButtons = function () {
        if (status === actions_1.ETaskStatus.Completed || task.workflow.status === workflow_1.EWorkflowStatus.Finished) {
            var dateCompleted = task.dateCompleted || task.workflow.dateCompleted;
            var label = dateCompleted ? (react_1["default"].createElement(react_1["default"].Fragment, null,
                formatMessage({ id: 'task.completed-with-date' }),
                react_1["default"].createElement("span", { className: TaskCard_css_1["default"]['completed__text-date'] }, strings_1.getDate(dateCompleted)))) : (formatMessage({ id: 'task.completed' }));
            return (react_1["default"].createElement("div", { className: TaskCard_css_1["default"]['completed'] },
                react_1["default"].createElement(icons_1.DoneInfoIcon, null),
                react_1["default"].createElement("p", { className: TaskCard_css_1["default"]['completed__text'] }, label)));
        }
        var renderCompleteButton = function (isDisabled) {
            return (react_1["default"].createElement(Button_1.Button, { isLoading: status === actions_1.ETaskStatus.Completing, onClick: function () {
                    return setTaskCompleted({
                        taskId: taskId,
                        workflowId: workflowId,
                        viewMode: viewMode,
                        output: outputValues
                    });
                }, label: formatMessage({ id: 'processes.complete-task' }), size: "md", disabled: isDisabled, buttonStyle: "yellow" }));
        };
        var _a = task.workflow, workflowId = _a.id, currentTask = _a.currentTask, taskId = task.id;
        var isReturnAllowed = viewMode !== ETaskCardViewMode.Guest && currentTask > 1;
        var isEmbeddedWorkflowsComplete = !task.subWorkflows.some(function (subWorkflow) { return subWorkflow.status !== workflow_1.EWorkflowStatus.Finished; });
        return (react_1["default"].createElement("div", { className: TaskCard_css_1["default"]['buttons'] },
            react_1["default"].createElement("div", { className: TaskCard_css_1["default"]['buttons__complete'] }, isEmbeddedWorkflowsComplete ? (renderCompleteButton(!isEmbeddedWorkflowsComplete)) : (react_1["default"].createElement(UI_1.Tooltip, { content: formatMessage({ id: 'task.need-complete-embedded-processes' }) },
                react_1["default"].createElement("div", null, renderCompleteButton(!isEmbeddedWorkflowsComplete))))),
            isReturnAllowed && (react_1["default"].createElement(UI_1.Tooltip, { content: !isEmbeddedWorkflowsComplete
                    ? formatMessage({ id: 'task.need-complete-embedded-processes' })
                    : formatMessage({ id: 'tasks.task-return-hint' }) },
                react_1["default"].createElement("div", null,
                    react_1["default"].createElement(Button_1.Button, { disabled: !isEmbeddedWorkflowsComplete, onClick: function () { return setTaskReverted({ taskId: taskId, workflowId: workflowId, viewMode: viewMode }); }, label: isMobile ? undefined : formatMessage({ id: 'processes.return-task' }), icon: isMobile ? icons_1.ReturnToIcon : undefined, buttonStyle: "transparent-black", className: TaskCard_css_1["default"]['buttons__return'], size: "md", isLoading: status === actions_1.ETaskStatus.Returning })))),
            viewMode !== ETaskCardViewMode.Guest && (react_1["default"].createElement(UI_1.Tooltip, { content: formatMessage({ id: 'task.delegate' }) },
                react_1["default"].createElement(Button_1.Button, { onClick: handleDelegateWorkflow, icon: icons_1.PlayLogoIcon, buttonStyle: "transparent-black", className: TaskCard_css_1["default"]['buttons__return'], size: "md", isLoading: status === actions_1.ETaskStatus.Returning })))));
    };
    var renderWorkflowData = function () {
        if (isWorkflowLoading) {
            return react_1["default"].createElement(WorkflowLogSkeleton_1.WorkflowLogSkeleton, null);
        }
        var isWorkflowInfoVisible = [
            workflow,
            viewMode !== ETaskCardViewMode.Guest,
            !isLogMinimized,
            !workflowLog.isOnlyAttachmentsShown,
        ].every(Boolean);
        return (react_1["default"].createElement(react_1["default"].Fragment, null,
            react_1["default"].createElement(WorkflowLog_1.WorkflowLog, { workflowStatus: (workflow === null || workflow === void 0 ? void 0 : workflow.status) || workflow_1.EWorkflowStatus.Running, theme: "beige", isLoading: workflowLog.isLoading, items: workflowLog.items, sorting: workflowLog.sorting, isCommentsShown: workflowLog.isCommentsShown, isOnlyAttachmentsShown: workflowLog.isOnlyAttachmentsShown, workflowId: workflowLog.workflowId, changeWorkflowLogViewSettings: changeWorkflowLogViewSettings, includeHeader: true, sendComment: sendWorkflowLogComments, currentTask: workflow === null || workflow === void 0 ? void 0 : workflow.currentTask, isLogMinimized: isLogMinimized && viewMode !== ETaskCardViewMode.Guest, areTasksClickable: viewMode === ETaskCardViewMode.Single, onUnmount: function () {
                    return changeWorkflowLog({
                        isOnlyAttachmentsShown: false,
                        sorting: workflow_1.EWorkflowsLogSorting.New
                    });
                }, minimizedLogMaxEvents: MINIMIZED_LOG_MAX_EVENTS, isCommentFieldHidden: viewMode === ETaskCardViewMode.Guest && status === actions_1.ETaskStatus.Completed, isToggleCommentHidden: viewMode === ETaskCardViewMode.Guest }),
            isWorkflowInfoVisible && (react_1["default"].createElement("div", { className: TaskCard_css_1["default"]['workflow-info'] },
                react_1["default"].createElement(WorkflowInfo_1.WorkflowInfo, { workflow: workflow }))),
            viewMode !== ETaskCardViewMode.Guest && (react_1["default"].createElement(Button_1.Button, { label: isLogMinimized ? formatMessage({ id: 'task.expand-log' }) : formatMessage({ id: 'task.minimize-log' }), buttonStyle: "transparent-yellow", size: "md", onClick: toggleLog, className: TaskCard_css_1["default"]['minimize-log-button'], disabled: workflowLog.isOnlyAttachmentsShown && workflowLog.items.length <= MINIMIZED_LOG_MAX_EVENTS }))));
    };
    return (react_1["default"].createElement("div", { ref: wrapperRef, className: classnames_1["default"](TaskCard_css_1["default"]['container'], viewMode === ETaskCardViewMode.Guest && TaskCard_css_1["default"]['container_guest']) },
        renderHeader(),
        react_1["default"].createElement("p", { className: TaskCard_css_1["default"]['description'] },
            react_1["default"].createElement(RichText_1.RichText, { text: task.description, interactiveChecklists: true, renderExtensions: __spreadArrays(checklist_1.createChecklistExtension(task), checklist_1.createProgressbarExtension(task)) })),
        react_1["default"].createElement("div", { className: TaskCard_css_1["default"]['info'] },
            react_1["default"].createElement("div", { className: TaskCard_css_1["default"]['performers'] },
                renderPerformersControllers(),
                renderPerformers()),
            react_1["default"].createElement(DueIn_1.DueIn, { withTime: true, dueDate: task.dueDate, onSave: setDueDate, onRemove: deleteDueDate, containerClassName: TaskCard_css_1["default"]['due-in'] })),
        react_1["default"].createElement("div", { className: TaskCard_css_1["default"]['complete-form'] },
            renderOutputFields(),
            renderTaskButtons(),
            viewMode !== ETaskCardViewMode.Guest && !helpers_1.isEmptyArray(task.subWorkflows) && (react_1["default"].createElement(SubWorkflows_1.SubWorkflowsContainer, { workflows: task.subWorkflows, ancestorTaskId: task.id }))),
        renderWorkflowData()));
}
exports.TaskCard = TaskCard;
function TaskCardWrapper(_a) {
    var task = _a.task, status = _a.status, restProps = __rest(_a, ["task", "status"]);
    if (status === actions_1.ETaskStatus.Loading)
        return react_1["default"].createElement(TaskCarkSkeleton_1.TaskCarkSkeleton, null);
    if (!task)
        return null;
    return react_1["default"].createElement(TaskCard, __assign({ task: task, status: status }, restProps));
}
exports.TaskCardWrapper = TaskCardWrapper;
