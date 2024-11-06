/* eslint-disable */
/* prettier-ignore */
import * as React from 'react';
import { useIntl } from 'react-intl';
import ReCAPTCHA from 'react-google-recaptcha';
import produce from 'immer';
import classnames from 'classnames';
import { useDispatch } from 'react-redux';

import { NotificationManager } from '../../../UI/Notifications';
import { ExtraFieldIntl } from '../../../TemplateEdit/ExtraFields';
import { EExtraFieldMode, IExtraField } from '../../../../types/template';
import { Button } from '../../../UI/Buttons/Button';
import { getEditedFields } from '../../../TemplateEdit/ExtraFields/utils/getEditedFields';
import { EInputNameBackgroundColor } from '../../../../types/workflow';
import { getPublicForm } from '../../../../api/getPublicForm';
import { EPublicFormState, IPublicForm } from '../types';
import { logger } from '../../../../utils/logger';
import { runPublicForm } from '../../../../api/runPublicForm';
import { checkExtraFieldsAreValid } from '../../../WorkflowEditPopup/utils/areKickoffFieldsValid';
import { ExtraFieldsHelper } from '../../../TemplateEdit/ExtraFields/utils/ExtraFieldsHelper';
import { getNormalizedKickoff } from '../../../../utils/mappers';
import { Header } from '../../../UI/Typeography/Header';
import { getPublicFormConfig } from '../../../../utils/getConfig';
import { deleteRemovedFilesFromFields } from '../../../../api/deleteRemovedFilesFromFields';
import { RichText } from '../../../RichText';
import { usersFetchStarted } from '../../../../redux/actions';
import { TPublicFormType } from '../../../../types/publicForms';
import { Copyright } from '../Copyright';
import { FormSkeleton } from '../FormSkeleton';
import { useShouldHideIntercom } from '../../../../hooks/useShouldHideIntercom';
import { prependHttp } from '../../../../utils/prependHttp';

import submitedImage from '../images/SubmitedImage.svg';
import * as ErrorImage from '../images/ErrorImage.svg';

import styles from './PublicForm.css';

import '../../../../assets/fonts/simple-line-icons/css/simple-line-icons.css';
import '../../../../assets/fonts/iconsmind-s/css/iconsminds.css';
import '../../../../assets/css/vendor/bootstrap.min.css';
import '../../../../assets/css/sass/themes/gogo.light.yellow.scss';
import 'react-perfect-scrollbar/dist/css/styles.css';
import 'rc-switch/assets/index.css';
import { isEnvCaptcha } from '../../../../constants/enviroment';

interface IPublicFormsAppProps {
  type: TPublicFormType;
}

export function PublicForm({ type }: IPublicFormsAppProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();

  const [formState, setFormState] = React.useState<EPublicFormState>(EPublicFormState.WaitingForAction);
  const [publicForm, setPublicForm] = React.useState<IPublicForm | null>(null);
  const [captcha, setCaptcha] = React.useState('');
  useShouldHideIntercom();

  React.useEffect(() => {
    dispatch(usersFetchStarted({ showErrorNotification: false }));
    fetchPublicForm();
  }, []);

  const fetchPublicForm = async () => {
    try {
      setFormState(EPublicFormState.Loading);

      const publicForm = await getPublicForm();

      if (!publicForm) {
        setFormState(EPublicFormState.FormNotFound);

        return;
      }

      const normalizedForm = produce(publicForm, (draftPublicForm) => {
        draftPublicForm.kickoff.fields = new ExtraFieldsHelper(publicForm.kickoff.fields).getFieldsWithValues();
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

      await deleteRemovedFilesFromFields(publicForm.kickoff.fields);
      const normalizedKickoffFileds = getNormalizedKickoff(publicForm.kickoff);
      const runFormResult = await runPublicForm(captcha, normalizedKickoffFileds);

      if (runFormResult?.redirectUrl) {
        window.location.replace(prependHttp(runFormResult?.redirectUrl));

        return;
      }

      setFormState(EPublicFormState.Submitted);
    } catch (error) {
      NotificationManager.error({ message: 'public-form.submit-failed' });
      logger.error('Failed to run public form', error);
      setFormState(EPublicFormState.WaitingForAction);
    }
  };

  const handleEditField = (apiName: string) => (changedProps: Partial<IExtraField>) => {
    setPublicForm((prevPublicForm) => {
      if (!prevPublicForm) {
        return prevPublicForm;
      }

      const oldFields = prevPublicForm.kickoff.fields;
      const newFields = getEditedFields(oldFields, apiName, changedProps);

      const newPublicForm = produce(prevPublicForm, (draftPublicForm) => {
        if (draftPublicForm) {
          draftPublicForm.kickoff.fields = newFields;
        }
      });

      return newPublicForm;
    });
  };

  const renderOutputFields = () => {
    if (!publicForm) {
      return null;
    }

    const {
      config: { reсaptchaSecret },
    } = getPublicFormConfig();

    return (
      <>
        {publicForm.kickoff.fields.map((field) => (
          <ExtraFieldIntl
            key={field.apiName}
            field={field}
            editField={handleEditField(field.apiName)}
            showDropdown={false}
            mode={EExtraFieldMode.ProcessRun}
            labelBackgroundColor={EInputNameBackgroundColor.OrchidWhite}
            namePlaceholder={field.name}
            descriptionPlaceholder={field.description}
            wrapperClassName={styles['output__field']}
            accountId={publicForm.accountId}
          />
        ))}

        {isEnvCaptcha && publicForm?.showCaptcha && (
          <div className={styles['captcha']}>
            <ReCAPTCHA
              sitekey={reсaptchaSecret}
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
