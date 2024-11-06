"use strict";
exports.__esModule = true;
exports.WorkflowEditPopupContainer = void 0;
var react_redux_1 = require("react-redux");
var actions_1 = require("../../redux/actions");
var WorkflowEditPopup_1 = require("./WorkflowEditPopup");
function mapStateToProps(_a) {
    var _b = _a.runWorkflowModal, isOpen = _b.isOpen, isWorkflowStarting = _b.isWorkflowStarting, workflow = _b.workflow, _c = _a.authUser, account = _c.account, isAdmin = _c.isAdmin, timezone = _c.timezone;
    return {
        isLoading: isWorkflowStarting,
        isOpen: isOpen,
        timezone: timezone,
        workflow: workflow,
        accountId: account.id || -1,
        isAdmin: Boolean(isAdmin)
    };
}
var mapDispatchToProps = {
    closeModal: actions_1.closeRunWorkflowModal,
    onRunWorkflow: actions_1.runWorkflow
};
exports.WorkflowEditPopupContainer = react_redux_1.connect(mapStateToProps, mapDispatchToProps)(WorkflowEditPopup_1.WorkflowEditPopup);
