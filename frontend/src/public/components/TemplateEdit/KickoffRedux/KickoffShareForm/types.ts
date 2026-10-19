import type { FormEvent } from 'react';

export interface IKickoffShareFormProps {
  className?: string;
}

export interface ISharedFormTabProps {
  publicUrl: string | null;
  isSuccessUrlEnabled: boolean;
  successUrl: string;
  onToggleSuccessUrl(): void;
  onChangeSuccessUrl(event: FormEvent<HTMLInputElement>): void;
}

export interface IEmbeddedFormTabProps {
  hasAccess: boolean;
  embedUrl: string | null;
  embedCode: string | null;
}
