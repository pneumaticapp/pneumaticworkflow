export interface IMcpIdentity {
  user_id: string | number;
  account_id: string | number;
}

export interface IMcpConnection extends IMcpIdentity {
  id: string;
  client_name: string;
  scopes: string[];
  created_at: string;
  revoked_at: string | null;
}

export interface IMcpConsent {
  request_id: string;
  client_name: string;
  account_name: string;
  scopes: string[];
  login_complete: boolean;
  csrf_token: string;
}

export type TMcpUploadStatus = 'pending' | 'importing' | 'ready' | 'attached' | 'expired' | 'revoked' | 'failed';

export interface IMcpUploadSession extends IMcpIdentity {
  id: string;
  status: TMcpUploadStatus;
  expires_at: string;
  filename: string;
  content_type: string;
  size: number;
}

export interface IMcpUploadToken {
  access_token: string;
  upload_session_id: string;
  file_upload_url: string;
  expires_in: number;
}

export interface IMcpUploadFormValues {
  sessionId: string;
  file?: File;
}
