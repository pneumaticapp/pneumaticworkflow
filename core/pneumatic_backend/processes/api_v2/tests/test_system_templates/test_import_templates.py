import pytest
from pneumatic_backend.processes.enums import (
    SysTemplateType,
    DueDateRule,
    FieldType,
)
from pneumatic_backend.processes.models import (
    SystemTemplateCategory,
    SystemTemplate
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
)


pytestmark = pytest.mark.django_db


def test_import_templates__category_not_exists__create(api_client):

    # arrange
    user = create_test_user(is_staff=True)
    category_name = "Human Resources"
    step_name = "Establish Performance Standards"
    step_desc = "The first step of the requirements."
    template_desc = "The performance appraisal process"
    template_name = "Performance Appraisal"
    data = {
      "info": "templates with categories from 0 through 14",
      "templates": [
        {
          "title": template_name,
          "intro": template_desc,
          "sopDescription": "it well with the overall system.",
          "steps": [
            {
              "stepName": step_name,
              "stepDescription": step_desc,
              "dueIn": {
                "days": 0,
                "hours": 12,
                "minutes": 30
              }
            },
            {
              "stepName": "Communicate Expectations",
              "stepDescription": "Once the peand what is expected of them."
            },
            {
              "stepName": "Measure Actual Performance",
              "stepDescription": "This step invbservable behaviors or results."
            },
            {
              "stepName": "Compare Actual Performance with Standards",
              "stepDescription": "In this gaps."
            },
            {
              "stepName": "Discuss Appraisal with the Employee",
              "stepDescription": "Next, the manance gaps should be addressed."
            },
            {
              "stepName": "Design and Implement a Performance Plan",
              "stepDescription": "The final step invoving their performance."
            }
          ],
          "category": category_name
        },
      ]
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/templates/system/import',
        data=data
    )

    # assert
    assert response.status_code == 204
    category = SystemTemplateCategory.objects.get(name=category_name)
    assert category.order == 1
    assert not category.is_active

    sys_template = SystemTemplate.objects.get(name=template_name)
    assert sys_template.is_active is True
    assert sys_template.description == template_desc
    assert sys_template.category_id == category.id
    assert sys_template.type == SysTemplateType.LIBRARY
    template_data = sys_template.template
    assert template_data['name'] == template_name
    assert template_data['description'] == template_desc
    assert len(template_data['tasks']) == 6
    assert template_data['tasks'][0]['name'] == step_name
    assert template_data['tasks'][0]['description'] == step_desc
    assert template_data['tasks'][0]['number'] == 1
    assert template_data['tasks'][0]['api_name']
    assert template_data['tasks'][1]['number'] == 2
    raw_due_date = template_data['tasks'][0]['raw_due_date']
    assert raw_due_date['rule'] == DueDateRule.AFTER_TASK_STARTED
    assert raw_due_date['duration_months'] == 0
    assert raw_due_date['duration'] == '00 12:30:00'
    assert raw_due_date['source_id'] == template_data['tasks'][0]['api_name']


def test_import_templates__existent_category__use_existent(api_client):

    # arrange
    user = create_test_user(is_staff=True)
    category_name = "Human Resources"
    category = SystemTemplateCategory.objects.create(
        name=category_name
    )
    template_name = "Performance Appraisal"
    data = {
      "info": "templates with categories from 0 through 14",
      "templates": [
        {
          "title": template_name,
          "intro": "The performance appraisal process",
          "sopDescription": "it well with the overall system.",
          "steps": [
            {
              "stepName": "Establish Performance Standards",
              "stepDescription": "The first step of the requirements."
            },
            {
              "stepName": "Communicate Expectations",
              "stepDescription": "Once the peand what is expected of them."
            }
          ],
          "category": category_name
        },
      ]
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/templates/system/import',
        data=data
    )

    # assert
    assert response.status_code == 204
    assert SystemTemplateCategory.objects.count() == 1

    sys_template = SystemTemplate.objects.get(name=template_name)
    assert sys_template.category_id == category.id


