"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
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
exports.__esModule = true;
exports.PublicForm = void 0;
/* eslint-disable */
/* prettier-ignore */
var React = require("react");
var react_intl_1 = require("react-intl");
var react_google_recaptcha_1 = require("react-google-recaptcha");
var immer_1 = require("immer");
var classnames_1 = require("classnames");
var react_redux_1 = require("react-redux");
var Notifications_1 = require("../../../UI/Notifications");
var ExtraFields_1 = require("../../../TemplateEdit/ExtraFields");
var template_1 = require("../../../../types/template");
var Button_1 = require("../../../UI/Buttons/Button");
var getEditedFields_1 = require("../../../TemplateEdit/ExtraFields/utils/getEditedFields");
var workflow_1 = require("../../../../types/workflow");
var getPublicForm_1 = require("../../../../api/getPublicForm");
var types_1 = require("../types");
var logger_1 = require("../../../../utils/logger");
var runPublicForm_1 = require("../../../../api/runPublicForm");
var areKickoffFieldsValid_1 = require("../../../WorkflowEditPopup/utils/areKickoffFieldsValid");
var ExtraFieldsHelper_1 = require("../../../TemplateEdit/ExtraFields/utils/ExtraFieldsHelper");
var mappers_1 = require("../../../../utils/mappers");
var Header_1 = require("../../../UI/Typeography/Header");
var getConfig_1 = require("../../../../utils/getConfig");
var deleteRemovedFilesFromFields_1 = require("../../../../api/deleteRemovedFilesFromFields");
var RichText_1 = require("../../../RichText");
var actions_1 = require("../../../../redux/actions");
var Copyright_1 = require("../Copyright");
var FormSkeleton_1 = require("../FormSkeleton");
var useShouldHideIntercom_1 = require("../../../../hooks/useShouldHideIntercom");
var prependHttp_1 = require("../../../../utils/prependHttp");
var SubmitedImage_svg_1 = require("../images/SubmitedImage.svg");
var ErrorImage = require("../images/ErrorImage.svg");
var PublicForm_css_1 = require("./PublicForm.css");
require("../../../../assets/fonts/simple-line-icons/css/simple-line-icons.css");
require("../../../../assets/fonts/iconsmind-s/css/iconsminds.css");
require("../../../../assets/css/vendor/bootstrap.min.css");
require("../../../../assets/css/sass/themes/gogo.light.yellow.scss");
require("react-perfect-scrollbar/dist/css/styles.css");
require("rc-switch/assets/index.css");
var enviroment_1 = require("../../../../constants/enviroment");
function PublicForm(_a) {
    var _this = this;
    var type = _a.type;
    var formatMessage = react_intl_1.useIntl().formatMessage;
    var dispatch = react_redux_1.useDispatch();
    var _b = React.useState(types_1.EPublicFormState.WaitingForAction), formState = _b[0], setFormState = _b[1];
    var _c = React.useState(null), publicForm = _c[0], setPublicForm = _c[1];
    var _d = React.useState(''), captcha = _d[0], setCaptcha = _d[1];
    useShouldHideIntercom_1.useShouldHideIntercom();
    React.useEffect(function () {
        dispatch(actions_1.usersFetchStarted({ showErrorNotification: false }));
        fetchPublicForm();
    }, []);
    var fetchPublicForm = function () { return __awaiter(_this, void 0, void 0, function () {
        var publicForm_1, normalizedForm, error_1;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    _a.trys.push([0, 2, , 3]);
                    setFormState(types_1.EPublicFormState.Loading);
                    return [4 /*yield*/, getPublicForm_1.getPublicForm()];
                case 1:
                    publicForm_1 = _a.sent();
                    if (!publicForm_1) {
                        setFormState(types_1.EPublicFormState.FormNotFound);
                        return [2 /*return*/];
                    }
                    normalizedForm = immer_1["default"](publicForm_1, function (draftPublicForm) {
                        draftPublicForm.kickoff.fields = new ExtraFieldsHelper_1.ExtraFieldsHelper(publicForm_1.kickoff.fields).getFieldsWithValues();
                    });
                    setPublicForm(normalizedForm);
                    setFormState(types_1.EPublicFormState.WaitingForAction);
                    return [3 /*break*/, 3];
                case 2:
                    error_1 = _a.sent();
                    setFormState(types_1.EPublicFormState.FormNotFound);
                    logger_1.logger.error('Failed to fetch public form.');
                    return [3 /*break*/, 3];
                case 3: return [2 /*return*/];
            }
        });
    }); };
    var handleRunPublicForm = function () { return __awaiter(_this, void 0, void 0, function () {
        var normalizedKickoffFileds, runFormResult, error_2;
        return __generator(this, function (_a) {
            switch (_a.label) {
                case 0:
                    if (!publicForm)
                        return [2 /*return*/];
                    _a.label = 1;
                case 1:
                    _a.trys.push([1, 4, , 5]);
                    setFormState(types_1.EPublicFormState.Submitting);
                    return [4 /*yield*/, deleteRemovedFilesFromFields_1.deleteRemovedFilesFromFields(publicForm.kickoff.fields)];
                case 2:
                    _a.sent();
                    normalizedKickoffFileds = mappers_1.getNormalizedKickoff(publicForm.kickoff);
                    return [4 /*yield*/, runPublicForm_1.runPublicForm(captcha, normalizedKickoffFileds)];
                case 3:
                    runFormResult = _a.sent();
                    if (runFormResult === null || runFormResult === void 0 ? void 0 : runFormResult.redirectUrl) {
                        window.location.replace(prependHttp_1.prependHttp(runFormResult === null || runFormResult === void 0 ? void 0 : runFormResult.redirectUrl));
                        return [2 /*return*/];
                    }
                    setFormState(types_1.EPublicFormState.Submitted);
                    return [3 /*break*/, 5];
                case 4:
                    error_2 = _a.sent();
                    Notifications_1.NotificationManager.error({ message: 'public-form.submit-failed' });
                    logger_1.logger.error('Failed to run public form', error_2);
                    setFormState(types_1.EPublicFormState.WaitingForAction);
                    return [3 /*break*/, 5];
                case 5: return [2 /*return*/];
            }
        });
    }); };
    var handleEditField = function (apiName) { return function (changedProps) {
        setPublicForm(function (prevPublicForm) {
            if (!prevPublicForm) {
                return prevPublicForm;
            }
            var oldFields = prevPublicForm.kickoff.fields;
            var newFields = getEditedFields_1.getEditedFields(oldFields, apiName, changedProps);
            var newPublicForm = immer_1["default"](prevPublicForm, function (draftPublicForm) {
                if (draftPublicForm) {
                    draftPublicForm.kickoff.fields = newFields;
                }
            });
            return newPublicForm;
        });
    }; };
    var renderOutputFields = function () {
        if (!publicForm) {
            return null;
        }
        var reсaptchaSecret = getConfig_1.getPublicFormConfig().config.reсaptchaSecret;
        return (React.createElement(React.Fragment, null,
            publicForm.kickoff.fields.map(function (field) { return (React.createElement(ExtraFields_1.ExtraFieldIntl, { key: field.apiName, field: field, editField: handleEditField(field.apiName), showDropdown: false, mode: template_1.EExtraFieldMode.ProcessRun, labelBackgroundColor: workflow_1.EInputNameBackgroundColor.OrchidWhite, namePlaceholder: field.name, descriptionPlaceholder: field.description, wrapperClassName: PublicForm_css_1["default"]['output__field'], accountId: publicForm.accountId })); }),
            enviroment_1.isEnvCaptcha && (publicForm === null || publicForm === void 0 ? void 0 : publicForm.showCaptcha) && (React.createElement("div", { className: PublicForm_css_1["default"]['captcha'] },
                React.createElement(react_google_recaptcha_1["default"], { sitekey: reсaptchaSecret, onChange: function (token) { return token && setCaptcha(token); }, theme: "light" })))));
    };
    if (formState === types_1.EPublicFormState.Loading) {
        return React.createElement(FormSkeleton_1.FormSkeleton, null);
    }
    if (formState === types_1.EPublicFormState.Submitted) {
        return (React.createElement("div", { className: classnames_1["default"](PublicForm_css_1["default"]['notification'], type === 'embedded' && PublicForm_css_1["default"]['embedded']) },
            type !== 'embedded' && (React.createElement("img", { className: PublicForm_css_1["default"]['notification__image'], src: SubmitedImage_svg_1["default"], alt: formatMessage({ id: 'public-form.submited-title' }) })),
            React.createElement(Header_1.Header, { className: PublicForm_css_1["default"]['notification__title'], size: "2", tag: "h1" }, formatMessage({ id: 'public-form.submited-title' })),
            React.createElement("p", { className: PublicForm_css_1["default"]['notification__text'] }, formatMessage({ id: 'public-form.submited-text' })),
            React.createElement(Button_1.Button, { size: "md", buttonStyle: "yellow", label: formatMessage({ id: 'public-form.submited-button' }), onClick: fetchPublicForm }),
            type === 'embedded' && React.createElement(Copyright_1.Copyright, { className: PublicForm_css_1["default"]['copyright'] })));
    }
    if (formState === types_1.EPublicFormState.FormNotFound) {
        return (React.createElement("div", { className: classnames_1["default"](PublicForm_css_1["default"]['notification'], type === 'embedded' && PublicForm_css_1["default"]['embedded']) },
            type !== 'embedded' && (React.createElement("img", { className: PublicForm_css_1["default"]['notification__image'], src: ErrorImage, alt: formatMessage({ id: 'public-form.error-title' }) })),
            React.createElement(Header_1.Header, { className: PublicForm_css_1["default"]['notification__title'], size: "2", tag: "h1" }, formatMessage({ id: 'public-form.error-title' })),
            React.createElement("p", { className: PublicForm_css_1["default"]['notification__text'] }, formatMessage({ id: 'public-form.error-text' })),
            type === 'embedded' && React.createElement(Copyright_1.Copyright, { className: PublicForm_css_1["default"]['copyright'] })));
    }
    if (!publicForm) {
        return null;
    }
    var isCompleteDisabled = [
        formState !== types_1.EPublicFormState.WaitingForAction,
        !areKickoffFieldsValid_1.checkExtraFieldsAreValid(publicForm === null || publicForm === void 0 ? void 0 : publicForm.kickoff.fields),
        (publicForm === null || publicForm === void 0 ? void 0 : publicForm.showCaptcha) && !captcha,
    ].some(Boolean);
    var classNamesByTypeMap = {
        shared: PublicForm_css_1["default"]['shared'],
        embedded: PublicForm_css_1["default"]['embedded']
    };
    return (React.createElement("div", { className: classnames_1["default"](PublicForm_css_1["default"]['kikcoff-form'], classNamesByTypeMap[type]) },
        React.createElement(Header_1.Header, { className: PublicForm_css_1["default"]['name'], size: "4", tag: "h1" }, publicForm.name),
        React.createElement("p", { className: PublicForm_css_1["default"]['description'] }, publicForm.kickoff.description ? (React.createElement(RichText_1.RichText, { text: publicForm.kickoff.description })) : (formatMessage({ id: 'public-form.form-hint' }))),
        React.createElement("div", { className: classnames_1["default"](PublicForm_css_1["default"]['kikcoff-form__inner'], classNamesByTypeMap[type]) },
            renderOutputFields(),
            React.createElement(Button_1.Button, { disabled: isCompleteDisabled, isLoading: formState === types_1.EPublicFormState.Submitting, onClick: handleRunPublicForm, label: formatMessage({ id: 'public-form.launch' }), size: "md", buttonStyle: "yellow", className: PublicForm_css_1["default"]['submit-button'] }),
            type === 'embedded' && React.createElement(Copyright_1.Copyright, { className: PublicForm_css_1["default"]['copyright'] }))));
}
exports.PublicForm = PublicForm;
