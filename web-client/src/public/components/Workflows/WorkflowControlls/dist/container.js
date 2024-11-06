"use strict";
exports.__esModule = true;
exports.WorkflowControlls = void 0;
var react_redux_1 = require("react-redux");
var WorkflowControlls_1 = require("./WorkflowControlls");
function mapStateToProps(_a) {
    var timezone = _a.authUser.timezone;
    return {
        timezone: timezone
    };
}
exports.WorkflowControlls = react_redux_1.connect(mapStateToProps)(WorkflowControlls_1.WorkflowControllsComponents);
