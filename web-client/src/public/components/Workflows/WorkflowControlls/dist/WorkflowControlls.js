"use strict";
var __spreadArrays = (this && this.__spreadArrays) || function () {
    for (var s = 0, i = 0, il = arguments.length; i < il; i++) s += arguments[i].length;
    for (var r = Array(s), k = 0, i = 0; i < il; i++)
        for (var a = arguments[i], j = 0, jl = a.length; j < jl; j++, k++)
            r[k] = a[j];
    return r;
};
exports.__esModule = true;
exports.WorkflowControllsComponents = void 0;
var react_1 = require("react");
var react_redux_1 = require("react-redux");
var react_intl_1 = require("react-intl");
var rc_switch_1 = require("rc-switch");
var classnames_1 = require("classnames");
var icons_1 = require("../../icons");
var helpers_1 = require("../../../utils/helpers");
var user_1 = require("../../../redux/selectors/user");
var workflow_1 = require("../../../types/workflow");
var Notifications_1 = require("../../UI/Notifications");
var actions_1 = require("../../../redux/actions");
var getSnoozeOptions_1 = require("../utils/getSnoozeOptions");
var routes_1 = require("../../../utils/routes");
var history_1 = require("../../../utils/history");
var checkCanControlWorkflow_1 = require("./utils/checkCanControlWorkflow");
var WorkflowControlls_css_1 = require("./WorkflowControlls.css");
function WorkflowControllsComponents(_a) {
    var _b, _c;
    var workflow = _a.workflow, timezone = _a.timezone, onWorkflowDeleted = _a.onWorkflowDeleted, onWorkflowEnded = _a.onWorkflowEnded, onWorkflowSnoozed = _a.onWorkflowSnoozed, onWorkflowResumed = _a.onWorkflowResumed, onWorkflowReturn = _a.onWorkflowReturn, onChangeUrgent = _a.onChangeUrgent, children = _a.children;
    var dispatch = react_redux_1.useDispatch();
    var formatMessage = react_intl_1.useIntl().formatMessage;
    var _d = react_1["default"].useState(workflow.isUrgent), isUrgent = _d[0], setIsUrgent = _d[1];
    var authUser = react_redux_1.useSelector(user_1.getAuthUser).authUser;
    var canControlWorkflow = checkCanControlWorkflow_1.checkCanControlWorkflow(authUser, workflow.template);
    if (!canControlWorkflow) {
        return react_1["default"].createElement(react_1["default"].Fragment, null, children([]));
    }
    var workflowId = workflow.id;
    var templateId = (_b = workflow.template) === null || _b === void 0 ? void 0 : _b.id;
    var passedTasks = workflow === null || workflow === void 0 ? void 0 : workflow.passedTasks;
    var snoozeOptions = getSnoozeOptions_1.getSnoozeOptions(formatMessage, timezone);
    var canCloneWorkflow = Boolean((_c = workflow.template) === null || _c === void 0 ? void 0 : _c.isActive);
    var canEndWorkflow = workflow.finalizable && workflow.status !== workflow_1.EWorkflowStatus.Finished;
    var canSnoozeWorkflow = workflow.status === workflow_1.EWorkflowStatus.Running;
    var canResumeWorkflow = workflow.status === workflow_1.EWorkflowStatus.Snoozed;
    var handleOnClone = function () {
        if (!workflow.template) {
            Notifications_1.NotificationManager.error({
                title: 'workflows.no-template-access'
            });
            return;
        }
        dispatch(actions_1.cloneWorkflowAction({
            workflowId: workflowId,
            workflowName: workflow.name,
            templateId: templateId
        }));
    };
    var handleResumeWorkflow = function () {
        if (workflowId) {
            dispatch(actions_1.setWorkflowResumed({
                workflowId: workflowId,
                onSuccess: onWorkflowResumed
            }));
        }
    };
    var handleEndWorkflow = function () {
        if (workflowId) {
            dispatch(actions_1.setWorkflowFinished({
                workflowId: workflowId,
                onWorkflowEnded: onWorkflowEnded
            }));
        }
    };
    var handleDeleteWorkflow = function () {
        dispatch(actions_1.deleteWorkflowAction({ workflowId: workflowId, onSuccess: onWorkflowDeleted }));
    };
    var handleChangeUrgent = function (isChecked) {
        onChangeUrgent === null || onChangeUrgent === void 0 ? void 0 : onChangeUrgent(isChecked);
        setIsUrgent(isChecked);
        dispatch(actions_1.editWorkflow({
            isUrgent: isChecked,
            workflowId: workflowId
        }));
    };
    var handleOnReturn = function (task) { return function () {
        dispatch(actions_1.returnWorkflowToTaskAction({ workflowId: workflowId, taskId: task.id, onSuccess: onWorkflowReturn }));
    }; };
    var handleEditTemplate = function () {
        if (templateId) {
            history_1.history.push(routes_1.getTemplateEditRoute(templateId));
        }
    };
    var handleSnoozeWorkflow = function (date) {
        dispatch(actions_1.snoozeWorkflow({
            workflowId: workflowId,
            date: date,
            onSuccess: onWorkflowSnoozed
        }));
    };
    var options = [
        {
            label: formatMessage({ id: 'workflows.card-resume' }),
            onClick: handleResumeWorkflow,
            Icon: icons_1.UnsnoozeIcon,
            withConfirmation: true,
            isHidden: !canResumeWorkflow,
            color: 'green',
            size: 'sm'
        },
        {
            label: (react_1["default"].createElement("div", { className: WorkflowControlls_css_1["default"]['urgent-wrapper'] },
                react_1["default"].createElement("span", { className: WorkflowControlls_css_1["default"]['urgent-text'] }, formatMessage({ id: 'workflows.card-urgent' })),
                react_1["default"].createElement(rc_switch_1["default"], { className: classnames_1["default"]('custom-switch custom-switch-primary custom-switch-small ml-auto'), checked: isUrgent, onChange: handleChangeUrgent, checkedChildren: null, unCheckedChildren: null }))),
            Icon: icons_1.UrgentIcon,
            isHidden: workflow.status === workflow_1.EWorkflowStatus.Finished,
            size: 'sm'
        },
        {
            label: formatMessage({ id: 'workflows.card-return' }),
            isHidden: !helpers_1.isArrayWithItems(passedTasks),
            Icon: icons_1.ReturnToIcon,
            subOptions: __spreadArrays(passedTasks).reverse().map(function (item, index) {
                var taskIndex = String(passedTasks.length - index).padStart(2, '0');
                return {
                    label: (react_1["default"].createElement("div", { className: WorkflowControlls_css_1["default"]['task-item'] },
                        react_1["default"].createElement("div", { className: WorkflowControlls_css_1["default"]['task-item__text'] }, item.name),
                        react_1["default"].createElement("div", { className: WorkflowControlls_css_1["default"]['task-item__index'] }, taskIndex))),
                    onClick: handleOnReturn(item),
                    withConfirmation: true,
                    size: 'lg'
                };
            }),
            size: 'sm'
        },
        {
            label: formatMessage({ id: 'workflows.card-snooze' }),
            Icon: icons_1.AlarmIcon,
            isHidden: !canSnoozeWorkflow,
            subOptions: snoozeOptions.map(function (option) {
                return {
                    label: (react_1["default"].createElement(react_1["default"].Fragment, null,
                        react_1["default"].createElement("span", { className: WorkflowControlls_css_1["default"]['dropdown-title'] }, option.title),
                        react_1["default"].createElement("span", { className: WorkflowControlls_css_1["default"]['dropdown-subtitle'] }, option.dateString))),
                    onClick: function () { return handleSnoozeWorkflow(option.dateISOString); },
                    size: 'lg'
                };
            }),
            size: 'sm'
        },
        {
            label: formatMessage({ id: 'workflows.clone' }),
            onClick: handleOnClone,
            Icon: icons_1.UnionIcon,
            isHidden: !canCloneWorkflow,
            size: 'sm'
        },
        {
            label: formatMessage({ id: 'workflows.edit-template' }),
            onClick: handleEditTemplate,
            Icon: icons_1.PencilIcon,
            isHidden: !templateId,
            size: 'sm'
        },
        {
            label: formatMessage({ id: 'workflows.card-end-workflow' }),
            onClick: handleEndWorkflow,
            Icon: icons_1.FlagIcon,
            withConfirmation: true,
            isHidden: !canEndWorkflow,
            size: 'sm'
        },
        {
            label: formatMessage({ id: 'workflows.card-delete' }),
            onClick: handleDeleteWorkflow,
            Icon: icons_1.TrashIcon,
            withConfirmation: true,
            isHidden: workflow.status === workflow_1.EWorkflowStatus.Finished,
            withUpperline: true,
            color: 'red',
            size: 'sm'
        },
    ];
    return react_1["default"].createElement(react_1["default"].Fragment, null, children(options));
}
exports.WorkflowControllsComponents = WorkflowControllsComponents;
