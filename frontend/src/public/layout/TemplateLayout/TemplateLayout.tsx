import * as React from 'react';
import { useIntl } from 'react-intl';

import { TopNavContainer } from '../../components/TopNav';
import { ReturnLink } from '../../components/UI';
import { ERoutes } from '../../constants/routes';
import { history } from '../../utils/history';
import { getLinkToTemplate } from '../../utils/routes/getLinkToTemplate';

interface ITemplateLayoutProps {
  children: React.ReactNode;
}

const FIELDSETS_TEMPLATE_PATH = /^\/templates\/(\d+)\/fieldsets(?:\/|$)/;

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
    const fieldsetsMatch = FIELDSETS_TEMPLATE_PATH.exec(pathname);
    if (fieldsetsMatch) {
      const templateId = Number(fieldsetsMatch[1]);
      if (!Number.isNaN(templateId)) {
        return (
          <ReturnLink
            label={formatMessage({ id: 'fieldsets.back-to-template' })}
            route={getLinkToTemplate({ templateId })}
          />
        );
      }
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
