import * as React from 'react';
import { useIntl } from 'react-intl';
import { matchPath } from 'react-router-dom';

import { TopNavContainer } from '../../components/TopNav';
import { ReturnLink } from '../../components/UI';
import { ERoutes } from '../../constants/routes';
import { history } from '../../utils/history';
import { getLinkToTemplate } from '../../utils/routes/getLinkToTemplate';
import { getLinkToFieldsets } from '../../utils/routes/getLinkToFieldsets';

import styles from './TemplateLayout.css';

interface ITemplateLayoutProps {
  children: React.ReactNode;
}

export function TemplateLayout({ children }: ITemplateLayoutProps) {
  const { formatMessage } = useIntl();
  const [pathname, setPathname] = React.useState(() => history.location.pathname);

  React.useEffect(() => {
    const unlisten = history.listen(({ pathname: nextPathname }) => {
      setPathname(nextPathname);
    });

    return unlisten;
  }, []);

  const renderLeftContent = () => {
    const detailMatch = matchPath<{ templateId: string }>(pathname, { path: ERoutes.TemplateFieldsetDetail });
    const templateId = Number(detailMatch?.params.templateId);

    if (detailMatch) {
      return (
        <div className={styles['breadcrumb-nav']}>
          <ReturnLink
            label={formatMessage({ id: 'fieldsets.breadcrumb.template' })}
            route={getLinkToTemplate({ templateId })}
          />
          <ReturnLink
            label={formatMessage({ id: 'fieldsets.breadcrumb.fieldsets' })}
            route={getLinkToFieldsets(templateId)}
          />
        </div>
      );
    }

    return (
      <ReturnLink
        label={formatMessage({ id: 'menu.templates' })}
        route={ERoutes.Templates}
      />
    );
  };

  return (
    <>
      <TopNavContainer leftContent={renderLeftContent()} />
      <main>
        <div className="container-fluid">
          {children}
        </div>
      </main>
    </>
  );
}

