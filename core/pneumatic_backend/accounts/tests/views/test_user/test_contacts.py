import pytest
from pneumatic_backend.accounts.tests.fixtures import (
    create_test_user,
    create_test_account
)
from pneumatic_backend.accounts.enums import (
    UserStatus,
    SourceType,
)
from pneumatic_backend.accounts.models import (
    Contact,
)


pytestmark = pytest.mark.django_db


def test_contacts__default_ordering__ok(api_client):

    # arrange
    user = create_test_user()
    contact_1 = Contact.objects.create(
        account=user.account,
        first_name='First A',
        last_name='Last B',
        photo='https://site.com/image.png',
        job_title='Hard worker',
        source=SourceType.MICROSOFT,
        source_id='1as23rioweqe!',
        email='contact1@mail.ru',
        user=user,
    )
    contact_2 = Contact.objects.create(
        account=user.account,
        first_name='First B',
        last_name='Last A',
        job_title='',
        source=SourceType.GOOGLE,
        source_id='1as23rioweqe!',
        email='contact2@mail.ru',
        user=user,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/user/contacts')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    data_1 = response.data[0]
    assert data_1['id'] == contact_2.id
    assert data_1['first_name'] == contact_2.first_name
    assert data_1['last_name'] == contact_2.last_name
    assert data_1['photo'] == contact_2.photo
    assert data_1['email'] == contact_2.email
    assert data_1['job_title'] == contact_2.job_title
    assert data_1['source'] == contact_2.source

    data_2 = response.data[1]
    assert data_2['id'] == contact_1.id
    assert data_2['first_name'] == contact_1.first_name
    assert data_2['last_name'] == contact_1.last_name
    assert data_2['photo'] == contact_1.photo
    assert data_2['email'] == contact_1.email
    assert data_2['job_title'] == contact_1.job_title
    assert data_2['source'] == contact_1.source


def test_contacts__inactive_contact__skip(api_client):

    # arrange
    user = create_test_user()
    Contact.objects.create(
        account=user.account,
        first_name='First A',
        last_name='Last B',
        photo='https://site.com/image.png',
        job_title='Hard worker',
        source=SourceType.MICROSOFT,
        source_id='1as23rioweqe!',
        email='contact1@mail.ru',
        user=user,
        status=UserStatus.INACTIVE
    )
    contact_2 = Contact.objects.create(
        account=user.account,
        first_name='First B',
        last_name='Last A',
        job_title='',
        source=SourceType.GOOGLE,
        source_id='1as23rioweqe!',
        email='contact2@mail.ru',
        user=user,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/user/contacts')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    data_1 = response.data[0]
    assert data_1['id'] == contact_2.id


def test_contacts__another_user_contact__skip(api_client):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    another_user = create_test_user(
        account=account,
        email='another@test.test'
    )
    Contact.objects.create(
        account=user.account,
        first_name='First A',
        last_name='Last B',
        photo='https://site.com/image.png',
        job_title='Hard worker',
        source=SourceType.MICROSOFT,
        source_id='1as23rioweqe!',
        email='contact1@mail.ru',
        user=another_user,
    )
    contact_2 = Contact.objects.create(
        account=user.account,
        first_name='First B',
        last_name='Last A',
        job_title='',
        source=SourceType.GOOGLE,
        source_id='1as23rioweqe!',
        email='contact2@mail.ru',
        user=user,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/user/contacts')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    data_1 = response.data[0]
    assert data_1['id'] == contact_2.id


def test_contacts__not_exist__empty_list(api_client):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/user/contacts')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_contacts__not_authenticated__permission_denied(api_client):

    # arrange

    # act
    response = api_client.get('/accounts/user/contacts')

    # assert
    assert response.status_code == 401


def test_contacts__search_first_name__ok(api_client):

    # arrange
    user = create_test_user()
    contact_1 = Contact.objects.create(
        account=user.account,
        first_name='Joanna De lee',
        last_name='Last B',
        photo='https://site.com/image.png',
        job_title='Hard worker',
        source=SourceType.MICROSOFT,
        source_id='1as23rioweqe!',
        email='contact1@mail.ru',
        user=user,
    )
    Contact.objects.create(
        account=user.account,
        first_name='DoLee',
        last_name='Last A',
        job_title='',
        source=SourceType.GOOGLE,
        source_id='1as23rioweqe!',
        email='contact2@mail.ru',
        user=user,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/user/contacts?search=De lee')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == contact_1.id


def test_contacts__search_last_name__ok(api_client):

    # arrange
    user = create_test_user()
    contact_1 = Contact.objects.create(
        account=user.account,
        first_name='Joanna De lee',
        last_name='Tony Blondette',
        photo='https://site.com/image.png',
        job_title='Hard worker',
        source=SourceType.MICROSOFT,
        source_id='1as23rioweqe!',
        email='contact1@mail.ru',
        user=user,
    )
    Contact.objects.create(
        account=user.account,
        first_name='Donald',
        last_name='Tomas',
        job_title='',
        source=SourceType.GOOGLE,
        source_id='1as23rioweqe!',
        email='contact2@mail.ru',
        user=user,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/user/contacts?search=Tony Blond')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == contact_1.id


def test_contacts__search_job_title__ok(api_client):

    # arrange
    user = create_test_user()
    contact_1 = Contact.objects.create(
        account=user.account,
        first_name='Joanna De lee',
        last_name='Tony Blondette',
        photo='https://site.com/image.png',
        job_title='QA Engeener',
        source=SourceType.MICROSOFT,
        source_id='1as23rioweqe!',
        email='contact1@mail.ru',
        user=user,
    )
    Contact.objects.create(
        account=user.account,
        first_name='Donald',
        last_name='Tomas',
        job_title='Interior Designer',
        source=SourceType.GOOGLE,
        source_id='1as23rioweqe!',
        email='contact2@mail.ru',
        user=user,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/user/contacts?search=QA')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == contact_1.id


def test_contacts__search_email__ok(api_client):

    # arrange
    user = create_test_user()
    contact_1 = Contact.objects.create(
        account=user.account,
        first_name='Joanna De lee',
        last_name='Tony Blondette',
        photo='https://site.com/image.png',
        job_title='QA Engeener',
        source=SourceType.MICROSOFT,
        source_id='1as23rioweqe!',
        email='contact1@mail.ru',
        user=user,
    )
    Contact.objects.create(
        account=user.account,
        first_name='Donald',
        last_name='Tomas',
        job_title='Interior Designer',
        source=SourceType.GOOGLE,
        source_id='1as23rioweqe!',
        email='contact2@gmail.com',
        user=user,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/accounts/user/contacts?search=contact1')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == contact_1.id


def test_contacts__ordering__last_name__ok(api_client):

    # arrange
    user = create_test_user()
    contact_1 = Contact.objects.create(
        account=user.account,
        first_name='First A',
        last_name='B',
        photo='https://site.com/image.png',
        job_title='Hard worker',
        source=SourceType.MICROSOFT,
        source_id='1as23rioweqe!',
        email='contact1@mail.ru',
        user=user,
    )
    contact_2 = Contact.objects.create(
        account=user.account,
        first_name='First B',
        last_name='A',
        job_title='',
        source=SourceType.GOOGLE,
        source_id='1as23rioweqe!',
        email='contact2@mail.ru',
        user=user,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/accounts/user/contacts?ordering=last_name'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == contact_2.id
    assert response.data[1]['id'] == contact_1.id


def test_contacts__ordering__last_name_reversed__ok(api_client):
    # arrange
    user = create_test_user()
    contact_1 = Contact.objects.create(
        account=user.account,
        first_name='First A',
        last_name='B',
        photo='https://site.com/image.png',
        job_title='Hard worker',
        source=SourceType.MICROSOFT,
        source_id='1as23rioweqe!',
        email='contact1@mail.ru',
        user=user,
    )
    contact_2 = Contact.objects.create(
        account=user.account,
        first_name='First B',
        last_name='A',
        job_title='',
        source=SourceType.GOOGLE,
        source_id='1as23rioweqe!',
        email='contact2@mail.ru',
        user=user,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/accounts/user/contacts?ordering=-last_name'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == contact_1.id
    assert response.data[1]['id'] == contact_2.id


def test_contacts__ordering__first_name__ok(api_client):

    # arrange
    user = create_test_user()
    contact_1 = Contact.objects.create(
        account=user.account,
        first_name='A',
        last_name='last name',
        photo='https://site.com/image.png',
        job_title='Hard worker',
        source=SourceType.MICROSOFT,
        source_id='1as23rioweqe!',
        email='contact1@mail.ru',
        user=user,
    )
    contact_2 = Contact.objects.create(
        account=user.account,
        first_name='B',
        last_name='last name',
        job_title='',
        source=SourceType.GOOGLE,
        source_id='1as23rioweqe!',
        email='contact2@mail.ru',
        user=user,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/accounts/user/contacts?ordering=first_name'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == contact_1.id
    assert response.data[1]['id'] == contact_2.id


def test_contacts__ordering__first_name_reversed__ok(api_client):

    # arrange
    user = create_test_user()
    contact_1 = Contact.objects.create(
        account=user.account,
        first_name='A',
        last_name='last name',
        photo='https://site.com/image.png',
        job_title='Hard worker',
        source=SourceType.MICROSOFT,
        source_id='1as23rioweqe!',
        email='contact1@mail.ru',
        user=user,
    )
    contact_2 = Contact.objects.create(
        account=user.account,
        first_name='B',
        last_name='last name',
        job_title='',
        source=SourceType.GOOGLE,
        source_id='1as23rioweqe!',
        email='contact2@mail.ru',
        user=user,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/accounts/user/contacts?ordering=-first_name'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == contact_2.id
    assert response.data[1]['id'] == contact_1.id


def test_contacts__ordering__source__ok(api_client):

    # arrange
    user = create_test_user()
    contact_1 = Contact.objects.create(
        account=user.account,
        first_name='first name',
        last_name='last name',
        photo='https://site.com/image.png',
        job_title='Hard worker',
        source=SourceType.MICROSOFT,
        source_id='1as23rioweqe!',
        email='contact1@mail.ru',
        user=user,
    )
    contact_2 = Contact.objects.create(
        account=user.account,
        first_name='first name',
        last_name='last name',
        job_title='',
        source=SourceType.GOOGLE,
        source_id='1as23rioweqe!',
        email='contact2@mail.ru',
        user=user,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/accounts/user/contacts?ordering=source'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == contact_2.id
    assert response.data[1]['id'] == contact_1.id


def test_contacts__ordering__source_reversed__ok(api_client):

    # arrange
    user = create_test_user()
    contact_1 = Contact.objects.create(
        account=user.account,
        first_name='first name',
        last_name='last name',
        photo='https://site.com/image.png',
        job_title='Hard worker',
        source=SourceType.MICROSOFT,
        source_id='1as23rioweqe!',
        email='contact1@mail.ru',
        user=user,
    )
    contact_2 = Contact.objects.create(
        account=user.account,
        first_name='first name',
        last_name='last name',
        job_title='',
        source=SourceType.GOOGLE,
        source_id='1as23rioweqe!',
        email='contact2@mail.ru',
        user=user,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/accounts/user/contacts?ordering=-source'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == contact_1.id
    assert response.data[1]['id'] == contact_2.id


def test_contacts__ordering__multiple_values__ok(api_client):

    # arrange
    user = create_test_user()
    contact_1 = Contact.objects.create(
        account=user.account,
        first_name='B',
        last_name='last name',
        photo='https://site.com/image.png',
        job_title='Hard worker',
        source=SourceType.MICROSOFT,
        source_id='1as23rioweqe!',
        email='contact1@mail.ru',
        user=user,
    )
    contact_2 = Contact.objects.create(
        account=user.account,
        first_name='A',
        last_name='last name',
        job_title='',
        source=SourceType.GOOGLE,
        source_id='1as23rioweqe!',
        email='contact2@mail.ru',
        user=user,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/accounts/user/contacts?ordering=-source,first_name'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == contact_1.id
    assert response.data[1]['id'] == contact_2.id


def test_contacts__filter_source__ok(api_client):

    # arrange
    user = create_test_user()
    Contact.objects.create(
        account=user.account,
        first_name='Joanna De lee',
        last_name='Last B',
        photo='https://site.com/image.png',
        job_title='Hard worker',
        source=SourceType.MICROSOFT,
        source_id='1as23rioweqe!',
        email='contact1@mail.ru',
        user=user,
    )
    contact_2 = Contact.objects.create(
        account=user.account,
        first_name='DoLee',
        last_name='Last A',
        job_title='',
        source=SourceType.GOOGLE,
        source_id='1as23rioweqe!',
        email='contact2@mail.ru',
        user=user,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        f'/accounts/user/contacts?source={SourceType.GOOGLE}'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == contact_2.id


def test_contacts__pagination__ok(api_client):

    # arrange
    user = create_test_user()
    contact_1 = Contact.objects.create(
        account=user.account,
        first_name='First name',
        last_name='B',
        photo='https://site.com/image.png',
        job_title='Hard worker',
        source=SourceType.MICROSOFT,
        source_id='1as23rioweqe!',
        email='contact1@mail.ru',
        user=user,
    )
    contact_2 = Contact.objects.create(
        account=user.account,
        first_name='First name',
        last_name='C',
        job_title='',
        source=SourceType.GOOGLE,
        source_id='1as23rioweqe!',
        email='contact2@mail.ru',
        user=user,
    )
    Contact.objects.create(
        account=user.account,
        first_name='First name',
        last_name='A',
        job_title='',
        source=SourceType.EMAIL,
        source_id='1as23rioweqe!',
        email='contact3@mail.ru',
        user=user,
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(
        '/accounts/user/contacts?limit=2&offset=1'
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['results']) == 2
    assert response.data['results'][0]['id'] == contact_1.id
    assert response.data['results'][1]['id'] == contact_2.id
    assert response.data['count'] == 3
    assert response.data['next'] is None
    assert response.data['previous'] is not None
