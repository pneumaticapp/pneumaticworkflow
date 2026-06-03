import * as React from 'react';
import { useState, useEffect } from 'react';
import { useIntl } from 'react-intl';
import ReCAPTCHA from 'react-google-recaptcha';
import produce from 'immer';
import classnames from 'classnames';
import { useDispatch } from 'react-redux';

import { NotificationManager } from '../../../UI/Notifications';
import { IExtraField } from '../../../../types/template';
import { Button } from '../../../UI/Buttons/Button';
import { getEditedFields } from '../../../TemplateEdit/ExtraFields/utils/getEditedFields';
import { EInputNameBackgroundColor } from '../../../../types/workflow';
import { getPublicForm } from '../../../../api/getPublicForm';
import { EPublicFormState, IPublicForm } from '../types';
import { logger } from '../../../../utils/logger';
import { getErrorMessage } from '../../../../utils/getErrorMessage';
import { MergedOutputList } from '../../../MergedOutputList';

import { runPublicForm } from '../../../../api/runPublicForm';
import { checkExtraFieldsAreValid } from '../../../WorkflowEditPopup/utils/areKickoffFieldsValid';
import { ExtraFieldsHelper } from '../../../TemplateEdit/ExtraFields/utils/ExtraFieldsHelper';
import { getNormalizedKickoff } from '../../../../utils/mappers';
import { Header } from '../../../UI/Typeography/Header';
import { getPublicFormConfig } from '../../../../utils/getConfig';
import { deleteRemovedFilesFromFields } from '../../../../api/deleteRemovedFilesFromFields';
import { RichText } from '../../../RichText';
import { usersFetchStarted } from '../../../../redux/accounts/slice';
import { TPublicFormType } from '../../../../types/publicForms';
import { Copyright } from '../Copyright';
import { FormSkeleton } from '../FormSkeleton';
import { useShouldHideIntercom } from '../../../../hooks/useShouldHideIntercom';
import { prependHttp } from '../../../../utils/prependHttp';

import submitedImage from '../images/SubmitedImage.svg';
import * as ErrorImage from '../images/ErrorImage.svg';

import '../../../../assets/fonts/simple-line-icons/css/simple-line-icons.css';
import '../../../../assets/fonts/iconsmind-s/css/iconsminds.css';
import '../../../../assets/css/vendor/bootstrap.min.css';
import '../../../../assets/css/sass/themes/gogo.light.yellow.scss';
import 'react-perfect-scrollbar/dist/css/styles.css';
import 'rc-switch/assets/index.css';
import { isEnvCaptcha } from '../../../../constants/enviroment';

import styles from './PublicForm.css';

interface IPublicFormsAppProps {
  type: TPublicFormType;
}

