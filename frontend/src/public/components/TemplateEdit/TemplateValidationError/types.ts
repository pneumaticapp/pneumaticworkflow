import type { ETaskFormParts } from '../types';

export interface ITemplateValidationErrorProps {
  apiNames: string[];
  section?: ETaskFormParts | null;
  className?: string;
}
