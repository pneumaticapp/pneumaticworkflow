import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import { loadCurrentFieldset, resetCurrentFieldset } from '../../../redux/fieldsets/slice';
import { getCurrentFieldset, isCurrentFieldsetLoading } from '../../../redux/selectors/fieldsets';
import { history } from '../../../utils/history';
import { ERoutes } from '../../../constants/routes';

import { FieldsetDetailsSkeleton } from './FieldsetDetailsSkeleton';
import { FieldsetDetailsForm } from './FieldsetDetailsForm';
import type { TFieldsetDetailsProps } from './types';

const FieldsetDetails = ({
  match: {
    params: { id: matchParamId },
  },
}: TFieldsetDetailsProps) => {
  const dispatch = useDispatch();
  const fieldset = useSelector(getCurrentFieldset);
  const isLoading = useSelector(isCurrentFieldsetLoading);

  useEffect(() => {
    const id = Number(matchParamId);

    if (Number.isNaN(id)) {
      history.push(ERoutes.Fieldsets);
      return;
    }

    if (fieldset?.id === id) return;
    dispatch(loadCurrentFieldset({ id }));
  }, [matchParamId]);

  useEffect(
    () => () => {
      dispatch(resetCurrentFieldset());
    },
    [],
  );

  if (isLoading) {
    return <FieldsetDetailsSkeleton />;
  }

  if (!fieldset) {
    return null;
  }

  return <FieldsetDetailsForm key={fieldset.id} fieldset={fieldset} />;
};

export default FieldsetDetails;
