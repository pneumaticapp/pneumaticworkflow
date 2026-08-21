import * as React from 'react';
import { useEffect } from 'react';
import { useIntl } from 'react-intl';
import { useSelector } from 'react-redux';
import classnames from 'classnames';

import { TopNavContainer } from '../../components/TopNav';
import { GraphViewToggle, EGraphViewMode } from '../../components/TemplateEdit/TemplateGraphEditor';
import { NavLink } from '../../components/NavLink';
import { ERoutes } from '../../constants/routes';
import { selectIsGraphCanvas, selectTemplateViewMode } from '../../redux/selectors/templateGraphView';
import templateIcon from '../../assets/img/template-20.svg';

import styles from './TemplateLayout.css';

interface ITemplateLayoutProps {
  children: React.ReactNode;
}

const GRAPH_LOCK_CLASS = 'template-graph-lock';

export function TemplateLayout({ children }: ITemplateLayoutProps) {
  const { formatMessage } = useIntl();
  const viewMode = useSelector(selectTemplateViewMode);
  const isGraphCanvas = useSelector(selectIsGraphCanvas);
  const isGraphMode = viewMode === EGraphViewMode.Graph;

  useEffect(() => {
    if (!isGraphCanvas) {
      return undefined;
    }

    const appContainer = document.getElementById('app-container');
    appContainer?.classList.add(GRAPH_LOCK_CLASS);
    document.body.classList.add(GRAPH_LOCK_CLASS);

    return () => {
      appContainer?.classList.remove(GRAPH_LOCK_CLASS);
      document.body.classList.remove(GRAPH_LOCK_CLASS);
    };
  }, [isGraphCanvas]);

  const renderLeftContent = () => {
    return (
      <div className={styles['navbar-left__content']}>
        <GraphViewToggle />
        <NavLink to={ERoutes.Templates} className={styles['all-templates']}>
          <span className={styles['all-templates__icon']}>
            <img src={templateIcon} alt="" />
          </span>
          {formatMessage({ id: 'template.all-templates' })}
        </NavLink>
      </div>
    );
  };

  return (
    <>
      <TopNavContainer leftContent={renderLeftContent()} />
      <main
        className={classnames(isGraphCanvas && styles['main--graph'])}
        data-test-id="template-layout"
        data-graph-mode={String(isGraphMode)}
      >
        <div className={classnames('container-fluid', isGraphCanvas && styles['content--graph'])}>
          {children}
        </div>
      </main>
    </>
  );
}
