import * as React from 'react';
import { useEffect } from 'react';
import { Formik } from 'formik';
import { useDispatch } from 'react-redux';

import { getErrorsObject } from '../../../../utils/formik/getErrorsObject';
import { validateRequired } from '../../../../utils/validators';
import { cancelAIAgentAvatarUpload } from '../../../../redux/ai/slice';
import { AIAgentFormFields } from './AIAgentFormFields';
import { EMPTY_AI_AGENT_FORM_VALUES } from './constants';
import type { IAIAgentFormProps } from './types';

export function CreateAIAgentForm({
  isActive,
  isSubmitting = false,
  initialValues = EMPTY_AI_AGENT_FORM_VALUES,
  submitLabel,
  onSubmit,
}: IAIAgentFormProps) {
  const dispatch = useDispatch();

  useEffect(
    () => () => {
      dispatch(cancelAIAgentAvatarUpload());
    },
    [dispatch],
  );

  return (
    <Formik
      initialValues={initialValues}
      validateOnMount
      validate={(values) =>
        getErrorsObject(values, {
          name: validateRequired,
          providerId: validateRequired,
          model: validateRequired,
          systemPrompt: validateRequired,
        })
      }
      onSubmit={onSubmit}
    >
      {isActive && <AIAgentFormFields isSubmitting={isSubmitting} submitLabel={submitLabel} />}
    </Formik>
  );
}
