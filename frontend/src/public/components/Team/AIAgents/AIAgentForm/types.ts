export interface IAIAgentFormValues {
  name: string;
  providerId: string;
  model: string;
  systemPrompt: string;
  photo: string;
}

export interface IAIAgentFormProps {
  isVisible: boolean;
  isSubmitting?: boolean;
  initialValues?: IAIAgentFormValues;
  submitLabel: string;
  onSubmit(values: IAIAgentFormValues): void;
}

export interface IAIAgentFormFieldsProps {
  isSubmitting: boolean;
  submitLabel: string;
}
