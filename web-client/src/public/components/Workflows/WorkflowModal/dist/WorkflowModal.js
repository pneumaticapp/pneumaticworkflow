'use strict';
var __extends =
  (this && this.__extends) ||
  (function () {
    var extendStatics = function (d, b) {
      extendStatics =
        Object.setPrototypeOf ||
        ({ __proto__: [] } instanceof Array &&
          function (d, b) {
            d.__proto__ = b;
          }) ||
        function (d, b) {
          for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p];
        };
      return extendStatics(d, b);
    };
    return function (d, b) {
      extendStatics(d, b);
      function __() {
        this.constructor = d;
      }
      d.prototype = b === null ? Object.create(b) : ((__.prototype = b.prototype), new __());
    };
  })();
var __assign =
  (this && this.__assign) ||
  function () {
    __assign =
      Object.assign ||
      function (t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
          s = arguments[i];
          for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p)) t[p] = s[p];
        }
        return t;
      };
    return __assign.apply(this, arguments);
  };
exports.__esModule = true;
exports.WorkflowModal = void 0;
/* eslint-disable */
/* prettier-ignore */
/* tslint:disable:max-file-line-count */
var React = require("react");
var classnames_1 = require('classnames');
var react_outside_click_handler_1 = require('react-outside-click-handler');
var react_textarea_autosize_1 = require('react-textarea-autosize');
var reactstrap_1 = require('reactstrap');
var Avatar_1 = require('../../UI/Avatar');
var icons_1 = require('../../icons');
var KickoffEdit_1 = require('../../KickoffEdit');
var workflows_1 = require('../../../utils/workflows');
var helpers_1 = require('../../../utils/helpers');
var users_1 = require('../../../utils/users');
var IntlMessages_1 = require('../../IntlMessages');
var KickoffOutputs_1 = require('../../KickoffOutputs');
var Loader_1 = require('../../UI/Loader');
var WorkflowLog_1 = require('../WorkflowLog');
var WorkflowModalHeaderProgressBar_1 = require('./WorkflowModalHeaderProgressBar');
var validators_1 = require('../../../utils/validators');
var TemplateName_1 = require('../../UI/TemplateName');
var getWorkflowProgressColor_1 = require('../utils/getWorkflowProgressColor');
var countCompletedTasks_1 = require('../utils/countCompletedTasks');
var getEditedFields_1 = require('../../TemplateEdit/ExtraFields/utils/getEditedFields');
var UserData_1 = require('../../UserData');
var DueIn_1 = require('../../DueIn');
var DateFormat_1 = require('../../UI/DateFormat');
var WorkflowModal_css_1 = require('./WorkflowModal.css');
var WorkflowModal = /** @class */ (function (_super) {
  __extends(WorkflowModal, _super);
  function WorkflowModal(props) {
    var _this = _super.call(this, props) || this;
    _this.calculateWorkflowProgress = function () {
      if (!_this.props.workflow) {
        return undefined;
      }
      var _a = _this.props.workflow,
        currentTask = _a.currentTask,
        tasksCount = _a.tasksCount,
        status = _a.status;
      if (currentTask && currentTask.number && tasksCount) {
        return helpers_1.getPercent(countCompletedTasks_1.countCompletedTasks(currentTask.number, status), tasksCount);
      }
      return undefined;
    };
    _this.renderWorkflowAsideInfo = function (_a) {
      var isMobile = _a.isMobile;
      var _b = _this.props,
        workflow = _b.workflow,
        workflowId = _b.workflowId,
        onWorkflowEnded = _b.onWorkflowEnded,
        onWorkflowSnoozed = _b.onWorkflowSnoozed,
        onWorkflowResumed = _b.onWorkflowResumed,
        onWorkflowDeleted = _b.onWorkflowDeleted;
      if (!workflowId || !workflow) {
        return null;
      }
      return React.createElement(WorkflowModalHeaderProgressBar_1.WorkflowModalHeaderProgressBar, {
        progress: _this.processProgress,
        color: getWorkflowProgressColor_1.getWorkflowProgressColor(workflow.status, [
          workflow.currentTask.dueDate,
          workflow.dueDate,
        ]),
        workflow: workflow,
        workflowId: workflowId,
        closeModal: _this.closeModal,
        isMobile: isMobile,
        onWorkflowEnded: onWorkflowEnded,
        onWorkflowSnoozed: onWorkflowSnoozed,
        onWorkflowResumed: onWorkflowResumed,
        onWorkflowDeleted: onWorkflowDeleted,
      });
    };
    _this.renderWorkflowName = function () {
      if (!_this.props.workflow) {
        return null;
      }
      var _a = _this.props,
        _b = _a.workflow,
        initialName = _b.name,
        isUrgent = _b.isUrgent,
        _c = _a.workflowEdit,
        isWorkflowNameEditing = _c.isWorkflowNameEditing,
        isWorkflowNameSaving = _c.isWorkflowNameSaving,
        workflowEditData = _c.workflow,
        name = _c.workflow.name,
        canEdit = _a.canEdit,
        setIsEditWorkflowName = _a.setIsEditWorkflowName,
        setWorkflowEdit = _a.setWorkflowEdit;
      if (!isWorkflowNameEditing) {
        return React.createElement(
          'div',
          { className: WorkflowModal_css_1['default']['popup-name-container'] },
          React.createElement(
            'div',
            { className: WorkflowModal_css_1['default']['popup-title'] },
            isUrgent
              ? React.createElement(
                  'div',
                  { className: WorkflowModal_css_1['default']['popup-title_urgent'] },
                  React.createElement(IntlMessages_1.IntlMessages, { id: 'workflows.card-urgent' }),
                )
              : null,
            React.createElement('div', { className: WorkflowModal_css_1['default']['popup-title_name'] }, initialName),
            canEdit &&
              React.createElement(
                React.Fragment,
                null,
                '\u00A0\u00A0',
                React.createElement(
                  'button',
                  {
                    type: 'button',
                    className: WorkflowModal_css_1['default']['popup-title__edit'],
                    onClick: function () {
                      return setIsEditWorkflowName(true);
                    },
                  },
                  React.createElement(icons_1.EditIcon, null),
                ),
              ),
          ),
        );
      }
      var handleEditName = function (event) {
        event.preventDefault();
        var shouldNotEdit = validators_1.validateWorkflowName(name) || name === initialName;
        if (shouldNotEdit) {
          setWorkflowEdit(__assign(__assign({}, workflowEditData), { name: initialName }));
          setIsEditWorkflowName(false);
          return;
        }
        _this.handleEditProcess({ name: name });
      };
      return React.createElement(
        'form',
        { className: WorkflowModal_css_1['default']['popup-title-form'], onSubmit: handleEditName },
        React.createElement(Loader_1.Loader, { isLoading: isWorkflowNameSaving }),
        isUrgent
          ? React.createElement(
              'div',
              { className: WorkflowModal_css_1['default']['popup-title_urgent'] },
              React.createElement(IntlMessages_1.IntlMessages, { id: 'workflows.card-urgent' }),
            )
          : null,
        React.createElement(react_textarea_autosize_1['default'], {
          translate: undefined,
          autoFocus: true,
          onBlur: handleEditName,
          value: name,
          onChange: function (e) {
            return setWorkflowEdit(__assign(__assign({}, workflowEditData), { name: e.target.value }));
          },
          className: classnames_1['default'](
            WorkflowModal_css_1['default']['popup-title-form__input'],
            isUrgent && WorkflowModal_css_1['default']['popup-title-form__input_urgent'],
          ),
        }),
      );
    };
    _this.renderKickoff = function () {
      if (!_this.props.workflow) {
        return null;
      }
      var _a = _this.props,
        initialKickoff = _a.workflow.kickoff,
        _b = _a.workflowEdit,
        isKickoffEditing = _b.isKickoffEditing,
        isKickoffSaving = _b.isKickoffSaving,
        editKickoff = _b.workflow.kickoff,
        workflowEditData = _b.workflow,
        setIsEditKickoff = _a.setIsEditKickoff,
        setWorkflowEdit = _a.setWorkflowEdit,
        canEdit = _a.canEdit;
      if (!initialKickoff || !editKickoff) {
        return null;
      }
      var initialEditKickoff = workflows_1.getEditKickoff(initialKickoff);
      if (!isKickoffEditing) {
        return React.createElement(KickoffOutputs_1.KickoffOutputs, {
          viewMode: KickoffOutputs_1.EKickoffOutputsViewModes.Detailed,
          containerClassName: 'mt-3',
          description: initialKickoff === null || initialKickoff === void 0 ? void 0 : initialKickoff.description,
          outputs: initialKickoff === null || initialKickoff === void 0 ? void 0 : initialKickoff.output,
          onEdit: canEdit
            ? function () {
                return setIsEditKickoff(true);
              }
            : undefined,
        });
      }
      var handleEditField = function (apiName) {
        return function (changedProps) {
          var newKickoffFields = getEditedFields_1.getEditedFields(editKickoff.fields, apiName, changedProps);
          var newKickoff = __assign(__assign({}, editKickoff), { fields: newKickoffFields });
          setWorkflowEdit(__assign(__assign({}, workflowEditData), { kickoff: newKickoff }));
        };
      };
      var handleCancel = function () {
        setWorkflowEdit(__assign(__assign({}, workflowEditData), { kickoff: initialEditKickoff }));
        setIsEditKickoff(false);
      };
      return React.createElement(
        'div',
        { className: WorkflowModal_css_1['default']['kickoff-edit'] },
        React.createElement(KickoffEdit_1.EditKickoffContainer, {
          isLoading: isKickoffSaving,
          kickoff: editKickoff,
          onEditField: handleEditField,
          onSave: function () {
            return _this.handleEditProcess({ kickoff: editKickoff });
          },
          onCancel: handleCancel,
        }),
      );
    };
    _this.handleEditProcess = function (_a) {
      var name = _a.name,
        kickoff = _a.kickoff;
      var _b = _this.props,
        workflowId = _b.workflowId,
        editWorkflow = _b.editWorkflow;
      editWorkflow({ name: name, kickoff: kickoff, workflowId: workflowId });
    };
    _this.closeModal = function () {
      var _a = _this.props,
        toggleModal = _a.toggleModal,
        onClose = _a.onClose;
      toggleModal();
      onClose === null || onClose === void 0 ? void 0 : onClose();
    };
    _this.renderContent = function () {
      var _a;
      var _b = _this.props,
        sorting = _b.sorting,
        isCommentsShown = _b.isCommentsShown,
        isOnlyAttachmentsShown = _b.isOnlyAttachmentsShown,
        workflow = _b.workflow,
        items = _b.items,
        workflowId = _b.workflowId,
        isLoading = _b.isLoading,
        changeWorkflowLogViewSettings = _b.changeWorkflowLogViewSettings,
        sendWorkflowLogComments = _b.sendWorkflowLogComments;
      if (isLoading) {
        return React.createElement(
          'div',
          {
            className: classnames_1['default']('w-100', WorkflowModal_css_1['default']['popup-header']),
            onClick: _this.closeModal,
          },
          React.createElement(Loader_1.Loader, { isLoading: true }),
        );
      }
      if (!workflow) {
        return null;
      }
      return React.createElement(
        React.Fragment,
        null,
        React.createElement(
          'div',
          { className: classnames_1['default'](WorkflowModal_css_1['default']['popup-header']) },
          React.createElement(icons_1.ModalCloseIcon, {
            onClick: _this.closeModal,
            className: WorkflowModal_css_1['default']['close-icon'],
          }),
          React.createElement(
            'div',
            { className: WorkflowModal_css_1['default']['header-popup-body'] },
            React.createElement(
              'div',
              { className: WorkflowModal_css_1['default']['popup-general-info-container'] },
              React.createElement(
                'div',
                { className: WorkflowModal_css_1['default']['popup-general-info'] },
                React.createElement(
                  'div',
                  { className: WorkflowModal_css_1['default']['popup-title-container'] },
                  React.createElement(
                    'div',
                    { className: WorkflowModal_css_1['default']['popup-pretitle'] },
                    React.createElement(TemplateName_1.TemplateName, {
                      isLegacyTemplate: workflow.isLegacyTemplate,
                      legacyTemplateName: workflow.legacyTemplateName,
                      templateName: (_a = workflow.template) === null || _a === void 0 ? void 0 : _a.name,
                    }),
                  ),
                  _this.renderWorkflowName(),
                  _this.renderWorkflowInfo(),
                  _this.renderDescription(),
                ),
              ),
              _this.renderKickoff(),
              _this.renderWorkflowAsideInfo({ isMobile: true }),
            ),
            _this.renderWorkflowAsideInfo({ isMobile: false }),
          ),
        ),
        React.createElement(
          reactstrap_1.ModalBody,
          { className: classnames_1['default'](WorkflowModal_css_1['default']['popup-body']) },
          React.createElement(WorkflowLog_1.WorkflowLog, {
            theme: 'white',
            items: items,
            sorting: sorting,
            isCommentsShown: isCommentsShown,
            isOnlyAttachmentsShown: isOnlyAttachmentsShown,
            workflowId: workflowId,
            changeWorkflowLogViewSettings: changeWorkflowLogViewSettings,
            includeHeader: true,
            sendComment: sendWorkflowLogComments,
            workflowStatus: workflow.status,
            onClickTask: _this.closeModal,
            currentTask: workflow.currentTask,
            areTasksClickable: true,
          }),
        ),
      );
    };
    _this.renderDescription = function () {
      var _a;
      var workflowDescription = (_a = _this.props.workflow) === null || _a === void 0 ? void 0 : _a.description;
      if (workflowDescription) {
        return React.createElement(
          'div',
          { className: WorkflowModal_css_1['default']['popup-description'] },
          workflowDescription,
        );
      }
      return null;
    };
    _this.renderWorkflowInfo = function () {
      var _a = _this.props,
        workflow = _a.workflow,
        editWorkflow = _a.editWorkflow,
        timezone = _a.timezone,
        dateFmt = _a.dateFmt;
      if (!workflow) return null;
      return React.createElement(
        'div',
        { className: WorkflowModal_css_1['default']['workflow-info'] },
        React.createElement(
          UserData_1.UserData,
          { userId: workflow === null || workflow === void 0 ? void 0 : workflow.workflowStarter },
          function (user) {
            if (!user) {
              return null;
            }
            var userData =
              workflow && workflow.isExternal
                ? {
                    status: 'external' /* External */,
                    email: '',
                    firstName: 'External User',
                    lastName: '',
                    photo: '',
                  }
                : user;
            return React.createElement(
              'div',
              { className: WorkflowModal_css_1['default']['workflow-starter'] },
              React.createElement(Avatar_1.Avatar, {
                user: userData,
                containerClassName: WorkflowModal_css_1['default']['workflow-starter__avatar'],
                showInitials: false,
                size: 'sm',
              }),
              React.createElement(
                'span',
                { className: WorkflowModal_css_1['default']['workflow-starter__name'] },
                users_1.getUserFullName(userData),
              ),
            );
          },
        ),
        React.createElement(
          'p',
          { className: WorkflowModal_css_1['default']['workflow-date-started'] },
          React.createElement(IntlMessages_1.IntlMessages, {
            id: 'workflows.card-started',
            values: {
              date: React.createElement(
                'span',
                { className: WorkflowModal_css_1['default']['workflow-date-started__date'] },
                React.createElement(DateFormat_1.DateFormat, { date: workflow.dateCreated }),
              ),
            },
          }),
        ),
        React.createElement(
          'div',
          { className: WorkflowModal_css_1['default']['workflow-due-date'] },
          React.createElement(DueIn_1.DueIn, {
            dateFmt: dateFmt,
            timezone: timezone,
            dueDate: workflow.dueDate,
            view: 'dueDate',
            onSave: function (date) {
              return editWorkflow({ workflowId: workflow.id, dueDate: date });
            },
            onRemove: function () {
              return editWorkflow({ workflowId: workflow.id, dueDate: null });
            },
          }),
        ),
      );
    };
    _this.processProgress = _this.calculateWorkflowProgress();
    return _this;
  }
  WorkflowModal.prototype.componentDidMount = function () {
    if (!this.props.workflow) {
      return;
    }
    var _a = this.props,
      _b = _a.workflow,
      name = _b.name,
      kickoff = _b.kickoff,
      setWorkflowEdit = _a.setWorkflowEdit;
    var editWorkflow = { name: name, kickoff: workflows_1.getEditKickoff(kickoff) };
    setWorkflowEdit(editWorkflow);
  };
  WorkflowModal.prototype.componentDidUpdate = function (prevProps) {
    var _a, _b;
    if (!this.props.workflow) {
      return;
    }
    if (
      ((_a = prevProps.workflow) === null || _a === void 0 ? void 0 : _a.kickoff.id) !==
      ((_b = this.props.workflow) === null || _b === void 0 ? void 0 : _b.kickoff.id)
    ) {
      var _c = this.props,
        _d = _c.workflow,
        name = _d.name,
        kickoff = _d.kickoff,
        setWorkflowEdit = _c.setWorkflowEdit;
      var editProcess = { name: name, kickoff: workflows_1.getEditKickoff(kickoff) };
      setWorkflowEdit(editProcess);
    }
    this.processProgress = this.calculateWorkflowProgress();
  };
  WorkflowModal.prototype.render = function () {
    var _a = this.props,
      isOpen = _a.isOpen,
      isRunWorkflowOpen = _a.isRunWorkflowOpen,
      isFullscreenImageOpen = _a.isFullscreenImageOpen;
    return React.createElement(
      'div',
      { className: WorkflowModal_css_1['default']['popup'] },
      React.createElement(
        reactstrap_1.Modal,
        {
          isOpen: isOpen,
          toggle: this.closeModal,
          backdrop: 'static',
          wrapClassName: classnames_1['default'](
            'processes-workflows-popup',
            'processes-inwork-popup',
            WorkflowModal_css_1['default']['inwork-popup'],
          ),
          className: WorkflowModal_css_1['default']['inwork-popup-dialog'],
          contentClassName: classnames_1['default'](WorkflowModal_css_1['default']['inwork-popup-content']),
        },
        React.createElement(
          react_outside_click_handler_1['default'],
          { disabled: isRunWorkflowOpen || isFullscreenImageOpen, onOutsideClick: this.closeModal },
          this.renderContent(),
        ),
      ),
    );
  };
  return WorkflowModal;
})(React.Component);
exports.WorkflowModal = WorkflowModal;
