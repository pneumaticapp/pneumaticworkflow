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
exports.WorkflowEditPopup = void 0;
/* eslint-disable */
/* prettier-ignore */
var React = require("react");
var classnames_1 = require("classnames");
var react_truncate_1 = require("react-truncate");
var reactstrap_1 = require("reactstrap");
var react_intl_1 = require("react-intl");
var rc_switch_1 = require("rc-switch");
var moment_timezone_1 = require("moment-timezone");
var defaultValues_1 = require("../../constants/defaultValues");
var routes_1 = require("../../constants/routes");
var Field_1 = require("../Field");
var history_1 = require("../../utils/history");
var IntlMessages_1 = require("../IntlMessages");
var workflow_1 = require("../../types/workflow");
var template_1 = require("../../types/template");
var helpers_1 = require("../../utils/helpers");
var getEditedFields_1 = require("../TemplateEdit/ExtraFields/utils/getEditedFields");
var getInitialKickoff_1 = require("./utils/getInitialKickoff");
var ExtraFields_1 = require("../TemplateEdit/ExtraFields");
var icons_1 = require("../icons");
var validators_1 = require("../../utils/validators");
var areKickoffFieldsValid_1 = require("./utils/areKickoffFieldsValid");
var Button_1 = require("../UI/Buttons/Button");
var RichText_1 = require("../RichText");
var UI_1 = require("../UI");
var DateFormat_1 = require("../UI/DateFormat");
var reactElementToText_1 = require("../../utils/reactElementToText");
var Templates_css_1 = require("../Templates/Templates.css");
function WorkflowEditPopup(_a) {
    var isOpen = _a.isOpen, isLoading = _a.isLoading, workflow = _a.workflow, timezone = _a.timezone, accountId = _a.accountId, isAdmin = _a.isAdmin, closeModal = _a.closeModal, onRunWorkflow = _a.onRunWorkflow;
    if (!workflow)
        return null;
    var formatMessage = react_intl_1.useIntl().formatMessage;
    var _b = React.useState(null), dueDate = _b[0], setDueDate = _b[1];
    var descriptionLinesCount = 5;
    var _c = React.useState(reactElementToText_1.reactElementToText(React.createElement(DateFormat_1.DateFormat, null)) + " \u2014 " + workflow.name), workflowName = _c[0], changeWorkflowName = _c[1];
    var _d = React.useState(getInitialKickoff_1.getInitialKickoff(workflow.kickoff)), kickoffState = _d[0], setKickoffState = _d[1];
    var _e = React.useState(false), isUrgent = _e[0], setIsUrgent = _e[1];
    var onChange = function (e) { return changeWorkflowName(e.currentTarget.value); };
    var _f = React.useState(false), textExpaned = _f[0], setTextExpanded = _f[1];
    var expandText = React.useCallback(function () { return setTextExpanded(!textExpaned); }, [textExpaned]);
    var ellispis = (React.createElement("a", { onClick: expandText, className: Templates_css_1["default"]['description_more'] },
        React.createElement("span", { className: Templates_css_1["default"]['more_delimeter'] }, defaultValues_1.ELLIPSIS_CHAR),
        React.createElement(IntlMessages_1.IntlMessages, { id: "templates.description-more" })));
    var handleEditField = function (apiName) { return function (changedProps) {
        setKickoffState(function (prevKickoff) {
            var newFields = getEditedFields_1.getEditedFields(prevKickoff.fields, apiName, changedProps);
            return __assign(__assign({}, prevKickoff), { fields: newFields });
        });
    }; };
    var isWorkflowsStartButtonDisabled = isLoading || Boolean(validators_1.validateWorkflowName(workflowName)) || !areKickoffFieldsValid_1.checkExtraFieldsAreValid(kickoffState === null || kickoffState === void 0 ? void 0 : kickoffState.fields);
    var handleToggleIsUrgent = function () { return setIsUrgent(!isUrgent); };
    var renderUrgentSwitch = function () {
        var handleSwitch = function () {
            handleToggleIsUrgent === null || handleToggleIsUrgent === void 0 ? void 0 : handleToggleIsUrgent();
        };
        return (React.createElement("div", { className: Templates_css_1["default"]['urgent-switch'] },
            React.createElement("div", { className: Templates_css_1["default"]['urgent-switch__label'] }, formatMessage({ id: 'workflows.card-urgent' })),
            React.createElement(rc_switch_1["default"], { className: classnames_1["default"]('custom-switch custom-switch-primary custom-switch-small ml-auto', Templates_css_1["default"]['urgent-switch__switch']), checkedChildren: null, unCheckedChildren: null, onChange: handleSwitch, checked: isUrgent })));
    };
    var renderModalHeader = function () {
        return (React.createElement(reactstrap_1.ModalHeader, { className: Templates_css_1["default"]['popup-header'], toggle: closeModal },
            React.createElement("div", { className: Templates_css_1["default"]['popup-pretitle'] },
                React.createElement(IntlMessages_1.IntlMessages, { id: "templates.popup-header-info" })),
            React.createElement("div", { className: Templates_css_1["default"]['popup-title'] },
                isUrgent ? (React.createElement("div", { className: 'urgent-badge' },
                    React.createElement(IntlMessages_1.IntlMessages, { id: "workflows.card-urgent" }))) : null,
                React.createElement("div", { className: Templates_css_1["default"]['popup-title__name'] }, workflow.name)),
            workflow.description && (React.createElement("div", { className: Templates_css_1["default"]['popup-description'] },
                React.createElement(react_truncate_1["default"], { lines: !textExpaned && descriptionLinesCount, ellipsis: ellispis, trimWhitespace: true }, workflow.description.split('\n').map(function (el, i, arr) {
                    var line = React.createElement("span", { key: i }, el);
                    if (i === arr.length - 1) {
                        return line;
                    }
                    else {
                        return [line, React.createElement("br", { key: i + "br" })];
                    }
                })))),
            React.createElement("div", { className: Templates_css_1["default"]['workflow-modal-info'] },
                React.createElement("div", { className: Templates_css_1["default"]['workflow-modal-info__stats'] },
                    workflow.tasksCount && (React.createElement("div", null,
                        React.createElement("span", { className: Templates_css_1["default"]['workflow-modal-info__stats-amount'] }, workflow.tasksCount),
                        "\u00A0",
                        React.createElement("span", null, helpers_1.getPluralNoun({
                            counter: workflow.tasksCount,
                            single: 'step',
                            plural: 'steps'
                        })))),
                    workflow.performersCount && (React.createElement("div", null,
                        React.createElement("span", { className: Templates_css_1["default"]['workflow-modal-info__stats-amount'] }, workflow.performersCount),
                        "\u00A0",
                        React.createElement("span", null, helpers_1.getPluralNoun({
                            counter: workflow.performersCount,
                            single: 'performer',
                            plural: 'performers'
                        }))))),
                renderUrgentSwitch())));
    };
    var renderTemplateEditButton = function () {
        var redirectToWorkflowEdit = function (e) {
            e.preventDefault();
            var redirectUrl = routes_1.ERoutes.TemplatesEdit.replace(':id', String(workflow.id));
            if (!history_1.history.location.pathname.includes(redirectUrl)) {
                history_1.history.push(redirectUrl);
            }
            closeModal();
        };
        return (React.createElement(Button_1.Button, { buttonStyle: "transparent-black", onClick: redirectToWorkflowEdit, label: formatMessage({ id: 'templates.edit-template' }), className: Templates_css_1["default"]['popup-buttons__button_edit-template'], size: "md" }));
    };
    var handleRunWorkflow = function (event) {
        event.preventDefault();
        onRunWorkflow(__assign(__assign({}, workflow), { kickoff: kickoffState, name: workflowName, isUrgent: isUrgent, dueDate: dueDate || undefined }));
    };
    return (React.createElement("div", { className: Templates_css_1["default"]['popup'] },
        React.createElement(reactstrap_1.Modal, { isOpen: isOpen, backdrop: "static", wrapClassName: classnames_1["default"]('processes-workflows-popup', Templates_css_1["default"]['workflows-modal']) },
            React.createElement(reactstrap_1.Form, { onSubmit: handleRunWorkflow },
                renderModalHeader(),
                React.createElement(reactstrap_1.ModalBody, { className: Templates_css_1["default"]['popup-body'] },
                    React.createElement("div", { className: Templates_css_1["default"]['modal-body_hint'] },
                        React.createElement(IntlMessages_1.IntlMessages, { id: "templates.body-hint" })),
                    React.createElement(Field_1.Field, { className: Templates_css_1["default"]['modal-body_input'], intlId: "templates.start-name", onChange: onChange, value: workflowName, validate: validators_1.validateWorkflowName, labelClassName: classnames_1["default"]('form-group mb-5', Templates_css_1["default"]['field-button']) }),
                    kickoffState && helpers_1.isArrayWithItems(kickoffState.fields) && (React.createElement("div", { className: Templates_css_1["default"]['popup__kickoff'] },
                        React.createElement(UI_1.SectionTitle, { className: Templates_css_1["default"]['section-title'] }, formatMessage({ id: 'template.kick-off-form-title' })),
                        kickoffState.description && (React.createElement("span", { className: Templates_css_1["default"]['kickoff__description'] },
                            React.createElement(RichText_1.RichText, { text: kickoffState.description }))),
                        React.createElement("div", { className: Templates_css_1["default"]['kickoff__inputs'] }, kickoffState.fields.map(function (field) { return (React.createElement(ExtraFields_1.ExtraFieldIntl, { key: field.apiName, field: __assign({}, field), editField: handleEditField(field.apiName), showDropdown: false, mode: template_1.EExtraFieldMode.ProcessRun, labelBackgroundColor: workflow_1.EInputNameBackgroundColor.OrchidWhite, namePlaceholder: field.name, descriptionPlaceholder: field.description, wrapperClassName: Templates_css_1["default"]['kickoff-extra-field'], accountId: accountId })); })))),
                    React.createElement("div", null,
                        React.createElement(UI_1.SectionTitle, { className: Templates_css_1["default"]['section-title'] }, formatMessage({ id: 'templates.due-date-title' })),
                        React.createElement(UI_1.DateField, { value: dueDate, onChange: setDueDate, title: formatMessage({ id: 'templates.due-date-field' }), foregroundColor: "beige", minDate: moment_timezone_1["default"].tz(timezone).add(1, 'days').format('YYYY-MM-DD') })),
                    React.createElement("div", { className: Templates_css_1["default"]['popup-buttons'] },
                        React.createElement(Button_1.Button, { buttonStyle: "yellow", type: "submit", disabled: isWorkflowsStartButtonDisabled, icon: icons_1.PlayLogoIcon, label: formatMessage({ id: 'templates.start-submit' }), className: Templates_css_1["default"]['popup-buttons__button'], size: "md", isLoading: isLoading }),
                        isAdmin && renderTemplateEditButton()))))));
}
exports.WorkflowEditPopup = WorkflowEditPopup;