def test_import_templates__existent_template__update(api_client):

    # arrange
    user = create_test_user(is_staff=True)
    # old data
    old_category = SystemTemplateCategory.objects.create(name='old category')
    template_name = "Performance Appraisal"
    sys_template = SystemTemplate.objects.create(
        is_active=False,
        name=template_name,
        description='Old desc',
        type=SysTemplateType.LIBRARY,
        category=old_category,
        template={
            'name': 'Old processing',
            'description': 'Old template desc',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'Checking data',
                    'number': 1,
                    'raw_due_date': {
                        'rule': DueDateRule.AFTER_WORKFLOW_STARTED,
                        'duration_months': 1,
                        'duration': '0 0:1:00',
                    }
                },
                {
                    'name': 'Finding reasons of request',
                    'number': 2,
                },
                {
                    'name': 'Responsing to client',
                    'number': 3,
                },
                {
                    'name': 'Creating report',
                    'number': 4,
                }
            ],
        }
    )
    # new data
    category_name = "Human Resources"
    step_name = "Establish Performance Standards"
    step_desc = "The first step of the requirements."
    template_desc = "The performance appraisal process"
    data = {
      "info": "templates with categories from 0 through 14",
      "templates": [
        {
          "title": template_name,
          "intro": template_desc,
          "sopDescription": "it well with the overall system.",
          "steps": [
            {
              "stepName": step_name,
              "stepDescription": step_desc,
              "dueIn": {
                  "days": 1,
                  "hours": 2,
                  "minutes": 0
              }
            },
            {
              "stepName": "Communicate Expectations",
              "stepDescription": "Once the peand what is expected of them."
            },
            {
              "stepName": "Measure Actual Performance",
              "stepDescription": "This step invbservable behaviors or results."
            },
            {
              "stepName": "Compare Actual Performance with Standards",
              "stepDescription": "In this gaps."
            },
            {
              "stepName": "Discuss Appraisal with the Employee",
              "stepDescription": "Next, the manance gaps should be addressed."
            },
            {
              "stepName": "Design and Implement a Performance Plan",
              "stepDescription": "The final step invoving their performance."
            }
          ],
          "category": category_name
        },
      ]
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/templates/system/import',
        data=data
    )

    # assert
    assert response.status_code == 204
    sys_template.refresh_from_db()
    category = SystemTemplateCategory.objects.get(name=category_name)

    assert sys_template.is_active is False
    assert sys_template.description == template_desc
    assert sys_template.category_id == category.id
    assert sys_template.type == SysTemplateType.LIBRARY
    template_data = sys_template.template
    assert template_data['name'] == template_name
    assert template_data['description'] == template_desc
    assert len(template_data['tasks']) == 6
    assert template_data['tasks'][0]['name'] == step_name
    assert template_data['tasks'][0]['description'] == step_desc
    assert template_data['tasks'][0]['number'] == 1
    assert template_data['tasks'][0]['api_name']
    raw_due_date = template_data['tasks'][0]['raw_due_date']
    assert raw_due_date['rule'] == DueDateRule.AFTER_TASK_STARTED
    assert raw_due_date['duration_months'] == 0
    assert raw_due_date['duration'] == '01 02:00:00'
    assert raw_due_date['source_id'] == template_data['tasks'][0]['api_name']


