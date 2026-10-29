import * as React from 'react';
import { useCallback, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import classnames from 'classnames';

import { ITemplateClient } from '../../../types/template';
import { IAuthUser, ETemplateStatus } from '../../../types/redux';
import { TUserListItem } from '../../../types/user';
import { useTemplateEditorController } from '../../../hooks/useTemplateEditorController';
import { selectIsGraphCanvas, selectTemplateSelectedTaskApiName } from '../../../redux/selectors/templateGraphView';
import { setSelectedTask } from '../../../redux/templateGraphView/slice';
import { AutoSaveStatusContainer } from '../AutoSaveStatus';
import { ConditionsBanner } from '../ConditionsBanner';
import { TemplateSettings } from '../TemplateSettings';
import { TemplateLeavingGuard } from '../TemplateLeavingGuard';
import { TemplateLineEditorView } from '../TemplateLineEditorView/TemplateLineEditorView';
import { TemplateGraphEditorView } from '../TemplateGraphEditorView/TemplateGraphEditorView';

import styles from '../TemplateEdit.css';

export interface ITemplateEditorContainerProps {
  template: ITemplateClient;
  authUser: IAuthUser;
  users: TUserListItem[];
  isSubscribed: boolean;
  accessConditions: boolean;
  shouldOpenFirstTask: boolean;
  saveTemplate(): void;
  setTemplate(payload: ITemplateClient): void;
  setTemplateStatus(status: ETemplateStatus): void;
}

export function TemplateEditorContainer({
  template,
  authUser,
  users,
  isSubscribed,
  accessConditions,
  shouldOpenFirstTask,
  saveTemplate,
  setTemplate,
  setTemplateStatus,
}: ITemplateEditorContainerProps) {
  const dispatch = useDispatch();
  const isGraphCanvas = useSelector(selectIsGraphCanvas);
  const selectedTaskApiName = useSelector(selectTemplateSelectedTaskApiName);
  const [isTemplateDeleted, setIsTemplateDeleted] = useState(false);

  const handleTemplateDeleted = useCallback((): void => {
    setIsTemplateDeleted(true);
  }, []);

  const selectTask = useCallback(
    (apiName: string | null): void => {
      dispatch(setSelectedTask(apiName));
    },
    [dispatch],
  );

  const controller = useTemplateEditorController({
    template,
    authUser,
    accessConditions,
    shouldOpenFirstTask,
    selectedTaskApiName,
    saveTemplate,
    setTemplate,
    setTemplateStatus,
    setSelectedTask: selectTask,
  });

  return (
    <div className={classnames(styles['container'], isGraphCanvas && styles['container--graph'])}>
      <AutoSaveStatusContainer onRetry={saveTemplate} />
      <TemplateLeavingGuard isTemplateDeleted={isTemplateDeleted} />

      <div className={classnames(styles['template-wrapper'], isGraphCanvas && styles['template-wrapper--graph'])}>
        <div className={styles['template-wrapper__info']}>
          <TemplateSettings onTemplateDeleted={handleTemplateDeleted} />
        </div>
        <div className={styles['template-wrapper__tasks']}>
          {!accessConditions && <ConditionsBanner />}
          {isGraphCanvas ? (
            <TemplateGraphEditorView
              template={template}
              users={users}
              selectedTaskApiName={selectedTaskApiName}
              controller={controller}
              selectTask={selectTask}
            />
          ) : (
            <TemplateLineEditorView users={users} isSubscribed={isSubscribed} controller={controller} />
          )}
        </div>
      </div>
    </div>
  );
}
