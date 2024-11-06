"use strict";
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g;
    return g = { next: verb(0), "throw": verb(1), "return": verb(2) }, typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (_) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
var __spreadArrays = (this && this.__spreadArrays) || function () {
    for (var s = 0, i = 0, il = arguments.length; i < il; i++) s += arguments[i].length;
    for (var r = Array(s), k = 0, i = 0; i < il; i++)
        for (var a = arguments[i], j = 0, jl = a.length; j < jl; j++, k++)
            r[k] = a[j];
    return r;
};
exports.__esModule = true;
exports.rootSaga = exports.watchDeleteCurrentTaskDueDate = exports.watchSetCurrentTaskDueDate = exports.watchUnmarkChecklistItem = exports.watchMarkChecklistItem = exports.watchSetTaskCompleted = exports.watchAddTaskGuest = exports.watchLoadCurrentTask = exports.deleteCurrentTaskDueDateSaga = exports.setCurrentTaskDueDateSaga = exports.watchUpdateTaskPerformers = exports.watchSetTaskReverted = exports.updatePerformersSaga = exports.setTaskReverted = exports.setTaskCompleted = void 0;
/* eslint-disable */
/* prettier-ignore */
// tslint:disable: max-file-line-count
var effects_1 = require("redux-saga/effects");
var actions_1 = require("./actions");
var getTask_1 = require("../../api/getTask");
var logger_1 = require("../../utils/logger");
var routes_1 = require("../../constants/routes");
var Notifications_1 = require("../../components/common/Notifications");
var history_1 = require("../../utils/history");
var completeTask_1 = require("../../api/completeTask");
var revertTask_1 = require("../../api/revertTask");
var actions_2 = require("../actions");
var getErrorMessage_1 = require("../../utils/getErrorMessage");
var user_1 = require("../selectors/user");
var storageOutputs_1 = require("../../components/TaskCard/utils/storageOutputs");
var TaskCard_1 = require("../../components/TaskCard");
var deleteRemovedFilesFromFields_1 = require("../../api/deleteRemovedFilesFromFields");
var task_1 = require("../selectors/task");
var addTaskPerformer_1 = require("../../api/addTaskPerformer");
var removeTaskPerformer_1 = require("../../api/removeTaskPerformer");
var addTaskGuest_1 = require("../../api/addTaskGuest");
var removeTaskGuest_1 = require("../../api/removeTaskGuest");
var workflows_1 = require("../selectors/workflows");
var tasks_1 = require("../../utils/tasks");
var markChecklistItem_1 = require("../../api/markChecklistItem");
var unmarkChecklistItem_1 = require("../../api/unmarkChecklistItem");
var deleteTaskDueDate_1 = require("../../api/deleteTaskDueDate");
var changeTaskDueDate_1 = require("../../api/changeTaskDueDate");
function fetchTask(_a) {
    var _b, sorting, isCommentsShown, isOnlyAttachmentsShown, prevTask, task, normalizedTask, action, error_1, isTaskNotFound;
    var _c = _a.payload, taskId = _c.taskId, viewMode = _c.viewMode;
    return __generator(this, function (_d) {
        switch (_d.label) {
            case 0: return [4 /*yield*/, effects_1.select(workflows_1.getWorkflowLog)];
            case 1:
                _b = _d.sent(), sorting = _b.sorting, isCommentsShown = _b.isCommentsShown, isOnlyAttachmentsShown = _b.isOnlyAttachmentsShown;
                return [4 /*yield*/, effects_1.select(task_1.getCurrentTask)];
            case 2:
                prevTask = _d.sent();
                return [4 /*yield*/, effects_1.put(actions_1.setCurrentTask(null))];
            case 3:
                _d.sent();
                _d.label = 4;
            case 4:
                _d.trys.push([4, 9, 11, 13]);
                if (!Number.isInteger(taskId)) {
                    throw {
                        message: 'Not found.',
                        status: 404 /* NotFound */
                    };
                }
                return [4 /*yield*/, effects_1.put(actions_1.setCurrentTaskStatus(actions_1.ETaskStatus.Loading))];
            case 5:
                _d.sent();
                return [4 /*yield*/, getTask_1.getTask(taskId)];
            case 6:
                task = _d.sent();
                normalizedTask = tasks_1.getNormalizedTask(task);
                return [4 /*yield*/, effects_1.put(actions_1.setCurrentTask(normalizedTask))];
            case 7:
                _d.sent();
                action = viewMode !== TaskCard_1.ETaskCardViewMode.Guest
                    ? actions_2.loadWorkflow(task.workflow.id)
                    : actions_2.changeWorkflowLogViewSettings({
                        id: task.workflow.id,
                        sorting: sorting,
                        comments: isCommentsShown,
                        isOnlyAttachmentsShown: isOnlyAttachmentsShown
                    });
                return [4 /*yield*/, effects_1.put(action)];
            case 8:
                _d.sent();
                return [3 /*break*/, 13];
            case 9:
                error_1 = _d.sent();
                return [4 /*yield*/, effects_1.put(actions_1.setCurrentTask(prevTask))];
            case 10:
                _d.sent();
                if (viewMode === TaskCard_1.ETaskCardViewMode.Guest) {
                    history_1.history.replace(routes_1.ERoutes.Error);
                    return [2 /*return*/];
                }
                isTaskNotFound = (error_1 === null || error_1 === void 0 ? void 0 : error_1.status) === 404 /* NotFound */;
                if (isTaskNotFound && viewMode === TaskCard_1.ETaskCardViewMode.Single) {
                    history_1.history.replace(routes_1.ERoutes.Error);
                    return [2 /*return*/];
                }
                logger_1.logger.info('fetch current task error : ', error_1);
                Notifications_1.NotificationManager.warning({ message: getErrorMessage_1.getErrorMessage(error_1) });
                if (viewMode === TaskCard_1.ETaskCardViewMode.Single) {
                    history_1.history.replace(routes_1.ERoutes.Tasks);
                }
                return [3 /*break*/, 13];
            case 11: return [4 /*yield*/, effects_1.put(actions_1.setCurrentTaskStatus(actions_1.ETaskStatus.WaitingForAction))];
            case 12:
                _d.sent();
                return [7 /*endfinally*/];
            case 13: return [2 /*return*/];
        }
    });
}
function addTaskGuestSaga(_a) {
    var currentUsers, uploadedGuest, newUsers, error_2;
    var _b = _a.payload, taskId = _b.taskId, guestEmail = _b.guestEmail, onStartUploading = _b.onStartUploading, onEndUploading = _b.onEndUploading, onError = _b.onError;
    return __generator(this, function (_c) {
        switch (_c.label) {
            case 0: return [4 /*yield*/, effects_1.select(user_1.getUsers)];
            case 1:
                currentUsers = _c.sent();
                _c.label = 2;
            case 2:
                _c.trys.push([2, 6, , 7]);
                onStartUploading === null || onStartUploading === void 0 ? void 0 : onStartUploading();
                return [4 /*yield*/, effects_1.call(addTaskGuest_1.addTaskGuest, taskId, guestEmail)];
            case 3:
                uploadedGuest = _c.sent();
                newUsers = __spreadArrays(currentUsers, [uploadedGuest]);
                return [4 /*yield*/, effects_1.put(actions_2.usersFetchFinished(newUsers))];
            case 4:
                _c.sent();
                return [4 /*yield*/, addPerformersToList([uploadedGuest.id])];
            case 5:
                _c.sent();
                onEndUploading === null || onEndUploading === void 0 ? void 0 : onEndUploading();
                return [3 /*break*/, 7];
            case 6:
                error_2 = _c.sent();
                Notifications_1.NotificationManager.warning({ message: getErrorMessage_1.getErrorMessage(error_2) });
                onError === null || onError === void 0 ? void 0 : onError();
                return [3 /*break*/, 7];
            case 7: return [2 /*return*/];
        }
    });
}
function setTaskCompleted(_a) {
    var currentUserId, task, setChecklistsHandlingAction, areChecklistsHandled, err_1;
    var _b = _a.payload, taskId = _b.taskId, workflowId = _b.workflowId, output = _b.output, viewMode = _b.viewMode;
    return __generator(this, function (_c) {
        switch (_c.label) {
            case 0: return [4 /*yield*/, effects_1.select(user_1.getAuthUser)];
            case 1:
                currentUserId = (_c.sent()).authUser.id;
                if (!currentUserId) {
                    return [2 /*return*/];
                }
                return [4 /*yield*/, effects_1.put(actions_1.setCurrentTaskStatus(actions_1.ETaskStatus.Completing))];
            case 2:
                _c.sent();
                return [4 /*yield*/, effects_1.select(task_1.getCurrentTask)];
            case 3:
                task = _c.sent();
                if (!(task === null || task === void 0 ? void 0 : task.areChecklistsHandling)) return [3 /*break*/, 6];
                _c.label = 4;
            case 4:
                if (!true) return [3 /*break*/, 6];
                return [4 /*yield*/, effects_1.take("SET_CHECKLISTS_HANDLING" /* SetChecklistsHandling */)];
            case 5:
                setChecklistsHandlingAction = _c.sent();
                areChecklistsHandled = !setChecklistsHandlingAction.payload;
                if (areChecklistsHandled) {
                    return [3 /*break*/, 6];
                }
                return [3 /*break*/, 4];
            case 6:
                _c.trys.push([6, 12, , 14]);
                return [4 /*yield*/, deleteRemovedFilesFromFields_1.deleteRemovedFilesFromFields(output)];
            case 7:
                _c.sent();
                return [4 /*yield*/, completeTask_1.completeTask(workflowId, currentUserId, taskId, output)];
            case 8:
                _c.sent();
                Notifications_1.NotificationManager.success({ title: 'tasks.task-success-complete' });
                storageOutputs_1.removeOutputFromLocalStorage(taskId);
                return [4 /*yield*/, effects_1.put(actions_1.setCurrentTaskStatus(actions_1.ETaskStatus.Completed))];
            case 9:
                _c.sent();
                if (!(viewMode === TaskCard_1.ETaskCardViewMode.List)) return [3 /*break*/, 11];
                return [4 /*yield*/, effects_1.put(actions_2.shiftTaskList({ currentTaskId: taskId }))];
            case 10:
                _c.sent();
                _c.label = 11;
            case 11:
                if (viewMode === TaskCard_1.ETaskCardViewMode.Single) {
                    history_1.history.push(routes_1.ERoutes.Tasks);
                }
                return [3 /*break*/, 14];
            case 12:
                err_1 = _c.sent();
                logger_1.logger.error(err_1);
                Notifications_1.NotificationManager.warning({
                    title: 'tasks.task-fail-complete',
                    message: getErrorMessage_1.getErrorMessage(err_1)
                });
                return [4 /*yield*/, effects_1.put(actions_1.setCurrentTaskStatus(actions_1.ETaskStatus.WaitingForAction))];
            case 13:
                _c.sent();
                return [3 /*break*/, 14];
            case 14: return [2 /*return*/];
        }
    });
}
exports.setTaskCompleted = setTaskCompleted;
function setTaskReverted(_a) {
    var currentUserId, err_2;
    var _b = _a.payload, processId = _b.workflowId, viewMode = _b.viewMode, taskId = _b.taskId;
    return __generator(this, function (_c) {
        switch (_c.label) {
            case 0: return [4 /*yield*/, effects_1.select(user_1.getAuthUser)];
            case 1:
                currentUserId = (_c.sent()).authUser.id;
                if (!currentUserId) {
                    return [2 /*return*/];
                }
                _c.label = 2;
            case 2:
                _c.trys.push([2, 7, 8, 10]);
                return [4 /*yield*/, effects_1.put(actions_1.setCurrentTaskStatus(actions_1.ETaskStatus.Returning))];
            case 3:
                _c.sent();
                return [4 /*yield*/, revertTask_1.revertTask({ id: processId })];
            case 4:
                _c.sent();
                Notifications_1.NotificationManager.success({ message: 'tasks.task-success-revert' });
                if (!(viewMode === TaskCard_1.ETaskCardViewMode.List)) return [3 /*break*/, 6];
                return [4 /*yield*/, effects_1.put(actions_2.shiftTaskList({ currentTaskId: taskId }))];
            case 5:
                _c.sent();
                _c.label = 6;
            case 6:
                if (viewMode === TaskCard_1.ETaskCardViewMode.Single) {
                    history_1.history.push(routes_1.ERoutes.Tasks);
                }
                return [3 /*break*/, 10];
            case 7:
                err_2 = _c.sent();
                Notifications_1.NotificationManager.warning({
                    title: 'tasks.task-fail-revert',
                    message: getErrorMessage_1.getErrorMessage(err_2)
                });
                return [3 /*break*/, 10];
            case 8: return [4 /*yield*/, effects_1.put(actions_1.setCurrentTaskStatus(actions_1.ETaskStatus.WaitingForAction))];
            case 9:
                _c.sent();
                return [7 /*endfinally*/];
            case 10: return [2 /*return*/];
        }
    });
}
exports.setTaskReverted = setTaskReverted;
function addPerformersToList(userIds) {
    var performers, newPerformers;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.select(task_1.getTaskPerformers)];
            case 1:
                performers = _a.sent();
                newPerformers = __spreadArrays(performers, userIds);
                return [4 /*yield*/, effects_1.put(actions_1.changeTaskPerformers(newPerformers))];
            case 2:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
