import React, { useEffect } from 'react';
import { useDispatch } from 'react-redux';

import { GeneralLoader } from '../GeneralLoader';
import { collectPaymentDetails } from '../../redux/actions';

export function CollectPaymentDetails() {
  const dispatch = useDispatch();

  useEffect(() => {
    dispatch(collectPaymentDetails())
  }, []);

  return (
    <GeneralLoader />
  );
}
