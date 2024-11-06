"use strict";
exports.__esModule = true;
exports.ProgressColumn = void 0;
var React = require("react");
var ProgressBar_1 = require("../../../../../../ProgressBar");
var getWorkflowProgress_1 = require("../../../../../utils/getWorkflowProgress");
var getWorkflowProgressColor_1 = require("../../../../../utils/getWorkflowProgressColor");
var ProgressbarTooltipContents_1 = require("../../../../../utils/ProgressbarTooltipContents");
function ProgressColumn(_a) {
    var workflow = _a.value;
    var currentTask = workflow.currentTask, tasksCount = workflow.tasksCount, status = workflow.status, task = workflow.task;
    var progress = getWorkflowProgress_1.getWorkflowProgress({ currentTask: currentTask, tasksCount: tasksCount, status: status });
    var color = getWorkflowProgressColor_1.getWorkflowProgressColor(status, [task.dueDate, workflow.dueDate]);
    return (React.createElement(ProgressBar_1.ProgressBar, { progress: progress, color: color, background: "#f6f6f6", tooltipContent: React.createElement(ProgressbarTooltipContents_1.ProgressbarTooltipContents, { workflow: workflow }) }));
}
exports.ProgressColumn = ProgressColumn;
