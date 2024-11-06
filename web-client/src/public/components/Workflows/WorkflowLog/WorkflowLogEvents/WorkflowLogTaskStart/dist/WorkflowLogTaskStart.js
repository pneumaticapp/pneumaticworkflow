"use strict";
exports.__esModule = true;
exports.WorkflowLogTaskStart = void 0;
/* eslint-disable */
/* prettier-ignore */
var React = require("react");
var classnames_1 = require("classnames");
var react_router_dom_1 = require("react-router-dom");
var react_intl_1 = require("react-intl");
var Avatar_1 = require("../../../../UI/Avatar");
var Header_1 = require("../../../../UI/Typeography/Header");
var strings_1 = require("../../../../../utils/strings");
var routes_1 = require("../../../../../constants/routes");
var UserData_1 = require("../../../../UserData");
var getLastTaskLogEventId_1 = require("./utils/getLastTaskLogEventId");
var icons_1 = require("../../../../icons");
var getDueInData_1 = require("../../../../DueIn/utils/getDueInData");
var WorkflowLogTaskStart_css_1 = require("./WorkflowLogTaskStart.css");
var MAX_SHOW_USERS = 5;
function WorkflowLogTaskStart(_a) {
    var id = _a.id, logItems = _a.logItems, sorting = _a.sorting, task = _a.task, created = _a.created, currentTask = _a.currentTask, areTasksClickable = _a.areTasksClickable, theme = _a.theme, onClickTask = _a.onClickTask;
    var dueDate = (id === getLastTaskLogEventId_1.getLastTaskLogEventId(logItems, sorting) && (currentTask === null || currentTask === void 0 ? void 0 : currentTask.dueDate)) || null;
    var formatMessage = react_intl_1.useIntl().formatMessage;
    var renderResponsiblesAvatars = function () {
        if (!(task === null || task === void 0 ? void 0 : task.performers)) {
            return null;
        }
        var usersLeft = Math.max((task === null || task === void 0 ? void 0 : task.performers.length) - MAX_SHOW_USERS, 0);
        return (React.createElement("div", { className: WorkflowLogTaskStart_css_1["default"]['start-responsibles'] }, task === null || task === void 0 ? void 0 :
            task.performers.slice(0, MAX_SHOW_USERS).map(function (userId, index) { return (React.createElement(UserData_1.UserData, { key: index, userId: userId }, function (user) {
                if (!user) {
                    return null;
                }
                return (React.createElement(Avatar_1.Avatar, { user: user, size: "sm", containerClassName: WorkflowLogTaskStart_css_1["default"]['start-responsible'], showInitials: false, withTooltip: true }));
            })); }),
            Boolean(usersLeft) && React.createElement("span", { className: WorkflowLogTaskStart_css_1["default"]['start-responsibles__more'] },
                "+",
                usersLeft)));
    };
    var renderTitle = function () {
        var redirectUrl = routes_1.ERoutes.TaskDetail.replace(':id', String(task === null || task === void 0 ? void 0 : task.id));
        var title = areTasksClickable ? (React.createElement(react_router_dom_1.Link, { to: redirectUrl, onClick: onClickTask }, task === null || task === void 0 ? void 0 : task.name)) : (task === null || task === void 0 ? void 0 : task.name);
        return (React.createElement(Header_1.Header, { tag: "h3", size: "6", className: WorkflowLogTaskStart_css_1["default"]['task-name'] }, title));
    };
    var renderDueIn = function () {
        var dueInData = getDueInData_1.getDueInData([dueDate]);
        if (!dueInData) {
            return null;
        }
        var timeLeft = dueInData.timeLeft, statusTitle = dueInData.statusTitle, isOverdue = dueInData.isOverdue;
        return (React.createElement("div", { className: classnames_1["default"](WorkflowLogTaskStart_css_1["default"]['due-in'], isOverdue && WorkflowLogTaskStart_css_1["default"]['due-in_overdue']) },
            React.createElement("p", { className: WorkflowLogTaskStart_css_1["default"]['due-in__inner'] },
                React.createElement("span", { className: WorkflowLogTaskStart_css_1["default"]['due-in__text'] }, formatMessage({ id: statusTitle }, { duration: timeLeft })),
                React.createElement(icons_1.ClockIcon, { className: WorkflowLogTaskStart_css_1["default"]['due-in__icon'] }))));
    };
    var getThemeClassName = React.useCallback(function () {
        var themeClassNameMap = {
            beige: WorkflowLogTaskStart_css_1["default"]['container-beige'],
            white: WorkflowLogTaskStart_css_1["default"]['container-white']
        };
        return themeClassNameMap[theme];
    }, [theme]);
    return (React.createElement("div", { className: classnames_1["default"](WorkflowLogTaskStart_css_1["default"]['container'], getThemeClassName()) },
        React.createElement("div", { className: WorkflowLogTaskStart_css_1["default"]['top-area'] },
            React.createElement("div", { className: WorkflowLogTaskStart_css_1["default"]['top-area__meta'] },
                React.createElement("p", { className: WorkflowLogTaskStart_css_1["default"]['pre-title'] }, formatMessage({ id: 'workflows.log-task-started-pre-title' }, { task: task === null || task === void 0 ? void 0 : task.number })),
                React.createElement("p", { className: WorkflowLogTaskStart_css_1["default"]['date-started'] },
                    formatMessage({ id: 'workflows.log-task-started' }),
                    "\u00A0",
                    React.createElement("span", { className: WorkflowLogTaskStart_css_1["default"]['date-started__date'] }, String(strings_1.getDate(created))))),
            renderTitle()),
        React.createElement("div", { className: WorkflowLogTaskStart_css_1["default"]['bottom-area'] },
            renderResponsiblesAvatars(),
            renderDueIn())));
}
exports.WorkflowLogTaskStart = WorkflowLogTaskStart;
