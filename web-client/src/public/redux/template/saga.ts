/* eslint-disable */
/* prettier-ignore */
/* tslint:disable:max-file-line-count */
import {
  actionChannel,
  ActionChannelEffect,
  ActionPattern,
  all,
  call,
  cancelled,
  CancelledEffect,
  delay,
  fork,
  put,
  select,
  take,
  takeEvery,
  takeLatest,
} from 'redux-saga/effects';
import { buffers } from 'redux-saga';

import {
  ETemplateActions,
  loadFromSystemSuccess,
  patchTemplate,
  saveTemplate,
  saveTemplateCanceled,
  saveTemplateFailed,
  saveTemplateSuccess,
  setAITemplateData,
  setAITemplateGenerationStatus,
  setTemplate,
  setTemplateStatus,
  TCloneTemplate,
  TDeleteTemplate,
  TDiscardChanges,
  TGenerateAITemplate,
  TLoadTemplate,
  TLoadTemplateFromSystem,
  TPatchTask,
  TPatchTemplate,
  TSaveTemplate,
  TStopAITemplateGeneration,
} from './actions';

import { getIsUserSubsribed, getUsers } from '../selectors/user';
import { createTemplate } from '../../api/createTemplate';
import { ERoutes } from '../../constants/routes';
import { getTemplateData } from '../selectors/template';
import { getTemplate } from '../../api/getTemplate';
import { getSystemTemplate } from '../../api/getSystemTemplate';
import { checkSomeRouteIsActive, history } from '../../utils/history';
import { ITemplate, ITemplateRequest, ITemplateResponse } from '../../types/template';
import { logger } from '../../utils/logger';
import { NotificationManager } from '../../components/UI/Notifications';
import { updateTemplate } from '../../api/updateTemplate';
import { getNormalizedTemplate, mapTemplateRequest } from '../../utils/template';
import { getErrorMessage, isPaidFeatureError } from '../../utils/getErrorMessage';
import { insertId } from '../../utils/templates/insertId';
import { ETemplateStatus } from '../../types/redux';
import { TUserListItem } from '../../types/user';
import { loadTemplateIntegrationsStats, loadTemplates } from '../actions';
import { copyTemplate } from '../../api/copyTemplate';
import { deleteTemplate } from '../../api/deleteTemplate';
import { setGeneralLoaderVisibility } from '../general/actions';
import { generateAITemplate } from '../../api/generateAITemplate';
import { discardTemplateChanges } from '../../api/discardTemplateChanges';

function* setTemplateByTemplateResponse(template: ITemplateResponse) {
  const isSubscribed: ReturnType<typeof getIsUserSubsribed> = yield select(getIsUserSubsribed);
  const users: ReturnType<typeof getUsers> = yield select(getUsers);

  const normalizedTemplate = getNormalizedTemplate(template, isSubscribed, users);
  yield put(setTemplate(normalizedTemplate));
}

function* fetchTemplate({ payload: id }: TLoadTemplate) {
  if (!Number.isInteger(id)) {
    history.replace(ERoutes.Templates);
    NotificationManager.warning({ message: 'template.not-found' });

    return;
  }

  try {
    const template: ITemplateResponse = yield getTemplate(id);
    yield setTemplateByTemplateResponse(template);
    yield put(setTemplateStatus(ETemplateStatus.Saved));

    yield put(loadTemplateIntegrationsStats({ templates: [template.id] }));
  } catch (error) {
    logger.info('failed lo load template: ', error);
    NotificationManager.warning({ message: getErrorMessage(error) });
    history.replace(ERoutes.Main);
    yield put(setTemplateStatus(ETemplateStatus.LoadingFailed));
  }
}

function* patchTemplateSaga({ payload: { changedFields, onSuccess, onFailed } }: TPatchTemplate) {
  const template: ReturnType<typeof getTemplateData> = yield select(getTemplateData);

  yield put(setTemplateStatus(ETemplateStatus.Saving));

  const nonDeactivativeFields: (keyof ITemplate)[] = ['isActive', 'isPublic', 'publicUrl', 'publicSuccessUrl'];
  let shouldDeactivateTemplate = Object.keys(changedFields).some(
    (key) => !nonDeactivativeFields.includes(key as keyof ITemplate),
  );

  if (Object.keys(changedFields).length === 1 && changedFields.hasOwnProperty('kickoff')) {
    shouldDeactivateTemplate =
      changedFields.kickoff?.description === template.kickoff.description ? shouldDeactivateTemplate : false;
  }

  const newTemplate: ITemplate = {
    ...template,
    ...changedFields,
    ...(shouldDeactivateTemplate && { isActive: false }),
  };

  yield put(setTemplate(newTemplate));
  yield delay(350);
  yield put(saveTemplate({ onSuccess, onFailed }));
}

