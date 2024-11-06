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
var __rest = (this && this.__rest) || function (s, e) {
    var t = {};
    for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p) && e.indexOf(p) < 0)
        t[p] = s[p];
    if (s != null && typeof Object.getOwnPropertySymbols === "function")
        for (var i = 0, p = Object.getOwnPropertySymbols(s); i < p.length; i++) {
            if (e.indexOf(p[i]) < 0 && Object.prototype.propertyIsEnumerable.call(s, p[i]))
                t[p[i]] = s[p[i]];
        }
    return t;
};
exports.__esModule = true;
exports.Profile = void 0;
var react_1 = require("react");
var react_intl_1 = require("react-intl");
var formik_1 = require("formik");
var profile_1 = require("../../constants/profile");
var InputField_1 = require("../UI/Fields/InputField");
var Button_1 = require("../UI/Buttons/Button");
var profile_2 = require("../../types/profile");
var titles_1 = require("../../constants/titles");
var validators_1 = require("../../utils/validators");
var getErrorsObject_1 = require("../../utils/formik/getErrorsObject");
var Header_1 = require("../UI/Typeography/Header");
var SectionTitle_1 = require("../UI/Typeography/SectionTitle");
var Checkbox_1 = require("../UI/Fields/Checkbox");
var AvatarController_1 = require("./AvatarController");
var UI_1 = require("../UI");
var validators_2 = require("./validators");
var Profile_css_1 = require("./Profile.css");
function Profile(_a) {
    var user = _a.user, editCurrentUser = _a.editCurrentUser, sendChangePassword = _a.sendChangePassword, onChangeTab = _a.onChangeTab;
    var formatMessage = react_intl_1.useIntl().formatMessage;
    var id = user.id, email = user.email, firstName = user.firstName, lastName = user.lastName, phone = user.phone, loading = user.loading, isDigestSubscriber = user.isDigestSubscriber, isTasksDigestSubscriber = user.isTasksDigestSubscriber, isCommentsMentionsSubscriber = user.isCommentsMentionsSubscriber, isNewTasksSubscriber = user.isNewTasksSubscriber, isNewslettersSubscriber = user.isNewslettersSubscriber, isSpecialOffersSubscriber = user.isSpecialOffersSubscriber, language = user.language, timezone = user.timezone, dateFdw = user.dateFdw, dateFmt = user.dateFmt;
    if (!id)
        return react_1["default"].createElement("div", { className: "loading" });
    var initialValues = {
        firstName: firstName,
        lastName: lastName,
        phone: phone,
        isDigestSubscriber: isDigestSubscriber,
        isTasksDigestSubscriber: isTasksDigestSubscriber,
        isCommentsMentionsSubscriber: isCommentsMentionsSubscriber,
        isNewTasksSubscriber: isNewTasksSubscriber,
        isNewslettersSubscriber: isNewslettersSubscriber,
        isSpecialOffersSubscriber: isSpecialOffersSubscriber,
        confirmNewPassword: '',
        newPassword: '',
        oldPassword: '',
        language: language,
        timezone: timezone,
        dateFdw: String(dateFdw),
        timeformat: dateFmt.split(',')[2].trim(),
        dateformat: dateFmt.split(',')[0] + "," + dateFmt.split(',')[1] + ","
    };
    react_1.useEffect(function () {
        document.title = titles_1.TITLES.Profile;
    }, []);
    react_1.useLayoutEffect(function () {
        onChangeTab(profile_2.ESettingsTabs.Profile);
    }, []);
    var handleSubmit = function (values) {
        var oldPassword = values.oldPassword, newPassword = values.newPassword, confirmNewPassword = values.confirmNewPassword, dateformat = values.dateformat, timeformat = values.timeformat, userData = __rest(values, ["oldPassword", "newPassword", "confirmNewPassword", "dateformat", "timeformat"]);
        editCurrentUser(__assign(__assign({}, userData), { dateFmt: dateformat + " " + timeformat }));
        var isPasswordChanged = newPassword && confirmNewPassword && oldPassword;
        if (isPasswordChanged) {
            sendChangePassword({ oldPassword: oldPassword, newPassword: newPassword, confirmNewPassword: confirmNewPassword });
        }
    };
    return (react_1["default"].createElement("div", { className: Profile_css_1["default"]['profile-form'] },
        react_1["default"].createElement(Header_1.Header, { className: Profile_css_1["default"]['header'], size: "4", tag: "h1" }, formatMessage({ id: 'user-info.title' })),
        react_1["default"].createElement(AvatarController_1.AvatarController, { user: user, containerClassname: Profile_css_1["default"]['avatar-controller'] }),
        react_1["default"].createElement(formik_1.Formik, { initialValues: initialValues, onSubmit: handleSubmit, validate: function (values) {
                var errors = getErrorsObject_1.getErrorsObject(values, {
                    firstName: validators_1.validateName,
                    lastName: validators_1.validateName,
                    phone: validators_1.validatePhone
                });
                var oldPassword = values.oldPassword, newPassword = values.newPassword, confirmNewPassword = values.confirmNewPassword;
                var isPasswordChanged = newPassword || confirmNewPassword || oldPassword;
                if (!isPasswordChanged) {
                    return errors;
                }
                var passwordErrors = getErrorsObject_1.getErrorsObject(values, {
                    oldPassword: validators_2.validateOldPassword,
                    newPassword: validators_2.validateNewPassword
                });
                if (oldPassword === newPassword) {
                    passwordErrors.newPassword = 'validation.passwords-are-same';
                }
                if (newPassword !== confirmNewPassword) {
                    passwordErrors.confirmNewPassword = 'validation.passwords-dont-match';
                }
                return __assign(__assign({}, errors), passwordErrors);
            } },
            react_1["default"].createElement(formik_1.Form, { autoComplete: "off" },
                react_1["default"].createElement("div", { className: Profile_css_1["default"]['fields-group'] },
                    react_1["default"].createElement(InputField_1.InputField, { value: id, fieldSize: "lg", title: formatMessage({ id: 'user.id' }), disabled: true, containerClassName: Profile_css_1["default"]['field'] }),
                    react_1["default"].createElement(InputField_1.InputField, { value: email, fieldSize: "lg", title: formatMessage({ id: 'user.email' }), disabled: true, containerClassName: Profile_css_1["default"]['field'], isRequired: true }),
                    react_1["default"].createElement(InputField_1.FormikInputField, { autoComplete: "given-name", name: "firstName", fieldSize: "lg", title: formatMessage({ id: 'user.first-name' }), containerClassName: Profile_css_1["default"]['field'], isRequired: true }),
                    react_1["default"].createElement(InputField_1.FormikInputField, { autoComplete: "family-name", name: "lastName", fieldSize: "lg", title: formatMessage({ id: 'user.last-name' }), containerClassName: Profile_css_1["default"]['field'], isRequired: true }),
                    react_1["default"].createElement(InputField_1.FormikInputField, { autoComplete: "tel", name: "phone", fieldSize: "lg", title: formatMessage({ id: 'user.phone' }), containerClassName: Profile_css_1["default"]['field'] })),
                react_1["default"].createElement("div", { className: Profile_css_1["default"]['fields-group'] },
                    react_1["default"].createElement(SectionTitle_1.SectionTitle, { className: Profile_css_1["default"]['fields-group__title'] }, formatMessage({ id: 'user-info.locale' })),
                    react_1["default"].createElement(UI_1.FormikDropdownList, { className: Profile_css_1["default"]['field'], label: "Language", name: "language", options: profile_1.LANGUAGE_OPTIONS }),
                    react_1["default"].createElement(UI_1.FormikDropdownList, { label: "Timezone", className: Profile_css_1["default"]['field'], name: "timezone", options: profile_1.TIMEZONE_OPTIONS }),
                    react_1["default"].createElement(UI_1.FormikDropdownList, { label: "Timeformat", className: Profile_css_1["default"]['field'], name: "timeformat", options: profile_1.TIMEFORMAT_OPTIONS }),
                    react_1["default"].createElement(UI_1.FormikDropdownList, { label: "Dateformat", className: Profile_css_1["default"]['field'], name: "dateformat", options: profile_1.DATEFORMAT_OPTIONS }),
                    react_1["default"].createElement(UI_1.FormikDropdownList, { label: "First day of the week", className: Profile_css_1["default"]['field'], name: "dateFdw", options: profile_1.FIRST_DAY_OPTIONS })),
                react_1["default"].createElement("div", { className: Profile_css_1["default"]['fields-group'] },
                    react_1["default"].createElement(SectionTitle_1.SectionTitle, { className: Profile_css_1["default"]['fields-group__title'] }, formatMessage({ id: 'user-info.subscriptions' })),
                    react_1["default"].createElement(Checkbox_1.FormikCheckbox, { title: formatMessage({ id: 'user-info.newsletter' }), name: "isNewslettersSubscriber", containerClassName: Profile_css_1["default"]['field'] }),
                    react_1["default"].createElement(Checkbox_1.FormikCheckbox, { title: formatMessage({ id: 'user-info.special-offers' }), name: "isSpecialOffersSubscriber", containerClassName: Profile_css_1["default"]['field'] }),
                    react_1["default"].createElement(Checkbox_1.FormikCheckbox, { title: formatMessage({ id: 'user-info.comments-and-mentions' }), name: "isCommentsMentionsSubscriber", containerClassName: Profile_css_1["default"]['field'] }),
                    react_1["default"].createElement(Checkbox_1.FormikCheckbox, { title: formatMessage({ id: 'user-info.new-tasks' }), name: "isNewTasksSubscriber", containerClassName: Profile_css_1["default"]['field'] }),
                    user.isAdmin && (react_1["default"].createElement(Checkbox_1.FormikCheckbox, { title: formatMessage({ id: 'user-info.digest' }), name: "isDigestSubscriber", containerClassName: Profile_css_1["default"]['field'] })),
                    react_1["default"].createElement(Checkbox_1.FormikCheckbox, { title: formatMessage({ id: 'user-info.tasks-digest' }), name: "isTasksDigestSubscriber", containerClassName: Profile_css_1["default"]['field'] })),
                react_1["default"].createElement("div", { className: Profile_css_1["default"]['fields-group'] },
                    react_1["default"].createElement(SectionTitle_1.SectionTitle, { className: Profile_css_1["default"]['fields-group__title'] }, formatMessage({ id: 'user-info.change-password' })),
                    react_1["default"].createElement(InputField_1.FormikInputField, { autocomplete: "off", type: "password", name: "oldPassword", fieldSize: "lg", title: formatMessage({ id: 'user.old-password' }), containerClassName: Profile_css_1["default"]['field'] }),
                    react_1["default"].createElement(InputField_1.FormikInputField, { autocomplete: "off", type: "password", name: "newPassword", fieldSize: "lg", title: formatMessage({ id: 'user.new-password' }), containerClassName: Profile_css_1["default"]['field'] }),
                    react_1["default"].createElement(InputField_1.FormikInputField, { autocomplete: "off", type: "password", name: "confirmNewPassword", fieldSize: "lg", title: formatMessage({ id: 'user.new-password-again' }), containerClassName: Profile_css_1["default"]['field'] })),
                react_1["default"].createElement(Button_1.Button, { label: formatMessage({ id: 'user-info.change-submit' }), className: Profile_css_1["default"]['submit-button'], isLoading: loading, type: "submit", size: "md", buttonStyle: "yellow" })))));
}
exports.Profile = Profile;