function removePerformersFromList(userId) {
    var performers, newPerformers;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.select(task_1.getTaskPerformers)];
            case 1:
                performers = _a.sent();
                newPerformers = performers.filter(function (performerId) { return !userId.includes(performerId); });
                return [4 /*yield*/, effects_1.put(actions_1.changeTaskPerformers(newPerformers))];
            case 2:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
function handleChangeChecklistItem(listApiName, itemApiName, isChecked) {
    var requestApi, task, checklist, checklistItem, error_3;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.put(actions_1.changeChecklistItem({ listApiName: listApiName, itemApiName: itemApiName, isChecked: isChecked }))];
            case 1:
                _a.sent();
                requestApi = isChecked ? markChecklistItem_1.markChecklistItem : unmarkChecklistItem_1.unmarkChecklistItem;
                return [4 /*yield*/, effects_1.select(task_1.getCurrentTask)];
            case 2:
                task = _a.sent();
                if (!task) {
                    return [2 /*return*/];
                }
                checklist = tasks_1.getTaskChecklist(task, listApiName);
                checklistItem = tasks_1.getTaskChecklistItem(task, listApiName, itemApiName);
                if (!checklist || !checklistItem) {
                    return [2 /*return*/];
                }
                _a.label = 3;
            case 3:
                _a.trys.push([3, 6, 8, 10]);
                return [4 /*yield*/, effects_1.put(actions_1.setChecklistsHandling(true))];
            case 4:
                _a.sent();
                return [4 /*yield*/, requestApi(checklist.id, checklistItem.id)];
            case 5:
                _a.sent();
                return [3 /*break*/, 10];
            case 6:
                error_3 = _a.sent();
                return [4 /*yield*/, effects_1.put(actions_1.changeChecklistItem({ listApiName: listApiName, itemApiName: itemApiName, isChecked: !isChecked }))];
            case 7:
                _a.sent();
                Notifications_1.NotificationManager.warning({ message: getErrorMessage_1.getErrorMessage(error_3) });
                logger_1.logger.info('failed to change checklist item: ', error_3);
                return [3 /*break*/, 10];
            case 8: return [4 /*yield*/, effects_1.put(actions_1.setChecklistsHandling(false))];
            case 9:
                _a.sent();
                return [7 /*endfinally*/];
            case 10: return [2 /*return*/];
        }
    });
}
function markChecklistItemSaga(_a) {
    var _b = _a.payload, listApiName = _b.listApiName, itemApiName = _b.itemApiName;
    return __generator(this, function (_c) {
        switch (_c.label) {
            case 0: return [4 /*yield*/, handleChangeChecklistItem(listApiName, itemApiName, true)];
            case 1:
                _c.sent();
                return [2 /*return*/];
        }
    });
}
function unmarkChecklistItemSaga(_a) {
    var _b = _a.payload, listApiName = _b.listApiName, itemApiName = _b.itemApiName;
    return __generator(this, function (_c) {
        switch (_c.label) {
            case 0: return [4 /*yield*/, handleChangeChecklistItem(listApiName, itemApiName, false)];
            case 1:
                _c.sent();
                return [2 /*return*/];
        }
    });
}
function updatePerformersSaga(_a) {
    var users, user, fetchMethodMap, fetchMethod, listAction, recoverListAction, error_4;
    var _b;
    var type = _a.type, _c = _a.payload, taskId = _c.taskId, userId = _c.userId;
    return __generator(this, function (_d) {
        switch (_d.label) {
            case 0: return [4 /*yield*/, effects_1.select(user_1.getUsers)];
            case 1:
                users = _d.sent();
                user = users.find(function (user) { return user.id === userId; });
                if (!user) {
                    return [2 /*return*/];
                }
                fetchMethodMap = [
                    {
                        check: function () { return type === "ADD_TASK_PERFORMER" /* AddTaskPerformer */ && user.type === 'user'; },
                        fetch: function () {
                            return __generator(this, function (_a) {
                                switch (_a.label) {
                                    case 0: return [4 /*yield*/, effects_1.call(addTaskPerformer_1.addTaskPerformer, taskId, userId)];
                                    case 1:
                                        _a.sent();
                                        return [2 /*return*/];
                                }
                            });
                        }
                    },
                    {
                        check: function () { return type === "REMOVE_TASK_PERFORMER" /* RemoveTaskPerformer */ && user.type === 'user'; },
                        fetch: function () {
                            return __generator(this, function (_a) {
                                switch (_a.label) {
                                    case 0: return [4 /*yield*/, effects_1.call(removeTaskPerformer_1.removeTaskPerformer, taskId, userId)];
                                    case 1:
                                        _a.sent();
                                        return [2 /*return*/];
                                }
                            });
                        }
                    },
                    {
                        check: function () { return type === "REMOVE_TASK_PERFORMER" /* RemoveTaskPerformer */ && user.type === 'guest'; },
                        fetch: function () {
                            return __generator(this, function (_a) {
                                switch (_a.label) {
                                    case 0: return [4 /*yield*/, effects_1.call(removeTaskGuest_1.removeTaskGuest, taskId, user.email)];
                                    case 1:
                                        _a.sent();
                                        return [2 /*return*/];
                                }
                            });
                        }
                    },
                ];
                fetchMethod = (_b = fetchMethodMap.find(function (_a) {
                    var check = _a.check;
                    return check();
                })) === null || _b === void 0 ? void 0 : _b.fetch;
                if (!fetchMethod) {
                    return [2 /*return*/];
                }
                listAction = type === "ADD_TASK_PERFORMER" /* AddTaskPerformer */ ? addPerformersToList : removePerformersFromList;
                recoverListAction = type === "ADD_TASK_PERFORMER" /* AddTaskPerformer */ ? removePerformersFromList : addPerformersToList;
                _d.label = 2;
            case 2:
                _d.trys.push([2, 5, , 7]);
                return [4 /*yield*/, listAction([userId])];
            case 3:
                _d.sent();
                return [4 /*yield*/, fetchMethod()];
            case 4:
                _d.sent();
                return [3 /*break*/, 7];
            case 5:
                error_4 = _d.sent();
                return [4 /*yield*/, recoverListAction([userId])];
            case 6:
                _d.sent();
                Notifications_1.NotificationManager.error({ message: getErrorMessage_1.getErrorMessage(error_4) });
                logger_1.logger.info('failed to update task performers: ', error_4);
                return [3 /*break*/, 7];
            case 7: return [2 /*return*/];
        }
    });
}
exports.updatePerformersSaga = updatePerformersSaga;
function watchSetTaskReverted() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("SET_TASK_REVERTED" /* SetTaskReverted */, function (action) {
                    var handlerAction;
                    return __generator(this, function (_a) {
                        switch (_a.label) {
                            case 0:
                                handlerAction = {
                                    type: "TASK_LIST_CHANNEL_ACTION" /* ChannelAction */,
                                    handler: function () { return setTaskReverted(action); }
                                };
                                return [4 /*yield*/, effects_1.put(handlerAction)];
                            case 1:
                                _a.sent();
                                return [2 /*return*/];
                        }
                    });
                })];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchSetTaskReverted = watchSetTaskReverted;