function* patchTaskSaga({ payload: { taskUUID, changedFields } }: TPatchTask) {
  const template: ReturnType<typeof getTemplateData> = yield select(getTemplateData);

  const newTasks = template.tasks.map((task) => {
    if (task.uuid === taskUUID) {
      return { ...task, ...changedFields };
    }

    return task;
  });

  yield put(patchTemplate({ changedFields: { tasks: newTasks } }));
}

function* fetchTemplateFromSystem({ payload: id }: TLoadTemplateFromSystem) {
  try {
    const systemTemplate: ITemplateResponse = yield getSystemTemplate(id);
    const isSubscribed: ReturnType<typeof getIsUserSubsribed> = yield select(getIsUserSubsribed);
    const users: ReturnType<typeof getUsers> = yield select(getUsers);
    const normalizedTemplate = getNormalizedTemplate(systemTemplate, isSubscribed, users);
    yield put(setTemplate(normalizedTemplate));
    yield put(loadFromSystemSuccess());
  } catch (error) {
    logger.info('fetch system template error : ', error);
    if (error && error.detail === 'Not found.') {
      history.replace(ERoutes.TemplatesCreate);
      NotificationManager.error({ message: 'template.fetch-template-fail' });
    }

    yield put(setTemplateStatus(ETemplateStatus.LoadingFailed));
  }
}

function* createOrUpdateTemplate(template: ITemplateRequest, isSubscribed: boolean, users: TUserListItem[]) {
  try {
    const saveTemplatePromise = !template.id ? createTemplate(template) : updateTemplate(template.id, template);
    const result: ITemplateResponse = yield saveTemplatePromise;

    return getNormalizedTemplate(result, isSubscribed, users);
  } catch (error) {
    if (isPaidFeatureError(error)) {
      yield put(saveTemplateCanceled());

      return;
    }

    logger.error('failed to save template:', error);

    NotificationManager.error({
      title: 'template.save-failed',
      message: getErrorMessage(error),
      timeOut: 0
    });
    yield put(saveTemplateFailed());

    return null;
  }
}

function* fetchSaveTemplate(onSuccess?: () => void, onFailed?: () => void) {
  const isTemplatePage = checkSomeRouteIsActive(
    ERoutes.TemplateView,
    ERoutes.TemplatesCreate,
    ERoutes.TemplatesCreateAI,
    ERoutes.TemplatesEdit,
    ERoutes.Templates,
  );

  if (!isTemplatePage) return;

  const isSubscribed: ReturnType<typeof getIsUserSubsribed> = yield select(getIsUserSubsribed);
  const users: ReturnType<typeof getUsers> = yield select(getUsers);

  const editingTemplate: ReturnType<typeof getTemplateData> = yield select(getTemplateData);
  const templateRequest = mapTemplateRequest(editingTemplate);

  const savedTemplate: ITemplate | null = yield createOrUpdateTemplate(templateRequest, isSubscribed, users);
  const lastTemplateState: ReturnType<typeof getTemplateData> = yield select(getTemplateData);

  if (!savedTemplate) {
    yield put(setTemplate({ ...lastTemplateState, isActive: false }));

    onFailed?.();

    return;
  }

  const isTemplateCreated = !templateRequest.id;

  const newTemplateState: ITemplate = {
    ...insertId(lastTemplateState, savedTemplate),
    updatedBy: savedTemplate.updatedBy,
    dateUpdated: savedTemplate.dateUpdated,
    publicUrl: savedTemplate.publicUrl,
    embedUrl: savedTemplate.embedUrl,
  };

  yield put(setTemplate(newTemplateState));

  if (isTemplateCreated) {
    const redirectUrl = ERoutes.TemplatesEdit.replace(':id', String(savedTemplate.id));
    history.replace(redirectUrl);
  }

  yield put(saveTemplateSuccess());
  onSuccess?.();
}