def test_import_templates__not_library_type__not_update(api_client):

    # arrange
    user = create_test_user(is_staff=True)
    # old data
    name = 'another name'
    desc = 'another desc'
    another_category = SystemTemplateCategory.objects.create(
        name='another category'
    )
    step_name = 'Another first step'
    step_desc = 'Another step desc'
    another_sys_template = SystemTemplate.objects.create(
        is_active=True,
        name=name,
        description=desc,
        type=SysTemplateType.ACTIVATED,
        category=another_category,
        template={
            'name': name,
            'description': desc,
            'kickoff': {},
            'tasks': [
                {
                    'name': step_name,
                    'description': step_desc,
                    'number': 1,
                },
                {
                    'name': 'Finding reasons of request',
                    'number': 2,
                },
                {
                    'name': 'Responsing to client',
                    'number': 3,
                },
                {
                    'name': 'Creating report',
                    'number': 4,
                }
            ],
        }
    )
    # new data
    data = {
      "info": "templates with categories from 0 through 14",
      "templates": [
        {
          "title": 'name',
          "intro": 'intro',
          "sopDescription": "it well with the overall system.",
          "steps": [
            {
              "stepName": 'Firs tstep',
              "stepDescription": 'first desc'
            },
            {
              "stepName": "Communicate Expectations",
              "stepDescription": "Once the peand what is expected of them."
            },
            {
              "stepName": "Measure Actual Performance",
              "stepDescription": "This step invbservable behaviors or results."
            },
            {
              "stepName": "Compare Actual Performance with Standards",
              "stepDescription": "In this gaps."
            },
            {
              "stepName": "Discuss Appraisal with the Employee",
              "stepDescription": "Next, the manance gaps should be addressed."
            },
            {
              "stepName": "Design and Implement a Performance Plan",
              "stepDescription": "The final step invoving their performance."
            }
          ],
          "category": 'new category'
        },
      ]
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/templates/system/import',
        data=data
    )

    # assert
    assert response.status_code == 204
    another_sys_template.refresh_from_db()

    assert another_sys_template.category == another_category
    assert another_sys_template.name == name
    assert another_sys_template.description == desc
    assert another_sys_template.type == SysTemplateType.ACTIVATED

    template_data = another_sys_template.template
    assert template_data['name'] == name
    assert template_data['description'] == desc
    assert len(template_data['tasks']) == 4
    assert template_data['tasks'][0]['name'] == step_name
    assert template_data['tasks'][0]['description'] == step_desc
    assert template_data['tasks'][0]['number'] == 1


def test_import_templates__create_and_update__ok(api_client):

    # arrange
    user = create_test_user(is_staff=True)
    category_name = "Human Resources"
    step_name_1 = "Establish Performance Standards"
    step_desc_1 = "The first step of the requirements."
    template_desc_1 = "The performance appraisal process"
    template_name_1 = "Performance Appraisal"

    step_name_2 = "Step Name 2"
    step_desc_2 = "Step Desc 2"
    template_desc_2 = "Desc 2"
    template_name_2 = "Name 2"
    data = {
      "info": "templates with categories from 0 through 14",
      "templates": [
        {
          "title": template_name_2,
          "intro": template_desc_2,
          "sopDescription": "it well with the overall system.",
          "steps": [
            {
              "stepName": step_name_2,
              "stepDescription": step_desc_2
            },
          ],
          "category": category_name
        },
        {
            "title": template_name_1,
            "intro": template_desc_1,
            "sopDescription": "it well with the overall system.",
            "steps": [
                {
                    "stepName": step_name_1,
                    "stepDescription": step_desc_1
                }
            ],
            "category": category_name
        }
      ]
    }

    sys_template_2 = SystemTemplate.objects.create(
        is_active=False,
        name=template_name_2,
        description=template_desc_2,
        type=SysTemplateType.LIBRARY,
        template={
            'name': 'Old processing',
            'description': 'Old template desc',
            'tasks': [
                {
                    'name': 'Checking data',
                    'number': 1,
                }
            ]
        }
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/templates/system/import',
        data=data
    )

    # assert
    assert response.status_code == 204
    assert SystemTemplate.objects.count() == 2
    category = SystemTemplateCategory.objects.get(name=category_name)

    sys_template_1 = SystemTemplate.objects.get(name=template_name_1)
    assert sys_template_1.is_active is True
    assert sys_template_1.description == template_desc_1
    assert sys_template_1.category_id == category.id
    assert sys_template_1.type == SysTemplateType.LIBRARY
    template_data = sys_template_1.template
    assert template_data['name'] == template_name_1
    assert template_data['description'] == template_desc_1
    assert len(template_data['tasks']) == 1
    assert template_data['tasks'][0]['name'] == step_name_1
    assert template_data['tasks'][0]['description'] == step_desc_1
    assert template_data['tasks'][0]['number'] == 1

    sys_template_2.refresh_from_db()
    assert sys_template_2.is_active is False
    assert sys_template_2.description == template_desc_2
    assert sys_template_2.category_id == category.id
    assert sys_template_2.type == SysTemplateType.LIBRARY
    template_data = sys_template_2.template
    assert template_data['name'] == template_name_2
    assert template_data['description'] == template_desc_2
    assert len(template_data['tasks']) == 1
    assert template_data['tasks'][0]['name'] == step_name_2
    assert template_data['tasks'][0]['description'] == step_desc_2
    assert template_data['tasks'][0]['number'] == 1


