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
exports.rootSaga = exports.watchRedirectToCustomerPortal = exports.watchOnAfterPaymentDetailsProvided = exports.watchMakeStripePayment = exports.watchChangePaymentDetails = exports.watchCollectPaymentDetails = exports.watchReturnFromSupermode = exports.watchDeleteUserPhoto = exports.watchUploadUserPhoto = exports.watchUserWSEvents = exports.watchSetUserToken = exports.watchSetRedirectUrl = exports.watchResendVerification = exports.watchEditAccount = exports.watchResetPassword = exports.watchForgotPassword = exports.watchChangePassword = exports.watchLogoutUser = exports.watchLoginPartnerSuperuser = exports.watchLoginSuperuser = exports.watchLoginUser = exports.watchRegisterUserInvited = exports.watchRegisterUser = exports.watchEditUser = exports.watchAuthUser = exports.onAfterPaymentDetailsProvidedSaga = exports.makeStripePaymentSaga = exports.changePaymentDetailsSaga = exports.collectPaymentDetailsSaga = exports.handleSetRedirectUrl = exports.handleDeleteUserPhoto = exports.handleUploadUserPhoto = exports.fetchResendVerification = exports.handleSetUserToken = exports.sendPasswordResetConfirm = exports.sendPasswordChange = exports.sendPasswordReset = exports.editCurrentAccount = exports.editCurrentProfile = exports.updateUserAsync = exports.logout = exports.registerWithInvite = exports.registerInviteAsync = exports.registerWithEmailPassword = exports.registerWithEmailAsync = exports.retrunFromSupermodeSaga = exports.loginPartnerSuperuser = exports.loginSuperuser = exports.loginWithEmailPassword = exports.loginWithEmailPasswordAsync = exports.authUserSaga = exports.authenticateUser = void 0;
var effects_1 = require("redux-saga/effects");
var auth_1 = require("../../api/auth");
var actions_1 = require("./actions");
var resendVerification_1 = require("../../api/resendVerification");
var routes_1 = require("../../constants/routes");
var Notifications_1 = require("../../components/common/Notifications");
var authCookie_1 = require("../../utils/authCookie");
var setOAuthRegistrationCompleted_1 = require("../../api/setOAuthRegistrationCompleted");
var user_1 = require("../selectors/user");
var auth_2 = require("../../utils/auth");
var editProfile_1 = require("../../api/editProfile");
var logger_1 = require("../../utils/logger");
var mappers_1 = require("../../utils/mappers");
var resetPassword_1 = require("../../api/resetPassword");
var getErrorMessage_1 = require("../../utils/getErrorMessage");
var resetPasswordSet_1 = require("../../api/resetPasswordSet");
var editAccount_1 = require("../../api/editAccount");
var changePassword_1 = require("../../api/changePassword");
var analytics_1 = require("../../utils/analytics");
var sendSignOut_1 = require("../../api/sendSignOut");
var storageKeys_1 = require("../../constants/storageKeys");
var utmParams_1 = require("../../views/user/utils/utmParams");
var actions_2 = require("../general/actions");
var history_1 = require("../../utils/history");
var saga_1 = require("../tasks/saga");
var saga_2 = require("../notifications/saga");
var uploadFiles_1 = require("../../utils/uploadFiles");
var changePhotoProfile_1 = require("../../api/changePhotoProfile");
var redux_1 = require("../../types/redux");
var firebase_1 = require("../../firebase");
var getTenantToken_1 = require("../../api/tenants/getTenantToken");
var superuserToken_1 = require("./utils/superuserToken");
var superuserReturnRoute_1 = require("./utils/superuserReturnRoute");
var makePayment_1 = require("../../api/makePayment");
var saga_3 = require("../accounts/saga");
var getAbsolutePath_1 = require("../../utils/getAbsolutePath");
var cardSetup_1 = require("../../api/cardSetup");
var confirmPaymentDetailsProvided_1 = require("./utils/confirmPaymentDetailsProvided");
var createAITemplate_1 = require("./utils/createAITemplate");
var trackCrozdesk_1 = require("../../utils/analytics/trackCrozdesk");
var getConfig_1 = require("../../utils/getConfig");
var getCustomerPortalLink_1 = require("../../api/getCustomerPortalLink");
var createTemplateFromName_1 = require("./utils/createTemplateFromName");
var saga_4 = require("../workflows/saga");
var localStorage_1 = require("../../utils/localStorage");
var enviroment_1 = require("../../constants/enviroment");
function authenticateUser(redirectUrl) {
    var user, err_1;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                _a.trys.push([0, 6, , 9]);
                return [4 /*yield*/, effects_1.call(auth_1.auth.getUser)];
            case 1:
                user = _a.sent();
                return [4 /*yield*/, effects_1.put(actions_1.authUserSuccess(user))];
            case 2:
                _a.sent();
                if (!(enviroment_1.isEnvBilling && !user.account.paymentCardProvided)) return [3 /*break*/, 5];
                if (!user.account.isSubscribed) return [3 /*break*/, 4];
                return [4 /*yield*/, effects_1.call(changePaymentDetailsSaga)];
            case 3:
                _a.sent();
                return [2 /*return*/];
            case 4:
                history_1.history.push(routes_1.ERoutes.CollectPaymentDetails);
                return [2 /*return*/];
            case 5:
                if (redirectUrl) {
                    history_1.history.replace(redirectUrl);
                }
                return [3 /*break*/, 9];
            case 6:
                err_1 = _a.sent();
                logger_1.logger.error(err_1);
                return [4 /*yield*/, effects_1.put(actions_1.redirectToLogin())];
            case 7:
                _a.sent();
                return [4 /*yield*/, effects_1.put(actions_1.authUserFail())];
            case 8:
                _a.sent();
                return [3 /*break*/, 9];
            case 9: return [2 /*return*/];
        }
    });
}
exports.authenticateUser = authenticateUser;
function authUserSaga() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, authenticateUser()];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.authUserSaga = authUserSaga;
exports.loginWithEmailPasswordAsync = function (email, password) {
    return auth_1.auth
        .signInWithEmailAndPassword(email, password)
        .then(function (authUser) { return authUser; })["catch"](function (error) { return error; });
};
function loginWithEmailPassword(_a) {
    var email, password, rememberMe, loginUser, err, isVerificationError, error_1;
    var payload = _a.payload;
    return __generator(this, function (_b) {
        switch (_b.label) {
            case 0:
                email = payload.email, password = payload.password, rememberMe = payload.rememberMe;
                _b.label = 1;
            case 1:
                _b.trys.push([1, 9, , 11]);
                return [4 /*yield*/, effects_1.call(exports.loginWithEmailPasswordAsync, email, password)];
            case 2:
                loginUser = _b.sent();
                if (!!loginUser.message) return [3 /*break*/, 4];
                authCookie_1.setJwtCookie(loginUser.token, rememberMe);
                return [4 /*yield*/, authenticateUser(loginUser.isAccountOwner ? routes_1.ERoutes.Main : routes_1.ERoutes.Tasks)];
            case 3:
                _b.sent();
                return [2 /*return*/];
            case 4:
                err = getErrorMessage_1.getErrorMessage(loginUser);
                isVerificationError = err.includes('Your account has not been verified');
                if (!isVerificationError) return [3 /*break*/, 6];
                Notifications_1.NotificationManager.error({ title: 'Login failed', message: err });
                return [4 /*yield*/, effects_1.put(actions_1.authUserFail(actions_1.EAuthUserFailType.NotVerified))];
            case 5:
                _b.sent();
                return [3 /*break*/, 8];
            case 6: return [4 /*yield*/, effects_1.put(actions_1.authUserFail(actions_1.EAuthUserFailType.Common))];
            case 7:
                _b.sent();
                _b.label = 8;
            case 8: return [3 /*break*/, 11];
            case 9:
                error_1 = _b.sent();
                return [4 /*yield*/, effects_1.put(actions_1.authUserFail(actions_1.EAuthUserFailType.Common))];
            case 10:
                _b.sent();
                return [3 /*break*/, 11];
            case 11: return [2 /*return*/];
        }
    });
}
exports.loginWithEmailPassword = loginWithEmailPassword;
function loginSuperuser(_a) {
    var email, loginUser, error_2;
    var payload = _a.payload;
    return __generator(this, function (_b) {
        switch (_b.label) {
            case 0:
                email = payload.email;
                _b.label = 1;
            case 1:
                _b.trys.push([1, 4, , 6]);
                return [4 /*yield*/, effects_1.call(auth_1.auth.signInAsSuperuser, email)];
            case 2:
                loginUser = _b.sent();
                superuserToken_1.setSuperuserToken(loginUser.token);
                return [4 /*yield*/, authenticateUser(routes_1.ERoutes.Main)];
            case 3:
                _b.sent();
                return [3 /*break*/, 6];
            case 4:
                error_2 = _b.sent();
                Notifications_1.NotificationManager.error({
                    title: 'Login failed',
                    message: getErrorMessage_1.getErrorMessage(error_2)
                });
                return [4 /*yield*/, effects_1.put(actions_1.authUserFail(actions_1.EAuthUserFailType.Common))];
            case 5:
                _b.sent();
                return [3 /*break*/, 6];
            case 6: return [2 /*return*/];
        }
    });
}
exports.loginSuperuser = loginSuperuser;
function loginPartnerSuperuser(_a) {
    var result, error_3;
    var tenantId = _a.payload.tenantId;
    return __generator(this, function (_b) {
        switch (_b.label) {
            case 0:
                _b.trys.push([0, 5, 6, 8]);
                return [4 /*yield*/, effects_1.put(actions_2.setGeneralLoaderVisibility(true))];
            case 1:
                _b.sent();
                return [4 /*yield*/, effects_1.call(getTenantToken_1.getTenantToken, tenantId)];
            case 2:
                result = _b.sent();
                return [4 /*yield*/, handleLogoutUnsubscribing({ shouldExpireToken: false })];
            case 3:
                _b.sent();
                superuserToken_1.setSuperuserToken(result.token);
                superuserReturnRoute_1.setSuperuserReturnRoute(history_1.history.location.pathname);
                return [4 /*yield*/, authenticateUser(routes_1.ERoutes.Main)];
            case 4:
                _b.sent();
                return [3 /*break*/, 8];
            case 5:
                error_3 = _b.sent();
                Notifications_1.NotificationManager.error({
                    title: 'Login failed',
                    message: getErrorMessage_1.getErrorMessage(error_3)
                });
                return [3 /*break*/, 8];
            case 6: return [4 /*yield*/, effects_1.put(actions_2.setGeneralLoaderVisibility(false))];
            case 7:
                _b.sent();
                return [7 /*endfinally*/];
            case 8: return [2 /*return*/];
        }
    });
}
exports.loginPartnerSuperuser = loginPartnerSuperuser;
function retrunFromSupermodeSaga() {
    var returnRoute, error_4;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                _a.trys.push([0, 4, 5, 7]);
                return [4 /*yield*/, effects_1.put(actions_2.setGeneralLoaderVisibility(true))];
            case 1:
                _a.sent();
                return [4 /*yield*/, handleLogoutUnsubscribing({ shouldExpireToken: false })];
            case 2:
                _a.sent();
                returnRoute = superuserReturnRoute_1.getSuperuserReturnRoute() || routes_1.ERoutes.Main;
                return [4 /*yield*/, authenticateUser(returnRoute)];
            case 3:
                _a.sent();
                superuserReturnRoute_1.resetSuperuserReturnRoute();
                return [3 /*break*/, 7];
            case 4:
                error_4 = _a.sent();
                Notifications_1.NotificationManager.error({
                    title: 'Login failed',
                    message: getErrorMessage_1.getErrorMessage(error_4)
                });
                return [3 /*break*/, 7];
            case 5: return [4 /*yield*/, effects_1.put(actions_2.setGeneralLoaderVisibility(false))];
            case 6:
                _a.sent();
                return [7 /*endfinally*/];
            case 7: return [2 /*return*/];
        }
    });
}
exports.retrunFromSupermodeSaga = retrunFromSupermodeSaga;
exports.registerWithEmailAsync = function (user, utmParams, captcha) {
    return auth_1.auth
        .createUserWithEmail(user, utmParams, captcha)
        .then(function (authUser) { return authUser; })["catch"](function (error) { return error; });
};
function registerWithEmailPassword(_a) {
    var utmParams, registerUser, _b, id, type, error_5;
    var _c = _a.payload, user = _c.user, captcha = _c.captcha, onStart = _c.onStart, onFinish = _c.onFinish;
    return __generator(this, function (_d) {
        switch (_d.label) {
            case 0:
                _d.trys.push([0, 7, 9, 10]);
                onStart === null || onStart === void 0 ? void 0 : onStart();
                utmParams = utmParams_1.getUTMParams();
                return [4 /*yield*/, effects_1.call(exports.registerWithEmailAsync, user, utmParams, captcha)];
            case 1:
                registerUser = _d.sent();
                if (!(!registerUser.message && registerUser.token)) return [3 /*break*/, 4];
                return [4 /*yield*/, effects_1.put(actions_1.registerUserSuccess(registerUser))];
            case 2:
                _d.sent();
                authCookie_1.setJwtCookie(registerUser.token);
                _b = [auth_2.getOAuthId(), auth_2.getOAuthType()], id = _b[0], type = _b[1];
                if (id && type) {
                    setOAuthRegistrationCompleted_1.setOAuthRegistrationCompleted(id, type)["catch"](function (error) { return error; });
                }
                return [4 /*yield*/, authenticateUser(routes_1.ERoutes.Templates)];
            case 3:
                _d.sent();
                return [3 /*break*/, 6];
            case 4:
                console.info('register failed :', registerUser.message);
                Notifications_1.NotificationManager.error({
                    title: 'Register failed',
                    message: registerUser.message
                });
                return [4 /*yield*/, effects_1.put(actions_1.authUserFail())];
            case 5:
                _d.sent();
                _d.label = 6;
            case 6: return [3 /*break*/, 10];
            case 7:
                error_5 = _d.sent();
                console.info('register error : ', String(error_5));
                return [4 /*yield*/, effects_1.put(actions_1.authUserFail())];
            case 8:
                _d.sent();
                return [3 /*break*/, 10];
            case 9:
                onFinish === null || onFinish === void 0 ? void 0 : onFinish();
                return [7 /*endfinally*/];
            case 10: return [2 /*return*/];
        }
    });
}
exports.registerWithEmailPassword = registerWithEmailPassword;
exports.registerInviteAsync = function (id, body) {
    return auth_1.auth
        .createUserWithInvite(id, body)
        .then(function (authUser) { return authUser; })["catch"](function (error) { return error; });
};
function registerWithInvite(_a) {
    var id, user, error_6;
    var payload = _a.payload;
    return __generator(this, function (_b) {
        switch (_b.label) {
            case 0: return [4 /*yield*/, effects_1.select(user_1.getInvitedUser)];
            case 1:
                id = (_b.sent()).invitedUser.id;
                if (!!id) return [3 /*break*/, 3];
                return [4 /*yield*/, effects_1.put(actions_1.authUserFail())];
            case 2:
                _b.sent();
                return [2 /*return*/];
            case 3:
                _b.trys.push([3, 10, , 12]);
                return [4 /*yield*/, effects_1.call(exports.registerInviteAsync, id, payload)];
            case 4:
                user = _b.sent();
                if (!(!user.message && user.token)) return [3 /*break*/, 7];
                return [4 /*yield*/, effects_1.put(actions_1.registerUserSuccess(user))];
            case 5:
                _b.sent();
                authCookie_1.setJwtCookie(user.token);
                return [4 /*yield*/, effects_1.call(authenticateUser, routes_1.ERoutes.Main)];
            case 6:
                _b.sent();
                return [3 /*break*/, 9];
            case 7:
                console.info('register failed :', user.message);
                Notifications_1.NotificationManager.error({
                    title: 'Register failed',
                    message: user.message
                });
                return [4 /*yield*/, effects_1.put(actions_1.authUserFail())];
            case 8:
                _b.sent();
                _b.label = 9;
            case 9: return [3 /*break*/, 12];
            case 10:
                error_6 = _b.sent();
                console.info('register error : ', String(error_6));
                return [4 /*yield*/, effects_1.put(actions_1.authUserFail())];
            case 11:
                _b.sent();
                return [3 /*break*/, 12];
            case 12: return [2 /*return*/];
        }
    });
}
exports.registerWithInvite = registerWithInvite;
function handleLogoutUnsubscribing(_a) {
    var shouldExpireToken = _a.shouldExpireToken;
    return __generator(this, function (_b) {
        switch (_b.label) {
            case 0: return [4 /*yield*/, effects_1.put(actions_2.clearAppFilters())];
            case 1:
                _b.sent();
                firebase_1.resetFirebaseDeviceToken();
                superuserToken_1.resetSuperuserToken();
                analytics_1.analytics.reset();
                if (!shouldExpireToken) return [3 /*break*/, 3];
                return [4 /*yield*/, sendSignOut_1.sendSignOut()];
            case 2:
                _b.sent();
                authCookie_1.removeAuthCookies();
                localStorage_1.removeLocalStorage();
                _b.label = 3;
            case 3: return [2 /*return*/];
        }
    });
}
function logout(action) {
    var _a, showLoader, redirectUrl, authUser, error_7;
    return __generator(this, function (_b) {
        switch (_b.label) {
            case 0:
                _a = __assign({ showLoader: true, redirectUrl: routes_1.ERoutes.Login }, action.payload), showLoader = _a.showLoader, redirectUrl = _a.redirectUrl;
                _b.label = 1;
            case 1:
                _b.trys.push([1, 9, 10, 13]);
                return [4 /*yield*/, effects_1.select(user_1.getAuthUser)];
            case 2:
                authUser = (_b.sent()).authUser;
                if (authUser.loggedState === redux_1.ELoggedState.LoggedOut) {
                    return [2 /*return*/];
                }
                if (!showLoader) return [3 /*break*/, 4];
                return [4 /*yield*/, effects_1.put(actions_2.setGeneralLoaderVisibility(true))];
            case 3:
                _b.sent();
                _b.label = 4;
            case 4: return [4 /*yield*/, handleLogoutUnsubscribing({ shouldExpireToken: true })];
            case 5:
                _b.sent();
                return [4 /*yield*/, effects_1.put(actions_1.logoutUserSuccess())];
            case 6:
                _b.sent();
                if (!redirectUrl) return [3 /*break*/, 8];
                return [4 /*yield*/, effects_1.put(actions_1.redirectToLogin())];
            case 7:
                _b.sent();
                _b.label = 8;
            case 8: return [3 /*break*/, 13];
            case 9:
                error_7 = _b.sent();
                logger_1.logger.error('logout error:', error_7);
                return [3 /*break*/, 13];
            case 10:
                if (!showLoader) return [3 /*break*/, 12];
                return [4 /*yield*/, effects_1.put(actions_2.setGeneralLoaderVisibility(false))];
            case 11:
                _b.sent();
                _b.label = 12;
            case 12: return [7 /*endfinally*/];
            case 13: return [2 /*return*/];
        }
    });
}
exports.logout = logout;
exports.updateUserAsync = function (body) {
    return editProfile_1.editProfile(body)
        .then(function (authUser) { return authUser; })["catch"](function (error) { return error; });
};
function editCurrentProfile(_a) {
    var result, err_2;
    var payload = _a.payload;
    return __generator(this, function (_b) {
        switch (_b.label) {
            case 0:
                _b.trys.push([0, 3, , 5]);
                return [4 /*yield*/, effects_1.call(exports.updateUserAsync, payload)];
            case 1:
                result = _b.sent();
                if (!result) {
                    return [2 /*return*/];
                }
                Notifications_1.NotificationManager.success({
                    message: 'user-account.edit-profile-success'
                });
                return [4 /*yield*/, effects_1.put(actions_1.editCurrentUserSuccess(mappers_1.mapToCamelCase(result)))];
            case 2:
                _b.sent();
                return [3 /*break*/, 5];
            case 3:
                err_2 = _b.sent();
                return [4 /*yield*/, effects_1.put(actions_1.profileEditFailed())];
            case 4:
                _b.sent();
                Notifications_1.NotificationManager.error({ message: 'user-account.edit-account-fail' });
                logger_1.logger.error('edit profile error', err_2);
                return [3 /*break*/, 5];
            case 5: return [2 /*return*/];
        }
    });
}
exports.editCurrentProfile = editCurrentProfile;
function editCurrentAccount(_a) {
    var result, err_3;
    var payload = _a.payload;
    return __generator(this, function (_b) {
        switch (_b.label) {
            case 0:
                _b.trys.push([0, 5, , 6]);
                return [4 /*yield*/, effects_1.call(editAccount_1.editAccount, payload)];
            case 1:
                result = _b.sent();
                if (!!result) return [3 /*break*/, 3];
                return [4 /*yield*/, effects_1.put(actions_1.accountEditFailed())];
            case 2:
                _b.sent();
                Notifications_1.NotificationManager.error({
                    message: 'user-account.edit-account-fail'
                });
                return [2 /*return*/];
            case 3:
                Notifications_1.NotificationManager.success({
                    message: 'user-account.edit-account-success'
                });
                return [4 /*yield*/, effects_1.put(actions_1.editCurrentAccountSuccess(result))];
            case 4:
                _b.sent();
                return [3 /*break*/, 6];
            case 5:
                err_3 = _b.sent();
                Notifications_1.NotificationManager.error({ message: 'user-account.edit-account-fail' });
                logger_1.logger.error('account edit error', err_3);
                return [3 /*break*/, 6];
            case 6: return [2 /*return*/];
        }
    });
}
exports.editCurrentAccount = editCurrentAccount;
function sendPasswordReset(_a) {
    var e_1, message;
    var payload = _a.payload;
    return __generator(this, function (_b) {
        switch (_b.label) {
            case 0:
                _b.trys.push([0, 3, , 5]);
                return [4 /*yield*/, effects_1.call(resetPassword_1.resetPassword, payload)];
            case 1:
                _b.sent();
                Notifications_1.NotificationManager.success({
                    message: 'Email with reset instructions was sent'
                });
                return [4 /*yield*/, effects_1.put(actions_1.sendForgotPasswordSuccess())];
            case 2:
                _b.sent();
                return [3 /*break*/, 5];
            case 3:
                e_1 = _b.sent();
                message = getErrorMessage_1.getErrorMessage(e_1);
                logger_1.logger.error(message, e_1);
                Notifications_1.NotificationManager.error({ message: message });
                return [4 /*yield*/, effects_1.put(actions_1.sendForgotPasswordFail())];
            case 4:
                _b.sent();
                return [3 /*break*/, 5];
            case 5: return [2 /*return*/];
        }
    });
}
exports.sendPasswordReset = sendPasswordReset;
function sendPasswordChange(_a) {
    var token, e_2, errorMessages;
    var payload = _a.payload;
    return __generator(this, function (_b) {
        switch (_b.label) {
            case 0:
                _b.trys.push([0, 4, , 6]);
                return [4 /*yield*/, effects_1.call(changePassword_1.changePassword, payload)];
            case 1:
                token = (_b.sent()).token;
                Notifications_1.NotificationManager.success({
                    message: 'user-account.change-password-success'
                });
                return [4 /*yield*/, effects_1.put(actions_1.setUserToken(token))];
            case 2:
                _b.sent();
                return [4 /*yield*/, effects_1.put(actions_1.sendChangePasswordSuccess())];
            case 3:
                _b.sent();
                return [3 /*break*/, 6];
            case 4:
                e_2 = _b.sent();
                errorMessages = getErrorMessage_1.getErrorMessage(e_2);
                logger_1.logger.error(errorMessages, e_2);
                Notifications_1.NotificationManager.error({ message: errorMessages });
                return [4 /*yield*/, effects_1.put(actions_1.sendChangePasswordFail())];
            case 5:
                _b.sent();
                return [3 /*break*/, 6];
            case 6: return [2 /*return*/];
        }
    });
}
exports.sendPasswordChange = sendPasswordChange;
var resetPasswordSetAsync = function (body) {
    return resetPasswordSet_1.resetPasswordSet(body)
        .then(function (data) { return data; })["catch"](function (e) { return e; });
};
function sendPasswordResetConfirm(_a) {
    var loginUser, e_3;
    var payload = _a.payload;
    return __generator(this, function (_b) {
        switch (_b.label) {
            case 0:
                _b.trys.push([0, 3, , 5]);
                return [4 /*yield*/, effects_1.call(resetPasswordSetAsync, payload)];
            case 1:
                loginUser = _b.sent();
                authCookie_1.setJwtCookie(loginUser.token);
                return [4 /*yield*/, effects_1.put(actions_1.sendResetPasswordSuccess(loginUser))];
            case 2:
                _b.sent();
                window.location.replace(routes_1.ERoutes.Main);
                return [3 /*break*/, 5];
            case 3:
                e_3 = _b.sent();
                logger_1.logger.error(e_3);
                return [4 /*yield*/, effects_1.put(actions_1.sendResetPasswordFail())];
            case 4:
                _b.sent();
                return [3 /*break*/, 5];
            case 5: return [2 /*return*/];
        }
    });
}
exports.sendPasswordResetConfirm = sendPasswordResetConfirm;
function handleSetUserToken(_a) {
    var payload = _a.payload;
    authCookie_1.setJwtCookie(payload);
}
exports.handleSetUserToken = handleSetUserToken;
function fetchResendVerification() {
    var e_4;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                _a.trys.push([0, 2, , 3]);
                return [4 /*yield*/, resendVerification_1.resendVerification()];
            case 1:
                _a.sent();
                Notifications_1.NotificationManager.success({ message: 'dashboard.resend-verification' });
                return [3 /*break*/, 3];
            case 2:
                e_4 = _a.sent();
                logger_1.logger.error(e_4);
                Notifications_1.NotificationManager.error({ message: getErrorMessage_1.getErrorMessage(e_4) });
                return [3 /*break*/, 3];
            case 3: return [2 /*return*/];
        }
    });
}
exports.fetchResendVerification = fetchResendVerification;
function handleUploadUserPhoto(_a) {
    var id, value, error_8;
    var _b = _a.payload, photo = _b.photo, onComplete = _b.onComplete;
    return __generator(this, function (_c) {
        switch (_c.label) {
            case 0:
                _c.trys.push([0, 7, 8, 10]);
                return [4 /*yield*/, effects_1.select(user_1.getAuthUser)];
            case 1:
                id = (_c.sent()).authUser.account.id;
                return [4 /*yield*/, effects_1.put(actions_2.setGeneralLoaderVisibility(true))];
            case 2:
                _c.sent();
                return [4 /*yield*/, uploadFiles_1.uploadUserAvatar(photo, id)];
            case 3:
                value = (_c.sent())[0];
                if (!(value === null || value === void 0 ? void 0 : value.url)) return [3 /*break*/, 6];
                return [4 /*yield*/, effects_1.call(changePhotoProfile_1.changePhotoProfile, { photo: value.url })];
            case 4:
                _c.sent();
                return [4 /*yield*/, effects_1.put(actions_1.setUserPhoto(value.url))];
            case 5:
                _c.sent();
                onComplete === null || onComplete === void 0 ? void 0 : onComplete();
                _c.label = 6;
            case 6: return [3 /*break*/, 10];
            case 7:
                error_8 = _c.sent();
                logger_1.logger.error('failed to upload user photo', error_8);
                Notifications_1.NotificationManager.error({ message: getErrorMessage_1.getErrorMessage(error_8) });
                return [3 /*break*/, 10];
            case 8: return [4 /*yield*/, effects_1.put(actions_2.setGeneralLoaderVisibility(false))];
            case 9:
                _c.sent();
                return [7 /*endfinally*/];
            case 10: return [2 /*return*/];
        }
    });
}
exports.handleUploadUserPhoto = handleUploadUserPhoto;
function handleDeleteUserPhoto() {
    var error_9;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                _a.trys.push([0, 4, 5, 7]);
                return [4 /*yield*/, effects_1.put(actions_2.setGeneralLoaderVisibility(true))];
            case 1:
                _a.sent();
                return [4 /*yield*/, effects_1.call(changePhotoProfile_1.changePhotoProfile, { photo: '' })];
            case 2:
                _a.sent();
                return [4 /*yield*/, effects_1.put(actions_1.setUserPhoto(''))];
            case 3:
                _a.sent();
                return [3 /*break*/, 7];
            case 4:
                error_9 = _a.sent();
                logger_1.logger.error('failed to delete user photo', error_9);
                Notifications_1.NotificationManager.error({ message: getErrorMessage_1.getErrorMessage(error_9) });
                return [3 /*break*/, 7];
            case 5: return [4 /*yield*/, effects_1.put(actions_2.setGeneralLoaderVisibility(false))];
            case 6:
                _a.sent();
                return [7 /*endfinally*/];
            case 7: return [2 /*return*/];
        }
    });
}
exports.handleDeleteUserPhoto = handleDeleteUserPhoto;
function handleWatchUserWSEvents() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.all([effects_1.fork(saga_1.watchNewTask), effects_1.fork(saga_1.watchRemoveTask), effects_1.fork(saga_2.watchNewNotifications), effects_1.fork(saga_4.watchNewWorkflowsEvent)])];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
function handleSetRedirectUrl(_a) {
    var redirectUrl = _a.payload;
    sessionStorage.setItem(storageKeys_1.REDIRECT_URL_STORAGE_KEY, redirectUrl);
}
exports.handleSetRedirectUrl = handleSetRedirectUrl;
function collectPaymentDetailsSaga() {
    var paymentCardProvided;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.select(user_1.getAuthUser)];
            case 1:
                paymentCardProvided = (_a.sent()).authUser.account.paymentCardProvided;
                if (paymentCardProvided) {
                    history_1.history.push(routes_1.ERoutes.Tasks);
                    return [2 /*return*/];
                }
                return [4 /*yield*/, effects_1.put(actions_1.makeStripePayment({
                        successUrl: getAbsolutePath_1.getAbsolutePath(routes_1.ERoutes.AfterPaymentDetailsProvided, { after_registration: 'true' }),
                        cancelUrl: getAbsolutePath_1.getAbsolutePath(routes_1.ERoutes.Login),
                        code: 'unlimited_month',
                        showLoader: false
                    }))];
            case 2:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.collectPaymentDetailsSaga = collectPaymentDetailsSaga;
