import { useEffect, useRef } from 'react';
import { useFormikContext } from 'formik';
import { useDispatch, useSelector } from 'react-redux';

import { loadAIProviderModels } from '../../../../redux/ai/slice';
import {
  getAIProviderModelsList,
  getAIProviderModelsProviderId,
  getAIProvidersList,
} from '../../../../redux/selectors/ai';
import type { IAIAgentFormValues } from './types';

export function useProviderModelsSync() {
  const dispatch = useDispatch();
  const providers = useSelector(getAIProvidersList);
  const modelsProviderId = useSelector(getAIProviderModelsProviderId);
  const models = useSelector(getAIProviderModelsList);
  const { values, setFieldValue } = useFormikContext<IAIAgentFormValues>();
  const prevProviderIdRef = useRef(values.providerId);
  const modelsRequestedForRef = useRef('');

  useEffect(() => {
    if (!values.providerId && providers.length === 1) {
      setFieldValue('providerId', String(providers[0].id));
    }
  }, [values.providerId, providers, setFieldValue]);

  useEffect(() => {
    if (!values.providerId) return;

    if (values.providerId !== prevProviderIdRef.current && values.model) {
      setFieldValue('model', '');
    }
    prevProviderIdRef.current = values.providerId;

    if (modelsProviderId !== Number(values.providerId) && modelsRequestedForRef.current !== values.providerId) {
      modelsRequestedForRef.current = values.providerId;
      dispatch(loadAIProviderModels(Number(values.providerId)));
    }
  }, [values.providerId, values.model, modelsProviderId, dispatch, setFieldValue]);

  useEffect(() => {
    const isCurrentProviderModels = modelsProviderId === Number(values.providerId);

    if (values.providerId && !values.model && isCurrentProviderModels && models.length > 0) {
      setFieldValue('model', models[0].slug);
    }
  }, [values.providerId, values.model, modelsProviderId, models, setFieldValue]);
}
