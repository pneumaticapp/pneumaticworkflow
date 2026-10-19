import {
  hasTemplateIdentityChanged,
  resolveTemplateFormMountKey,
} from '../templateFormUtils';

describe('hasTemplateIdentityChanged', () => {
  it('treats create-session identity → first numeric id as the same session', () => {
    expect(hasTemplateIdentityChanged('create:/templates/create/', 42)).toBe(false);
    expect(hasTemplateIdentityChanged('create', 42)).toBe(false);
    expect(hasTemplateIdentityChanged(undefined, 42)).toBe(false);
  });

  it('detects a real switch between templates or create flows', () => {
    expect(hasTemplateIdentityChanged(42, 43)).toBe(true);
    expect(hasTemplateIdentityChanged('create:/templates/create/', 'create:/templates/create-with-ai/')).toBe(true);
  });
});

describe('resolveTemplateFormMountKey', () => {
  it('keeps the create-session key after the first autosave assigns an id', () => {
    const duringCreate = resolveTemplateFormMountKey({
      previousIdentity: undefined,
      nextIdentity: 'create:/templates/create/',
      previousCreateSessionKey: undefined,
      templateId: undefined,
    });

    expect(duringCreate).toEqual({
      mountKey: 'create:/templates/create/',
      createSessionKey: 'create:/templates/create/',
    });

    const afterFirstSave = resolveTemplateFormMountKey({
      previousIdentity: 'create:/templates/create/',
      nextIdentity: 42,
      previousCreateSessionKey: duringCreate.createSessionKey,
      templateId: 42,
    });

    expect(afterFirstSave).toEqual({
      mountKey: 'create:/templates/create/',
      createSessionKey: 'create:/templates/create/',
    });
  });

  it('clears the create-session key when navigating to another template', () => {
    const afterNavigate = resolveTemplateFormMountKey({
      previousIdentity: 42,
      nextIdentity: 43,
      previousCreateSessionKey: 'create:/templates/create/',
      templateId: 43,
    });

    expect(afterNavigate).toEqual({
      mountKey: 43,
      createSessionKey: undefined,
    });
  });

  it('changes the mount key when switching create flows', () => {
    const afterSwitch = resolveTemplateFormMountKey({
      previousIdentity: 'create:/templates/create/',
      nextIdentity: 'create:/templates/create-with-ai/',
      previousCreateSessionKey: 'create:/templates/create/',
      templateId: undefined,
    });

    expect(afterSwitch).toEqual({
      mountKey: 'create:/templates/create-with-ai/',
      createSessionKey: 'create:/templates/create-with-ai/',
    });
  });

  it('uses the template id for an existing template with no create session', () => {
    expect(
      resolveTemplateFormMountKey({
        previousIdentity: 5,
        nextIdentity: 5,
        previousCreateSessionKey: undefined,
        templateId: 5,
      }),
    ).toEqual({
      mountKey: 5,
      createSessionKey: undefined,
    });
  });
});
