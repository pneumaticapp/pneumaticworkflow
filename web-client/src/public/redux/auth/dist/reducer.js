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
exports.reducer = exports.INIT_STATE = void 0;
/* eslint-disable no-param-reassign */
var immer_1 = require("immer");
var moment_timezone_1 = require("moment-timezone");
var getConfig_1 = require("../../utils/getConfig");
var redux_1 = require("../../types/redux");
var cookie_1 = require("../../utils/cookie");
var actions_1 = require("./actions");
var account_1 = require("../../types/account");
var _a = getConfig_1.getBrowserConfig(), googleAuthUserInfo = _a.googleAuthUserInfo, invitedUser = _a.invitedUser;
var EMPTY_USER = {
    email: '',
    account: {
        id: undefined,
        name: '',
        isVerified: false,
        tenantName: '',
        billingPlan: account_1.ESubscriptionPlan.Unknown,
        plan: account_1.ESubscriptionPlan.Unknown,
        planExpiration: null,
        leaseLevel: 'standard',
        logoSm: null,
        logoLg: null,
        paymentCardProvided: true,
        trialEnded: false,
        trialIsActive: false,
        isSubscribed: false
    },
    id: -1,
    isAdmin: false,
    firstName: '',
    lastName: '',
    token: cookie_1.parseCookies(document.cookie).token || '',
    phone: '',
    photo: '',
    loading: false,
    status: "active" /* Active */,
    googleAuthUserInfo: googleAuthUserInfo,
    invitedUser: invitedUser,
    isAccountOwner: true,
    isDigestSubscriber: false,
    isTasksDigestSubscriber: false,
    isCommentsMentionsSubscriber: false,
    isNewTasksSubscriber: false,
    isNewslettersSubscriber: false,
    isSpecialOffersSubscriber: false,
    type: 'user',
    loggedState: cookie_1.parseCookies(document.cookie)['token'] ? redux_1.ELoggedState.LoggedIn : redux_1.ELoggedState.LoggedOut,
    language: '',
    timezone: moment_timezone_1["default"].tz.guess(),
    dateFmt: '',
    dateFdw: ''
};
exports.INIT_STATE = __assign(__assign({}, EMPTY_USER), getConfig_1.getBrowserConfig().user);
// eslint-disable-next-line @typescript-eslint/default-param-last
exports.reducer = function (state, action) {
    if (state === void 0) { state = exports.INIT_STATE; }
    switch (action.type) {
        case "AUTH_USER" /* AuthUser */:
            return __assign(__assign({}, state), { loading: true });
        case "AUTH_USER_SUCCESS" /* AuthUserSuccess */:
            return __assign(__assign(__assign({}, state), { loading: false, loggedState: redux_1.ELoggedState.LoggedIn }), action.payload);
        case "CHANGE_PASSWORD_SUCCESS" /* ChangePasswordSuccess */:
        case "EDIT_USER_SUCCESS" /* EditUserSuccess */:
        case "REGISTER_USER_SUCCESS" /* RegisterUserSuccess */:
        case "RESET_PASSWORD_SUCCESS" /* ResetPasswordSuccess */:
            return __assign(__assign(__assign({}, state), { loading: false }), action.payload);
        case "EDIT_ACCOUNT_SUCCESS" /* EditAccountSuccess */:
            return __assign(__assign({}, state), { loading: false, account: __assign(__assign({}, state.account), action.payload) });
        case "CHANGE_PASSWORD" /* ChangePassword */:
        case "EDIT_USER" /* EditUser */:
        case "EDIT_ACCOUNT" /* EditAccount */:
        case "LOGIN_USER" /* LoginUser */:
        case "LOGIN_SUPERUSER" /* LoginSuperuser */:
        case "REGISTER_USER" /* RegisterUser */:
        case "REGISTER_USER_INVITED" /* RegisterUserInvited */:
        case "FORGOT_PASSWORD" /* ForgotPassword */:
        case "RESET_PASSWORD" /* ResetPassword */:
            return __assign(__assign({}, state), { loading: true });
        case "FORGOT_PASSWORD_SUCCESS" /* ForgotPasswordSuccess */:
        case "EDIT_FAILED" /* EditFailed */:
            return __assign(__assign({}, state), { loading: false });
        case "AUTH_USER_FAIL" /* AuthUserFail */:
            return immer_1["default"](state, function (draftState) {
                var _a;
                draftState.error = (_a = action.payload) !== null && _a !== void 0 ? _a : actions_1.EAuthUserFailType.Common;
                draftState.loading = false;
            });
        case "FORGOT_PASSWORD_FAIL" /* ForgotPasswordFail */:
        case "RESET_PASSWORD_FAIL" /* ResetPasswordFail */:
        case "CHANGE_PASSWORD_FAIL" /* ChangePasswordFail */:
            return __assign(__assign({}, state), { error: actions_1.EAuthUserFailType.Common, loading: false });
        case "REMOVE_GOOGLE_USER" /* RemoveGoogleUser */:
            return __assign(__assign({}, state), { googleAuthUserInfo: {} });
        case "SET_USER_TOKEN" /* SetToken */:
            return __assign(__assign({}, state), { token: action.payload });
        case "SET_USER_PHOTO" /* SetUserPhoto */:
            return __assign(__assign({}, state), { photo: action.payload });
        case "LOGOUT_USER_SUCCESS" /* LogoutUserSuccess */: {
            return __assign(__assign({}, state), { loggedState: redux_1.ELoggedState.LoggedOut });
        }
        case "SET_CURRENT_PLAN" /* SetCurrentPlan */: {
            var _a = action.payload, billingPlan_1 = _a.billingPlan, planExpiration_1 = _a.planExpiration;
            return immer_1["default"](state, function (draftState) {
                draftState.account.billingPlan = billingPlan_1;
                draftState.account.planExpiration = planExpiration_1;
            });
        }
        default:
            return __assign({}, state);
    }
};
