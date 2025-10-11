from src.authentication.views.verification import (
    VerificationTokenView,
    VerificationTokenResendView,
)
from src.authentication.views.password import (
    ChangePasswordView,
    ResetPasswordViewSet,
)
from src.authentication.views.google import (
    SignInWithGoogleView,
    GoogleAuthViewSet,
)
from src.authentication.views.signin import (
    TokenObtainPairCustomView,
    SuperuserEmailTokenView,
)
from src.authentication.views.signup import (
    SignUpView,
)
from src.authentication.views.context import (
    ContextUserView,
)
from src.authentication.views.signout import (
    SignOutView,
)
from src.authentication.views.microsoft import (
    MSAuthViewSet,
)
from src.authentication.views.auth0 import (
    Auth0ViewSet,
)