def test_import_templates__kickoff_fields__names_transferred(api_client):

    # arrange
    user = create_test_user(is_staff=True)
    template_name = "Performance Appraisal"
    data = {
        "info": "",
        "templates": [
            {
                "title": template_name,
                "intro": 'intro',
                "sopDescription": "sop description",
                "category": 'category',
                "kickoff": {
                    'initiator': 'user',
                    "Contractor Information": "largeText",
                    "prospectiveInvestmentName": "text",
                    "Start": "date"
                },
                "steps": [
                    {
                        "stepName": 'name',
                        "stepDescription": 'desc',
                    }
                ]
            }
        ]
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/templates/system/import',
        data=data
    )

    # assert
    assert response.status_code == 204
    sys_template = SystemTemplate.objects.get(name=template_name)
    template_data = sys_template.template
    fields = template_data['kickoff']['fields']
    assert len(fields) == 4

    assert fields[0]['order'] == 1
    assert fields[0]['type'] == FieldType.USER
    assert fields[0]['name'] == 'Initiator'
    assert fields[0]['is_required'] is True

    assert fields[1]['order'] == 2
    assert fields[1]['type'] == FieldType.TEXT
    assert fields[1]['name'] == 'Contractor information'
    assert fields[1]['is_required'] is False

    assert fields[2]['order'] == 3
    assert fields[2]['type'] == FieldType.STRING
    assert fields[2]['name'] == 'Prospective investment name'
    assert fields[2]['is_required'] is False

    assert fields[3]['order'] == 4
    assert fields[3]['type'] == FieldType.DATE
    assert fields[3]['name'] == 'Start'
    assert fields[3]['is_required'] is False


def test_import_templates__escape_quote__ok(api_client):

    """ https://www.compart.com/en/unicode/U+201C """

    # arrange
    user = create_test_user(is_staff=True)
    category_name = "Human “Resources"
    step_name = "Establish “Performance Standards"
    step_desc = "The first “step of the requirements."
    template_desc = "The performance “appraisal process"
    template_name = "Performance “Appraisal"
    data = {
      "info": "templates with “categories from 0 through 14",
      "templates": [
        {
          "title": template_name,
          "intro": template_desc,
          "category": category_name,
          "steps": [
            {
              "stepName": step_name,
              "stepDescription": step_desc,
              "dueIn": {
                "days": 0,
                "hours": 12,
                "minutes": 30
              }
            }
          ]
        }
      ]
    }
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/templates/system/import',
        data=data
    )

    # assert
    assert response.status_code == 204
    sys_template = SystemTemplate.objects.get(name=template_name)
    assert sys_template.description == template_desc
    template_data = sys_template.template
    assert template_data['name'] == template_name
    assert template_data['description'] == template_desc
    assert template_data['tasks'][0]['name'] == step_name
    assert template_data['tasks'][0]['description'] == step_desc
    assert sys_template.category.name == category_name

# End to end tests


