import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import { TITLES } from '../../constants/titles';
import {
  loadTemplates,
  loadTemplatesSystem,
  loadTemplatesSystemCategories,
  resetTemplates,
} from '../../redux/actions';
import { getIsAdmin } from '../../redux/selectors/user';
import { TemplatesUser } from './TemplatesUser';
import { TemplatesSystem } from './TemplatesSystem';

import styles from './Templates.css';

export function Templates() {
  const dispatch = useDispatch();
  const isAdmin = useSelector(getIsAdmin);

  useEffect(() => {
    document.title = TITLES.Templates;
    dispatch(loadTemplates(0));

    return () => {
      dispatch(resetTemplates());
    };
  }, [dispatch]);

  useEffect(() => {
    if (!isAdmin) {
      return;
    }

    dispatch(loadTemplatesSystem());
    dispatch(loadTemplatesSystemCategories());
  }, [dispatch, isAdmin]);

  return (
    <div className={styles['container']}>
      <TemplatesUser />
      {isAdmin && <TemplatesSystem />}
    </div>
  );
}