function* handleCloneTemplate({ payload: { templateId } }: TCloneTemplate) {
  try {
    yield put(setGeneralLoaderVisibility(true));
    const clonedTemplate: ITemplateResponse = yield call(copyTemplate, templateId);

    if (clonedTemplate) {
      history.replace(ERoutes.TemplatesEdit.replace(':id', String(clonedTemplate.id)));
      NotificationManager.success({ title: 'template.success-copy' });
    }
  } catch (error) {
    NotificationManager.warning({
      title: 'template.fail-copy',
      message: getErrorMessage(error),
    });
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

function* handleDeleteTemplate({ payload: { templateId } }: TDeleteTemplate) {
  try {
    yield put(setGeneralLoaderVisibility(true));
    yield deleteTemplate(templateId);
    NotificationManager.success({ title: 'template.success-delete' });

    if (checkSomeRouteIsActive(ERoutes.Templates)) {
      yield put(loadTemplates(0));

      return;
    }

    history.push(ERoutes.Templates);
  } catch (err) {
    NotificationManager.warning({
      title: 'template.fail-delete',
      message: getErrorMessage(err),
    });
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

function* generateAITemplateSaga(action: TGenerateAITemplate | TStopAITemplateGeneration) {
  if (action.type === ETemplateActions.StopAITemplateGeneration) {
    yield put(setAITemplateGenerationStatus('initial'));
    yield put(setAITemplateData({ template: null }));

    return;
  }

  const {
    payload: { description: templateDescription },
  } = action;

  const isSubscribed: ReturnType<typeof getIsUserSubsribed> = yield select(getIsUserSubsribed);
  const users: ReturnType<typeof getUsers> = yield select(getUsers);

  const abortController = new AbortController();

  try {
    yield put(setAITemplateGenerationStatus('generating'));
    const generatedTemplate: ITemplateResponse = yield generateAITemplate(templateDescription, abortController.signal);
    yield put(setAITemplateData({ template: getNormalizedTemplate(generatedTemplate, isSubscribed, users) }));
    yield put(setAITemplateGenerationStatus('generated'));
  } catch (error) {
    yield put(setAITemplateGenerationStatus('initial'));
    logger.error('failed to generate AI template:', error);

    NotificationManager.error({ message: getErrorMessage(error) });
  } finally {
    const cancel: CancelledEffect = yield cancelled();
    if (cancel) {
      abortController.abort();
    }
  }
}

function* applyAITemplateSaga() {
  history.push(ERoutes.TemplatesCreateAI);
}

function* discardChangesSaga({ payload: { templateId, onSuccess } }: TDiscardChanges) {
  try {
    yield put(setGeneralLoaderVisibility(true));
    yield discardTemplateChanges({ templateId });
    onSuccess?.();
  } catch (err) {
    NotificationManager.warning({ message: getErrorMessage(err) });
  } finally {
    yield put(setGeneralLoaderVisibility(false));
  }
}

export function* watchFetchTemplate() {
  yield takeEvery(ETemplateActions.Load, fetchTemplate);
}

export function* watchPatchTemplate() {
  yield takeLatest(ETemplateActions.PatchTemplate, patchTemplateSaga);
}

export function* watchPatchTask() {
  yield takeLatest(ETemplateActions.PatchTask, patchTaskSaga);
}

export function* watchFetchTemplateFromSystem() {
  yield takeEvery(ETemplateActions.LoadFromSystem, fetchTemplateFromSystem);
}

export function* watchSaveTemplate() {
  const autosaveChannel: ActionPattern<ActionChannelEffect> = yield actionChannel(
    ETemplateActions.Save,
    buffers.sliding(1),
  );
  while (true) {
    const { payload }: TSaveTemplate = yield take(autosaveChannel);
    yield call(fetchSaveTemplate, payload?.onSuccess, payload?.onFailed);
  }
}

export function* watchCloneTemplate() {
  yield takeEvery(ETemplateActions.CloneTemplate, handleCloneTemplate);
}

export function* watchDeleteTemplate() {
  yield takeEvery(ETemplateActions.DeleteTemplate, handleDeleteTemplate);
}

export function* watchGenerateAITemplate() {
  yield takeLatest(
    [ETemplateActions.GenerateAITemplate, ETemplateActions.StopAITemplateGeneration],
    generateAITemplateSaga,
  );
}

export function* applyAITemplate() {
  yield takeEvery(ETemplateActions.ApplyAITemplate, applyAITemplateSaga);
}

export function* watchDiscardChanges() {
  yield takeEvery(ETemplateActions.DiscardChanges, discardChangesSaga);
}

export function* rootSaga() {
  yield all([
    fork(watchFetchTemplate),
    fork(watchFetchTemplateFromSystem),
    fork(watchSaveTemplate),
    fork(watchPatchTemplate),
    fork(watchPatchTask),
    fork(watchCloneTemplate),
    fork(watchDeleteTemplate),
    fork(watchGenerateAITemplate),
    fork(applyAITemplate),
    fork(watchDiscardChanges),
  ]);
}
