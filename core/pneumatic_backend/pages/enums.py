

class PageType:

    SIGNIN = 'signin'
    SIGNUP = 'signup'
    SIGNUP_BY_INVITE = 'signup-by-invite'
    RESET_PASSWORD = 'reset-password'
    FORGOT_PASSWORD = 'forgot-password'

    CHOICES = (
        (SIGNIN, 'Sign in'),
        (SIGNUP, 'Sign up'),
        (SIGNUP_BY_INVITE, 'Sign up by invite'),
        (RESET_PASSWORD, 'Reset password'),
        (FORGOT_PASSWORD, 'Forgot password'),
    )

    PUBLIC_TYPES = {
        SIGNIN,
        SIGNUP,
        SIGNUP_BY_INVITE,
        RESET_PASSWORD,
        FORGOT_PASSWORD,
    }