function watchUpdateTaskPerformers() {
    var changePerformersChannel, action;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.actionChannel([
                    "ADD_TASK_PERFORMER" /* AddTaskPerformer */,
                    "REMOVE_TASK_PERFORMER" /* RemoveTaskPerformer */,
                ])];
            case 1:
                changePerformersChannel = _a.sent();
                _a.label = 2;
            case 2:
                if (!true) return [3 /*break*/, 5];
                return [4 /*yield*/, effects_1.take(changePerformersChannel)];
            case 3:
                action = _a.sent();
                return [4 /*yield*/, updatePerformersSaga(action)];
            case 4:
                _a.sent();
                return [3 /*break*/, 2];
            case 5: return [2 /*return*/];
        }
    });
}
exports.watchUpdateTaskPerformers = watchUpdateTaskPerformers;
function setCurrentTaskDueDateSaga(_a) {
    var task, error_5;
    var dueDate = _a.payload;
    return __generator(this, function (_b) {
        switch (_b.label) {
            case 0: return [4 /*yield*/, effects_1.select(task_1.getCurrentTask)];
            case 1:
                task = _b.sent();
                if (!task) {
                    return [2 /*return*/];
                }
                _b.label = 2;
            case 2:
                _b.trys.push([2, 6, , 8]);
                return [4 /*yield*/, effects_1.put(actions_1.patchCurrentTask({ dueDate: dueDate }))];
            case 3:
                _b.sent();
                return [4 /*yield*/, effects_1.put(actions_2.patchTaskInList({ taskId: task.id, task: { dueDate: dueDate } }))];
            case 4:
                _b.sent();
                return [4 /*yield*/, effects_1.call(changeTaskDueDate_1.changeTaskDueDate, task.id, dueDate)];
            case 5:
                _b.sent();
                return [3 /*break*/, 8];
            case 6:
                error_5 = _b.sent();
                Notifications_1.NotificationManager.warning({ message: getErrorMessage_1.getErrorMessage(error_5) });
                logger_1.logger.info('failed to change task due date: ', error_5);
                return [4 /*yield*/, effects_1.put(actions_1.patchCurrentTask({ dueDate: task.dueDate }))];
            case 7:
                _b.sent();
                return [3 /*break*/, 8];
            case 8: return [2 /*return*/];
        }
    });
}
exports.setCurrentTaskDueDateSaga = setCurrentTaskDueDateSaga;
function deleteCurrentTaskDueDateSaga() {
    var task, error_6;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.select(task_1.getCurrentTask)];
            case 1:
                task = _a.sent();
                if (!task) {
                    return [2 /*return*/];
                }
                _a.label = 2;
            case 2:
                _a.trys.push([2, 6, , 8]);
                return [4 /*yield*/, effects_1.put(actions_1.patchCurrentTask({ dueDate: null }))];
            case 3:
                _a.sent();
                return [4 /*yield*/, effects_1.put(actions_2.patchTaskInList({ taskId: task.id, task: { dueDate: null } }))];
            case 4:
                _a.sent();
                return [4 /*yield*/, effects_1.call(deleteTaskDueDate_1.deleteTaskDueDate, task.id)];
            case 5:
                _a.sent();
                return [3 /*break*/, 8];
            case 6:
                error_6 = _a.sent();
                Notifications_1.NotificationManager.warning({ message: getErrorMessage_1.getErrorMessage(error_6) });
                logger_1.logger.info('failed to delete task due date: ', error_6);
                return [4 /*yield*/, effects_1.put(actions_1.patchCurrentTask({ dueDate: task.dueDate }))];
            case 7:
                _a.sent();
                return [3 /*break*/, 8];
            case 8: return [2 /*return*/];
        }
    });
}
exports.deleteCurrentTaskDueDateSaga = deleteCurrentTaskDueDateSaga;
function watchLoadCurrentTask() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("LOAD_CURRENT_TASK" /* LoadCurrentTask */, fetchTask)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchLoadCurrentTask = watchLoadCurrentTask;
function watchAddTaskGuest() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("ADD_TASK_GUEST" /* AddTaskGuest */, addTaskGuestSaga)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchAddTaskGuest = watchAddTaskGuest;
function watchSetTaskCompleted() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("SET_TASK_COMPLETED" /* SetTaskCompleted */, function (action) {
                    var handlerAction;
                    return __generator(this, function (_a) {
                        switch (_a.label) {
                            case 0:
                                handlerAction = {
                                    type: "TASK_LIST_CHANNEL_ACTION" /* ChannelAction */,
                                    handler: function () { return setTaskCompleted(action); }
                                };
                                return [4 /*yield*/, effects_1.put(handlerAction)];
                            case 1:
                                _a.sent();
                                return [2 /*return*/];
                        }
                    });
                })];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchSetTaskCompleted = watchSetTaskCompleted;