def test_create_template__from_imported_template__ok(api_client):

    """ end-to-end test """

    # arrange
    user = create_test_user(is_staff=True)
    category_name = "Human Resources"
    step_name = "Establish Performance Standards"
    step_desc = "The first step of the requirements."
    template_desc = "The performance appraisal process"
    template_name = "Performance Appraisal"
    data = {
        "info": "templates with categories from 0 through 14",
        "templates": [
            {
                "title": template_name,
                "intro": template_desc,
                "sopDescription": "it well with the overall system.",
                "steps": [
                    {
                        "stepName": step_name,
                        "stepDescription": step_desc,
                        "dueIn": {
                            "days": 12,
                            "hours": 2,
                            "minutes": 3
                        }
                    },
                    {
                        "stepName": "Communicate Expectations",
                        "stepDescription": "Once the them."
                    },
                    {
                        "stepName": "Measure Actual Performance",
                        "stepDescription": "This step or results."
                    },
                    {
                        "stepName": "Compare Actual with Standards",
                        "stepDescription": "In this gaps."
                    },
                    {
                        "stepName": "Discuss Appraisal with the Employee",
                        "stepDescription": "Next, be addressed."
                    },
                    {
                        "stepName": "Design and Implement a Performance Plan",
                        "stepDescription": "The their performance."
                    }
                ],
                "category": category_name
            },
        ]
    }
    api_client.token_authenticate(user)

    # create sys template
    response_import = api_client.post(
        '/templates/system/import',
        data=data
    )

    # get sys template
    response_list = api_client.get('/templates/system')
    sys_template_id = response_list.data[0]['id']

    # fill sys template
    response_fill = api_client.post(
        f'/templates/system/{sys_template_id}/fill'
    )

    # act
    response = api_client.post(
        path=f'/templates',
        data=response_fill.data
    )

    # assert
    assert response_import.status_code == 204
    assert response_list.status_code == 200
    assert response_fill.status_code == 200
    assert response.status_code == 200
    data = response.data
    assert data['name'] == template_name
    assert data['description'] == template_desc
    assert len(data['tasks']) == 6
    task_data = data['tasks'][0]
    assert task_data['name'] == step_name
    assert task_data['description'] == step_desc
    assert task_data['number'] == 1
    assert task_data['api_name']
    raw_due_date = task_data['raw_due_date']
    assert raw_due_date['rule'] == DueDateRule.AFTER_TASK_STARTED
    assert raw_due_date['duration_months'] == 0
    assert raw_due_date['duration'] == '12 02:03:00'
    assert raw_due_date['source_id'] == task_data['api_name']


def test_create_template__kickoff_fields__ok(api_client):

    """ end-to-end test """

    # arrange
    user = create_test_user(is_staff=True)
    template_name = "Performance Appraisal"
    data = {
        "info": "templates with categories from 0 through 14",
        "templates": [
            {
                "title": template_name,
                "intro": 'intro',
                "category": 'category_name',
                "kickoff": {
                    'initiator': 'user',
                    "Contractor Information": "largeText",
                    "prospectiveInvestmentName": "text",
                    "Start": "date"
                },
                "steps": [
                    {
                        "stepName": "Communicate Expectations",
                        "stepDescription": "Once the peand them."
                    }
                ]
            }
        ]
    }
    api_client.token_authenticate(user)

    # create sys template
    response_import = api_client.post(
        '/templates/system/import',
        data=data
    )

    # get sys template
    response_list = api_client.get('/templates/system')
    sys_template_id = response_list.data[0]['id']

    # fill sys template
    response_fill = api_client.post(
        f'/templates/system/{sys_template_id}/fill'
    )

    # act
    response = api_client.post(
        path=f'/templates',
        data=response_fill.data
    )

    # assert
    assert response_import.status_code == 204
    assert response_list.status_code == 200
    assert response_fill.status_code == 200
    assert response.status_code == 200
    data = response.data
    fields = data['kickoff']['fields']
    assert len(fields) == 4

    assert fields[0]['order'] == 1
    assert fields[0]['type'] == FieldType.USER
    assert fields[0]['name'] == 'Initiator'
    assert fields[0]['is_required'] is True

    assert fields[1]['order'] == 2
    assert fields[1]['type'] == FieldType.TEXT
    assert fields[1]['name'] == 'Contractor information'
    assert fields[1]['is_required'] is False

    assert fields[2]['order'] == 3
    assert fields[2]['type'] == FieldType.STRING
    assert fields[2]['name'] == 'Prospective investment name'
    assert fields[2]['is_required'] is False

    assert fields[3]['order'] == 4
    assert fields[3]['type'] == FieldType.DATE
    assert fields[3]['name'] == 'Start'
    assert fields[3]['is_required'] is False
