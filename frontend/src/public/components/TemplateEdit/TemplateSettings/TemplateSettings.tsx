import React, { useState } from 'react';
import { useIntl } from 'react-intl';
import StickyBox from 'react-sticky-box';

import { EditableText } from '../../UI';
import { NAVBAR_HEIGHT } from '../../../constants/defaultValues';
import { ITemplate } from '../../../types/template';
import { TemplateControllsContainer } from '../TemplateControlls';
import { isArrayWithItems } from '../../../utils/helpers';
import { IInfoWarningProps, InfoWarningsModal } from '../InfoWarningsModal';
import { TemplateLastUpdateInfo } from '../TemplateLastUpdateInfo';
import { RichEditor } from '../../RichEditor';
import { useTemplateField } from '../useTemplateForm';

import styles from './TemplateSettings.css';

export function TemplateSettings() {
  const { formatMessage } = useIntl();
  const { values, setFieldValue } = useTemplateField();
  const [isInfoWarningsModaOpen, setIsInfoWarningsModaOpen] = useState(false);
  const [infoWarnings, setInfoWarnings] = useState<any>([]);

  const handleChangeTemplateField = (field: keyof ITemplate) => (value: ITemplate[keyof ITemplate]) => {
    setFieldValue(field as string, value, false);
  };

  const handleChangeTextField = (field: keyof ITemplate) => (value: string) => handleChangeTemplateField(field)(value);

  const handleSetInfoWarnings = (infoWarningsLocal: ((props: IInfoWarningProps) => JSX.Element)[]) => {
    if (isArrayWithItems(infoWarningsLocal)) {
      setIsInfoWarningsModaOpen(true);
      setInfoWarnings(infoWarningsLocal);
    }
  };

  const renderInfoWarningsModal = () => {
    const handleCloseModal = () => setIsInfoWarningsModaOpen(false);

    return <InfoWarningsModal isOpen={isInfoWarningsModaOpen} onClose={handleCloseModal} warnings={infoWarnings} />;
  };

  return (
    <>
      {renderInfoWarningsModal()}
      <StickyBox offsetTop={NAVBAR_HEIGHT} offsetBottom={20}>
        <EditableText
          text={values.name}
          className={styles['template-name']}
          onChangeText={handleChangeTextField('name')}
          placeholder={formatMessage({ id: 'template.name-placeholder' })}
          editButtonHint={formatMessage({ id: 'template.edit-name' })}
        />
        <div className={styles['description']}>
          <RichEditor
            key={values.id ?? 'new'}
            withToolbar={false}
            withMentions={false}
            placeholder={formatMessage({ id: 'template.placeholder' })}
            className={styles['description-editor']}
            defaultValue={values.description ?? ''}
            handleChange={(value) => {
              handleChangeTextField('description')(value);
              return Promise.resolve(value);
            }}
          />
        </div>

        <TemplateControllsContainer setInfoWarnings={handleSetInfoWarnings} />

        {(values.updatedBy || values.dateUpdated) && (
          <div className={styles['last-update']}>
            <TemplateLastUpdateInfo updatedBy={values.updatedBy} dateUpdated={values.dateUpdated} />
          </div>
        )}
      </StickyBox>
    </>
  );
}