function changePaymentDetailsSaga() {
    var response, error_10;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                _a.trys.push([0, 4, , 5]);
                return [4 /*yield*/, effects_1.put(actions_2.setGeneralLoaderVisibility(true))];
            case 1:
                _a.sent();
                return [4 /*yield*/, effects_1.call(cardSetup_1.cardSetup, {
                        successUrl: getAbsolutePath_1.getAbsolutePath(routes_1.ERoutes.AfterPaymentDetailsProvided, { new_payment_details: 'true' }),
                        cancelUrl: getAbsolutePath_1.getAbsolutePath(routes_1.ERoutes.Main)
                    })];
            case 2:
                response = _a.sent();
                if (response.setupLink) {
                    window.location.replace(response.setupLink);
                    return [2 /*return*/];
                }
                return [4 /*yield*/, effects_1.put(actions_2.setGeneralLoaderVisibility(false))];
            case 3:
                _a.sent();
                return [3 /*break*/, 5];
            case 4:
                error_10 = _a.sent();
                logger_1.logger.error(error_10);
                Notifications_1.NotificationManager.error({ message: getErrorMessage_1.getErrorMessage(error_10) });
                return [3 /*break*/, 5];
            case 5: return [2 /*return*/];
        }
    });
}
exports.changePaymentDetailsSaga = changePaymentDetailsSaga;
function makeStripePaymentSaga(_a) {
    var response, error_11;
    var _b = _a.payload, successUrl = _b.successUrl, cancelUrl = _b.cancelUrl, code = _b.code, _c = _b.quantity, quantity = _c === void 0 ? 1 : _c, _d = _b.showLoader, showLoader = _d === void 0 ? true : _d;
    return __generator(this, function (_e) {
        switch (_e.label) {
            case 0:
                _e.trys.push([0, 8, , 11]);
                if (!showLoader) return [3 /*break*/, 2];
                return [4 /*yield*/, effects_1.put(actions_2.setGeneralLoaderVisibility(true))];
            case 1:
                _e.sent();
                _e.label = 2;
            case 2: return [4 /*yield*/, effects_1.call(makePayment_1.makePayment, {
                    successUrl: successUrl,
                    cancelUrl: cancelUrl,
                    code: code,
                    quantity: quantity
                })];
            case 3:
                response = _e.sent();
                if (response.paymentLink) {
                    window.location.replace(response.paymentLink);
                    return [2 /*return*/];
                }
                return [4 /*yield*/, saga_3.fetchPlan()];
            case 4:
                _e.sent();
                return [4 /*yield*/, authenticateUser()];
            case 5:
                _e.sent();
                if (!showLoader) return [3 /*break*/, 7];
                return [4 /*yield*/, effects_1.put(actions_2.setGeneralLoaderVisibility(false))];
            case 6:
                _e.sent();
                _e.label = 7;
            case 7:
                history_1.history.push(routes_1.ERoutes.Tasks);
                Notifications_1.NotificationManager.success({ message: 'checkout.payment-success-title' });
                return [3 /*break*/, 11];
            case 8:
                error_11 = _e.sent();
                if (!showLoader) return [3 /*break*/, 10];
                return [4 /*yield*/, effects_1.put(actions_2.setGeneralLoaderVisibility(false))];
            case 9:
                _e.sent();
                _e.label = 10;
            case 10:
                logger_1.logger.error(error_11);
                Notifications_1.NotificationManager.error({ message: getErrorMessage_1.getErrorMessage(error_11) });
                return [3 /*break*/, 11];
            case 11: return [2 /*return*/];
        }
    });
}
exports.makeStripePaymentSaga = makeStripePaymentSaga;
function onAfterPaymentDetailsProvidedSaga() {
    var _a, afterRegistrationParam, newPaymentDetailsParam, env, templateId, error_12;
    return __generator(this, function (_b) {
        switch (_b.label) {
            case 0: return [4 /*yield*/, confirmPaymentDetailsProvided_1.confirmPaymentDetailsProvided()];
            case 1:
                _b.sent();
                _a = history_1.getQueryStringParams(history_1.history.location.search), afterRegistrationParam = _a.after_registration, newPaymentDetailsParam = _a.new_payment_details;
                if (newPaymentDetailsParam) {
                    history_1.history.push(routes_1.ERoutes.Main);
                    return [2 /*return*/];
                }
                if (!afterRegistrationParam) {
                    history_1.history.push(routes_1.ERoutes.Tasks);
                    return [2 /*return*/];
                }
                env = getConfig_1.getBrowserConfig().env;
                if (env === 'prod') {
                    trackCrozdesk_1.trackCrozdesk();
                }
                _b.label = 2;
            case 2:
                _b.trys.push([2, 5, , 6]);
                return [4 /*yield*/, createTemplateFromName_1.createTemplateFromName()];
            case 3:
                templateId = _b.sent();
                if (templateId) {
                    history_1.history.push(routes_1.ERoutes.TemplatesEdit.replace(':id', String(templateId)));
                    return [2 /*return*/];
                }
                return [4 /*yield*/, createAITemplate_1.createAITemplate()];
            case 4:
                _b.sent();
                history_1.history.push(routes_1.ERoutes.Templates);
                return [3 /*break*/, 6];
            case 5:
                error_12 = _b.sent();
                history_1.history.push(routes_1.ERoutes.Templates);
                return [3 /*break*/, 6];
            case 6: return [2 /*return*/];
        }
    });
}
exports.onAfterPaymentDetailsProvidedSaga = onAfterPaymentDetailsProvidedSaga;
function redirectToCustomerPortalSaga() {
    var link, error_13;
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0:
                _a.trys.push([0, 4, , 6]);
                return [4 /*yield*/, effects_1.put(actions_2.setGeneralLoaderVisibility(true))];
            case 1:
                _a.sent();
                return [4 /*yield*/, effects_1.call(getCustomerPortalLink_1.getCustomerPortalLink, encodeURIComponent(window.location.href))];
            case 2:
                link = (_a.sent()).link;
                if (link) {
                    window.location.replace(link);
                    return [2 /*return*/];
                }
                return [4 /*yield*/, effects_1.put(actions_2.setGeneralLoaderVisibility(false))];
            case 3:
                _a.sent();
                return [3 /*break*/, 6];
            case 4:
                error_13 = _a.sent();
                return [4 /*yield*/, effects_1.put(actions_2.setGeneralLoaderVisibility(false))];
            case 5:
                _a.sent();
                logger_1.logger.error(error_13);
                Notifications_1.NotificationManager.error({ message: getErrorMessage_1.getErrorMessage(error_13) });
                return [3 /*break*/, 6];
            case 6: return [2 /*return*/];
        }
    });
}
function watchAuthUser() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("AUTH_USER" /* AuthUser */, authUserSaga)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchAuthUser = watchAuthUser;
function watchEditUser() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("EDIT_USER" /* EditUser */, editCurrentProfile)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchEditUser = watchEditUser;
function watchRegisterUser() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("REGISTER_USER" /* RegisterUser */, registerWithEmailPassword)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchRegisterUser = watchRegisterUser;
function watchRegisterUserInvited() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("REGISTER_USER_INVITED" /* RegisterUserInvited */, registerWithInvite)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchRegisterUserInvited = watchRegisterUserInvited;
function watchLoginUser() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("LOGIN_USER" /* LoginUser */, loginWithEmailPassword)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchLoginUser = watchLoginUser;
function watchLoginSuperuser() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("LOGIN_SUPERUSER" /* LoginSuperuser */, loginSuperuser)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchLoginSuperuser = watchLoginSuperuser;
function watchLoginPartnerSuperuser() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("LOGIN_PARTNER_SUPERUSER" /* LoginPartnerSuperuser */, loginPartnerSuperuser)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchLoginPartnerSuperuser = watchLoginPartnerSuperuser;
function watchLogoutUser() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeLeading("LOGOUT_USER" /* LogoutUser */, logout)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchLogoutUser = watchLogoutUser;
function watchChangePassword() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("CHANGE_PASSWORD" /* ChangePassword */, sendPasswordChange)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchChangePassword = watchChangePassword;
function watchForgotPassword() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("FORGOT_PASSWORD" /* ForgotPassword */, sendPasswordReset)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchForgotPassword = watchForgotPassword;
function watchResetPassword() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("RESET_PASSWORD" /* ResetPassword */, sendPasswordResetConfirm)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchResetPassword = watchResetPassword;
function watchEditAccount() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("EDIT_ACCOUNT" /* EditAccount */, editCurrentAccount)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchEditAccount = watchEditAccount;
function watchResendVerification() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeLatest("RESEND_VERIFICATION" /* ResendVerification */, fetchResendVerification)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchResendVerification = watchResendVerification;
function watchSetRedirectUrl() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeLatest("SET_REDIRECT_URL" /* SetRedirectUrl */, handleSetRedirectUrl)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchSetRedirectUrl = watchSetRedirectUrl;
function watchSetUserToken() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("SET_USER_TOKEN" /* SetToken */, handleSetUserToken)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchSetUserToken = watchSetUserToken;
function watchUserWSEvents() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("WATCH_USER_WS_EVENTS" /* WatchUserWSEvents */, handleWatchUserWSEvents)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchUserWSEvents = watchUserWSEvents;
function watchUploadUserPhoto() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("UPLOAD_USER_PHOTO" /* UploadUserPhoto */, handleUploadUserPhoto)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchUploadUserPhoto = watchUploadUserPhoto;
function watchDeleteUserPhoto() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("DELETE_USER_PHOTP" /* DeleteUserPhoto */, handleDeleteUserPhoto)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchDeleteUserPhoto = watchDeleteUserPhoto;
function watchReturnFromSupermode() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("RETURN_FROM_SUPERMODE" /* ReturnFromSupermode */, retrunFromSupermodeSaga)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchReturnFromSupermode = watchReturnFromSupermode;
function watchCollectPaymentDetails() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("COLLECT_PAYMENT_DETAILS" /* CollectPaymentDetails */, collectPaymentDetailsSaga)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchCollectPaymentDetails = watchCollectPaymentDetails;
function watchChangePaymentDetails() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("CHANGE_PAYMENT_DETAILS" /* ChangePaymentDetails */, changePaymentDetailsSaga)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchChangePaymentDetails = watchChangePaymentDetails;
function watchMakeStripePayment() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("MAKE_STRIPE_PAYMENT" /* MakeStripePayment */, makeStripePaymentSaga)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchMakeStripePayment = watchMakeStripePayment;
function watchOnAfterPaymentDetailsProvided() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("AFTER_PAYMENT_DEATILS_PROVIDED" /* OnAfterPaymentDetailsProvided */, onAfterPaymentDetailsProvidedSaga)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchOnAfterPaymentDetailsProvided = watchOnAfterPaymentDetailsProvided;
function watchRedirectToCustomerPortal() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.takeEvery("REDIRECT_TO_CUSTOMER_PORTAL" /* RedirectToCustomerPortal */, redirectToCustomerPortalSaga)];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.watchRedirectToCustomerPortal = watchRedirectToCustomerPortal;
function rootSaga() {
    return __generator(this, function (_a) {
        switch (_a.label) {
            case 0: return [4 /*yield*/, effects_1.all([
                    effects_1.fork(watchLoginUser),
                    effects_1.fork(watchLoginSuperuser),
                    effects_1.fork(watchLoginPartnerSuperuser),
                    effects_1.fork(watchLogoutUser),
                    effects_1.fork(watchRegisterUser),
                    effects_1.fork(watchRegisterUserInvited),
                    effects_1.fork(watchAuthUser),
                    effects_1.fork(watchChangePassword),
                    effects_1.fork(watchEditAccount),
                    effects_1.fork(watchEditUser),
                    effects_1.fork(watchForgotPassword),
                    effects_1.fork(watchResetPassword),
                    effects_1.fork(watchResendVerification),
                    effects_1.fork(watchSetRedirectUrl),
                    effects_1.fork(watchSetUserToken),
                    effects_1.fork(watchUserWSEvents),
                    effects_1.fork(watchUploadUserPhoto),
                    effects_1.fork(watchDeleteUserPhoto),
                    effects_1.fork(watchReturnFromSupermode),
                    effects_1.fork(watchCollectPaymentDetails),
                    effects_1.fork(watchChangePaymentDetails),
                    effects_1.fork(watchMakeStripePayment),
                    effects_1.fork(watchOnAfterPaymentDetailsProvided),
                    effects_1.fork(watchRedirectToCustomerPortal),
                ])];
            case 1:
                _a.sent();
                return [2 /*return*/];
        }
    });
}
exports.rootSaga = rootSaga;