function watchMarkChecklistItem() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("MARK_CHECKLIST_ITEM" /* MarkChecklistItem */, markChecklistItemSaga)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchMarkChecklistItem = watchMarkChecklistItem;
function watchUnmarkChecklistItem() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("UNMARK_CHECKLIST_ITEM" /* UnmarkChecklistItem */, unmarkChecklistItemSaga)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchUnmarkChecklistItem = watchUnmarkChecklistItem;
function watchSetCurrentTaskDueDate() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("SET_CURRENT_TASK_DUE_DATE" /* SetCurrentTaskDueDate */, setCurrentTaskDueDateSaga)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchSetCurrentTaskDueDate = watchSetCurrentTaskDueDate;
function watchDeleteCurrentTaskDueDate() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("DELETE_CURRENT_TASK_DUE_DATE" /* DeleteCurrentTaskDueDate */, deleteCurrentTaskDueDateSaga)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchDeleteCurrentTaskDueDate = watchDeleteCurrentTaskDueDate;
function rootSaga() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.all([
                    effects_1.fork(watchLoadCurrentTask),
                    effects_1.fork(watchSetTaskCompleted),
                    effects_1.fork(watchSetTaskReverted),
                    effects_1.fork(watchUpdateTaskPerformers),
                    effects_1.fork(watchAddTaskGuest),
                    effects_1.fork(watchMarkChecklistItem),
                    effects_1.fork(watchUnmarkChecklistItem),
                    effects_1.fork(watchSetCurrentTaskDueDate),
                    effects_1.fork(watchDeleteCurrentTaskDueDate),
                ])];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.rootSaga = rootSaga;
