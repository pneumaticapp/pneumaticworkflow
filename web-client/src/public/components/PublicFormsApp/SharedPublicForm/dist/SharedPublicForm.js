"use strict";
exports.__esModule = true;
exports.SharedPublicForm = void 0;
var react_1 = require("react");
var Notifications_1 = require("../../UI/Notifications");
var Copyright_1 = require("../common/Copyright");
var PublicForm_1 = require("../common/PublicForm/PublicForm");
var SharedPublicForm_css_1 = require("./SharedPublicForm.css");
function SharedPublicForm() {
    return (react_1["default"].createElement("div", { className: SharedPublicForm_css_1["default"]['container'] },
        react_1["default"].createElement(Notifications_1.NotificationContainer, null),
        react_1["default"].createElement(PublicForm_1.PublicForm, { type: "shared" }),
        react_1["default"].createElement(Copyright_1.Copyright, null)));
}
exports.SharedPublicForm = SharedPublicForm;