export function PublicForm({ type }: IPublicFormsAppProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const [formState, setFormState] = useState<EPublicFormState>(EPublicFormState.WaitingForAction);
  const [publicForm, setPublicForm] = useState<IPublicForm | null>(null);
  const [captcha, setCaptcha] = useState('');
  useShouldHideIntercom();

  useEffect(() => {
    dispatch(usersFetchStarted({ showErrorNotification: false }));
    fetchPublicForm();
  }, []);

  const fetchPublicForm = async () => {
    try {
      setFormState(EPublicFormState.Loading);

      const fetchedForm = await getPublicForm();

      if (!fetchedForm) {
        setFormState(EPublicFormState.FormNotFound);

        return;
      }

      const normalizedForm = produce(fetchedForm, (draftPublicForm) => {
        draftPublicForm.kickoff.fields = new ExtraFieldsHelper(fetchedForm.kickoff.fields).getFieldsWithValues();
      });

      setPublicForm(normalizedForm);
      setFormState(EPublicFormState.WaitingForAction);
    } catch (error) {
      setFormState(EPublicFormState.FormNotFound);
      logger.error('Failed to fetch public form.');
    }
  };

  const handleRunPublicForm = async () => {
    if (!publicForm) return;

    try {
      setFormState(EPublicFormState.Submitting);

      const allFieldsetFields = publicForm.kickoff.fieldsets.flatMap((fieldset) => fieldset.fields);
      const mergedKickoff = {
        ...publicForm.kickoff,
        fields: [...publicForm.kickoff.fields, ...allFieldsetFields],
      };

      await deleteRemovedFilesFromFields(mergedKickoff.fields);
      const normalizedKickoffFileds = getNormalizedKickoff(mergedKickoff);
      const runFormResult = await runPublicForm(captcha, normalizedKickoffFileds);

      if (runFormResult?.redirectUrl) {
        window.location.replace(prependHttp(runFormResult?.redirectUrl));

        return;
      }

      setFormState(EPublicFormState.Submitted);
    } catch (error) {
      NotificationManager.notifyApiError(error, { message: getErrorMessage(error) });
      logger.error('Failed to run public form', error);
      setFormState(EPublicFormState.WaitingForAction);
    }
  };


  const updatePublicForm = (updater: (draft: IPublicForm) => void) => {
    setPublicForm((prevPublicForm) => {
      if (!prevPublicForm) return prevPublicForm;
      return produce(prevPublicForm, updater);
    });
  };

  const handleEditField = (apiName: string) => (changedProps: Partial<IExtraField>) => {
    updatePublicForm((draft) => {
      draft.kickoff.fields = getEditedFields(draft.kickoff.fields, apiName, changedProps);
    });
  };

  const handleEditFieldsetField = (apiName: string) => (changedProps: Partial<IExtraField>) => {
    updatePublicForm((draft) => {
      draft.kickoff.fieldsets = draft.kickoff.fieldsets.map((fieldset) => ({
        ...fieldset,
        fields: getEditedFields(fieldset.fields, apiName, changedProps),
      }));
    });
  };

  const renderOutputFields = () => {
    if (!publicForm) {
      return null;
    }

    const {
      config: { recaptchaSecret },
    } = getPublicFormConfig();

    return (
      <>
        <MergedOutputList
          fields={publicForm.kickoff.fields.filter((field) => !field.isHidden)}
          fieldsets={publicForm.kickoff.fieldsets.map((fieldset) => ({
            ...fieldset,
            fields: fieldset.fields.filter((field) => !field.isHidden),
          }))}
          onEditField={handleEditField}
          onEditFieldsetField={handleEditFieldsetField}
          labelBackgroundColor={EInputNameBackgroundColor.OrchidWhite}
          fieldClassName={styles['output__field']}
          accountId={publicForm.accountId}
        />

        {isEnvCaptcha && publicForm?.showCaptcha && (
          <div className={styles['captcha']}>
            <ReCAPTCHA
              sitekey={recaptchaSecret}
              onChange={(token: string | null) => token && setCaptcha(token)}
              theme="light"
            />
          </div>
        )}
      </>
    );
  };

  if (formState === EPublicFormState.Loading) {
    return <FormSkeleton />;
  }

  if (formState === EPublicFormState.Submitted) {
    return (
      <div className={classnames(styles['notification'], type === 'embedded' && styles['embedded'])}>
        {type !== 'embedded' && (
          <img
            className={styles['notification__image']}
            src={submitedImage}
            alt={formatMessage({ id: 'public-form.submited-title' })}
          />
        )}
        <Header className={styles['notification__title']} size="2" tag="h1">
          {formatMessage({ id: 'public-form.submited-title' })}
        </Header>
        <p className={styles['notification__text']}>{formatMessage({ id: 'public-form.submited-text' })}</p>
        <Button
          size="md"
          buttonStyle="yellow"
          label={formatMessage({ id: 'public-form.submited-button' })}
          onClick={fetchPublicForm}
        />
        {type === 'embedded' && <Copyright className={styles['copyright']} />}
      </div>
    );
  }

  if (formState === EPublicFormState.FormNotFound) {
    return (
      <div className={classnames(styles['notification'], type === 'embedded' && styles['embedded'])}>
        {type !== 'embedded' && (
          <img
            className={styles['notification__image']}
            src={ErrorImage}
            alt={formatMessage({ id: 'public-form.error-title' })}
          />
        )}
        <Header className={styles['notification__title']} size="2" tag="h1">
          {formatMessage({ id: 'public-form.error-title' })}
        </Header>
        <p className={styles['notification__text']}>{formatMessage({ id: 'public-form.error-text' })}</p>
        {type === 'embedded' && <Copyright className={styles['copyright']} />}
      </div>
    );
  }

  if (!publicForm) {
    return null;
  }

  const isCompleteDisabled = [
    formState !== EPublicFormState.WaitingForAction,
    !checkExtraFieldsAreValid(publicForm?.kickoff.fields),
    publicForm?.kickoff.fieldsets?.some((fieldset) => !checkExtraFieldsAreValid(fieldset.fields)),
    publicForm?.showCaptcha && !captcha,
  ].some(Boolean);

  const classNamesByTypeMap: Record<typeof type, string> = {
    shared: styles['shared'],
    embedded: styles['embedded'],
  };

  return (
    <div className={classnames(styles['kikcoff-form'], classNamesByTypeMap[type])}>
      <Header className={styles['name']} size="4" tag="h1">
        {publicForm.name}
      </Header>

      <p className={styles['description']}>
        {publicForm.kickoff.description ? (
          <RichText text={publicForm.kickoff.description} />
        ) : (
          formatMessage({ id: 'public-form.form-hint' })
        )}
      </p>

      <div className={classnames(styles['kikcoff-form__inner'], classNamesByTypeMap[type])}>
        {renderOutputFields()}

        <Button
          disabled={isCompleteDisabled}
          isLoading={formState === EPublicFormState.Submitting}
          onClick={handleRunPublicForm}
          label={formatMessage({ id: 'public-form.launch' })}
          size="md"
          buttonStyle="yellow"
          className={styles['submit-button']}
        />

        {type === 'embedded' && <Copyright className={styles['copyright']} />}
      </div>
    </div>
  );
}
