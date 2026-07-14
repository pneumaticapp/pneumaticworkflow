import * as React from 'react';

export interface IKickoffShareFormProps {
  className?: string;
}

export interface ISharedFormTabProps {
  publicUrl: string | null;
  isSuccessUrlEnabled: boolean;
  successUrl: string;
  onToggleSuccessUrl(): void;
  onChangeSuccessUrl(event: React.FormEvent<HTMLInputElement>): void;
}

export interface IEmbeddedFormTabProps {
  hasAccess: boolean;
  embedUrl: string | null;
  embedCode: string | null;
}
