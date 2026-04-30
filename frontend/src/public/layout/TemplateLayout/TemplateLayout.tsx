import * as React from 'react';
import { useIntl } from 'react-intl';
import { useSelector, useDispatch } from 'react-redux';
import { matchPath } from 'react-router-dom';

import { TopNavContainer } from '../../components/TopNav';
import { ReturnLink, SelectMenu } from '../../components/UI';
import { ERoutes } from '../../constants/routes';
import { fieldsetsSortingValues } from '../../constants/sortings';
import { setFieldsetsListSorting } from '../../redux/fieldsets/slice';
import { getFieldsetsSorting } from '../../redux/selectors/fieldsets';
import { EFieldsetsSorting } from '../../types/fieldset';
import { history } from '../../utils/history';
import { getLinkToTemplate } from '../../utils/routes/getLinkToTemplate';
import { getLinkToFieldsets } from '../../utils/routes/getLinkToFieldsets';

import styles from './TemplateLayout.css';

interface ITemplateLayoutProps {
  children: React.ReactNode;
}

export function TemplateLayout({ children }: ITemplateLayoutProps) {
  const { formatMessage } = useIntl();
  const dispatch = useDispatch();
  const fieldsetsSorting = useSelector(getFieldsetsSorting);
  const [pathname, setPathname] = React.useState(() => history.location.pathname);

  const handleFieldsetsSortingChange = (value: EFieldsetsSorting) => {
    dispatch(setFieldsetsListSorting(value));
  };

  React.useEffect(() => {
    const unlisten = history.listen(({ pathname: nextPathname }) => {
      setPathname(nextPathname);
    });

    return unlisten;
  }, []);

  const renderLeftContent = () => {
    const detailMatch = matchPath<{ templateId: string }>(pathname, { path: ERoutes.TemplateFieldsetDetail });
    const listMatch = matchPath<{ templateId: string }>(pathname, { path: ERoutes.TemplateFieldsets });
    const templateId = Number((detailMatch || listMatch)?.params.templateId);

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

    if (listMatch) {
      return (
        <div className={styles['navbar-left__content']}>
          <ReturnLink
            label={formatMessage({ id: 'fieldsets.back-to-template' })}
            route={getLinkToTemplate({ templateId })}
          />
          <SelectMenu
            closeOnSelect
            activeValue={fieldsetsSorting}
            values={fieldsetsSortingValues}
            toggleTextClassName={styles['sorting-toggle-text']}
            onChange={handleFieldsetsSortingChange}
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

