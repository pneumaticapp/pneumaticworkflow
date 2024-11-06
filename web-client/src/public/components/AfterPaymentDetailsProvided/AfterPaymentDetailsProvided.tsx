import React, { useEffect } from 'react';
import { useDispatch } from 'react-redux';

import { GeneralLoader } from '../GeneralLoader';
import { onAfterPaymentDetailsProvided } from '../../redux/actions';

export function AfterPaymentDetailsProvided() {
  const dispatch = useDispatch();

  useEffect(() => {
    dispatch(onAfterPaymentDetailsProvided());
  }, []);

  return (
    <GeneralLoader />
  );
}