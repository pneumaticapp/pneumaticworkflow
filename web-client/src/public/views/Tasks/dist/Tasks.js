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
exports.__esModule = true;
exports.TasksView = void 0;
var React = require("react");
var component_1 = require("@loadable/component");
var react_router_dom_1 = require("react-router-dom");
var layout_1 = require("../../layout");
var routes_1 = require("../../constants/routes");
var Tasks_1 = require("../../components/Tasks");
var UI_1 = require("../../components/UI");
var Task = component_1["default"](function () { return Promise.resolve().then(function () { return require(/* webpackChunkName: "task", webpackPrefetch: true */ '../../components/TaskDetail'); }); }, { fallback: React.createElement(UI_1.Loader, { isLoading: true }) });
exports.TasksView = function () {
    return (React.createElement(layout_1.TasksLayout, null,
        React.createElement(React.Suspense, { fallback: React.createElement("div", { className: "loading" }) },
            React.createElement(react_router_dom_1.Switch, null,
                React.createElement(react_router_dom_1.Route, { path: routes_1.ERoutes.TaskDetail, render: function (props) {
                        var id = props.match.params.id;
                        return React.createElement(Task, __assign({ key: "task-" + id }, props));
                    } }),
                React.createElement(react_router_dom_1.Route, { path: routes_1.ERoutes.Tasks, component: Tasks_1.TasksContainer }),
                React.createElement(react_router_dom_1.Redirect, { to: routes_1.ERoutes.Error })))));
};
