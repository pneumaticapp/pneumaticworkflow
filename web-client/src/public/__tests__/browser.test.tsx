import * as ReactDOM from 'react-dom'
import { shallow } from 'enzyme'
import { AppContainer } from '../components/App'

jest.mock('../utils/getConfig', () => ({
  getBrowserConfigEnv: () => ({ api: { urls: {} } }),
  getBrowserConfig: () => ({
    googleAuthUserInfo: {},
    invitedUser: {},
  }),
}))
jest.mock('../redux/store')
jest.mock('react-dom')

describe('browser', () => {
  it('рендерит приложение при импорте', () => {
    const render = ReactDOM.render as jest.Mock

    const domSpy = jest
      .spyOn(document, 'getElementById')
      .mockReturnValue('div' as unknown as HTMLElement)

    jest.requireActual('../browser')
    const [component, element] = render.mock.calls[0]
    const childrenWrapper = shallow((component as any).props.children)

    expect(element).toEqual('div')
    expect(domSpy).toHaveBeenCalledWith('pneumatic-frontend')
    expect(childrenWrapper.exists(AppContainer)).toEqual(true)
  })
})
