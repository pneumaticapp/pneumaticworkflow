export const enum EOAuthType {
  Google = 'Google',
  Microsoft = 'Microsoft',
  SSO = 'SSO',
}

export const enum ERegisterType {
  Common = 'Common',
}

export type TRegisterType = EOAuthType | ERegisterType;
