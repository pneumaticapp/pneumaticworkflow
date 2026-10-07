from typing import Dict, List, Optional, Tuple
from src.processes.models.workflows.event import WorkflowEvent
from src.processes.models.workflows.fields import TaskField
from src.processes.models.workflows.task import Task
from src.processes.services.tasks.field import TaskFieldService
from src.ai.services.utils import as_tag, escape_closing_tags


class TaskUserMessageService:

    """ Creates a user message that passes the task to an AI agent """

    def __init__(self, task: Task):
        self.task = task

    def _get_return_comment(self) -> Optional[str]:

        """ Text of the comment the task was returned for rework with.
            None if the current task run was not started by a return.

            the last event on the task is TASK_REVERT
            with the text 'The phone number is wrong'
            -> 'The phone number is wrong'

            the task was completed after the revert
            -> None """

        events = WorkflowEvent.objects.on_task(self.task.id)
        revert_event = events.task_revert().order_by('-created').first()
        if revert_event is None:
            return None
        complete_event = events.task_complete().order_by('-created').first()
        if complete_event and complete_event.created > revert_event.created:
            return None
        return revert_event.text

    def _get_task_message(self) -> str:

        """ Task name, description and the rework comment.

            name 'Take the order', description 'Parse the transcript',
            returned for rework with 'The phone number is wrong'
            ->
            <task_name>
            Take the order
            </task_name>

            <task_description>
            Parse the transcript
            </task_description>

            <rework_comment>
            The task was returned to you for rework. Comment of the user
            who returned it:
            The phone number is wrong
            </rework_comment> """

        parts = [
            as_tag(
                tag='task_name',
                content=escape_closing_tags(self.task.name),
            ),
            as_tag(
                tag='task_description',
                content=escape_closing_tags(self.task.description or ''),
            ),
        ]
        comment = self._get_return_comment()
        if comment:
            parts.append(
                as_tag(
                    tag='rework_comment',
                    content=(
                        'The task was returned to you for rework. '
                        'Comment of the user who returned it:\n'
                        f'{escape_closing_tags(comment)}'
                    ),
                ),
            )
        return '\n\n'.join(parts)

    def _get_attachments_message(self) -> str:

        """ Content of the files attached to the task. Not implemented yet.

            any task -> '' """

        return ''

    def _get_field_options(self, field: TaskField) -> List[str]:

        """ Values the field value can be selected from.
            The same source the field value is validated against.

            selections 'Cash' and 'Card', a dataset item 'Card'
            -> ['Cash', 'Card'] """

        values = list(field.selections.values_list('value', flat=True))
        if field.dataset_id:
            values.extend(field.dataset.items.values_list('value', flat=True))
        return list(dict.fromkeys(values))

    def _get_field_attrs(self, field: TaskField) -> Dict[str, str]:

        """ Attributes of a field of any type.

            api_name 'size-1', name 'Size', type 'radio', required
            -> {
                'api_name': 'size-1',
                'name': 'Size',
                'type': 'radio',
                'required': 'yes',
            } """

        return {
            'api_name': field.api_name,
            'name': field.name,
            'type': field.type,
            'required': 'yes' if field.is_required else 'no',
        }

    def _get_description_prompt(self, field: TaskField) -> str:

        """ Description of the field, empty string if there is none.

            description 'Digits only'
            ->
            <description>
            Digits only
            </description> """

        if not field.description:
            return ''
        return as_tag(
            tag='description',
            content=escape_closing_tags(field.description),
        )

    def _get_options_prompt(self, field: TaskField) -> str:

        """ Values to select from, empty string if the field has none.

            options 'Cash' and 'Card'
            ->
            <options>
            <option>Cash</option>
            <option>Card</option>
            </options> """

        options = self._get_field_options(field=field)
        if not options:
            return ''
        return as_tag(
            tag='options',
            content='\n'.join(
                as_tag(
                    tag='option',
                    content=escape_closing_tags(value),
                    inline=True,
                )
                for value in options
            ),
        )

    def _get_string_field_prompt(self, field: TaskField) -> str:

        """ Specification of a single line text field.

            api_name 'phone-1', name 'Phone', required,
            description 'Digits only'
            ->
            <field_spec api_name="phone-1" name="Phone" type="string"
                        required="yes" max_length="140">
            <description>
            Digits only
            </description>
            </field_spec> """

        return as_tag(
            tag='field_spec',
            content=self._get_description_prompt(field=field),
            **self._get_field_attrs(field=field),
            max_length=TaskFieldService.STRING_LENGTH,
        )

    def _get_simple_field_prompt(self, field: TaskField) -> str:

        """ Specification of a field that has no parameters besides
            the common attributes and the description.
            The value format of the type is given in the system message.

            api_name 'total-1', name 'Total', type 'number', required,
            description 'Order total'
            ->
            <field_spec api_name="total-1" name="Total" type="number"
                        required="yes">
            <description>
            Order total
            </description>
            </field_spec> """

        return as_tag(
            tag='field_spec',
            content=self._get_description_prompt(field=field),
            **self._get_field_attrs(field=field),
        )

    def _get_text_field_prompt(self, field: TaskField) -> str:

        """ Specification of a multiline text field.

            api_name 'notes-1', name 'Notes', not required,
            no description
            ->
            <field_spec api_name="notes-1" name="Notes" type="text"
                        required="no"/> """

        return self._get_simple_field_prompt(field=field)

    def _get_number_field_prompt(self, field: TaskField) -> str:

        """ Specification of a number field.

            api_name 'total-1', name 'Total', required,
            no description
            ->
            <field_spec api_name="total-1" name="Total" type="number"
                        required="yes"/> """

        return self._get_simple_field_prompt(field=field)

    def _get_date_field_prompt(self, field: TaskField) -> str:

        """ Specification of a date field.

            api_name 'due-1', name 'Due date', required,
            no description
            ->
            <field_spec api_name="due-1" name="Due date" type="date"
                        required="yes"/> """

        return self._get_simple_field_prompt(field=field)

    def _get_url_field_prompt(self, field: TaskField) -> str:

        """ Specification of a web address field.

            api_name 'site-1', name 'Site', not required,
            no description
            ->
            <field_spec api_name="site-1" name="Site" type="url"
                        required="no"/> """

        return self._get_simple_field_prompt(field=field)

    def _get_user_field_prompt(self, field: TaskField) -> str:

        """ Specification of a user field. The possible values are given
            in the task description, not in the field specification.

            api_name 'owner-1', name 'Owner', required, no description
            ->
            <field_spec api_name="owner-1" name="Owner" type="user"
                        required="yes"/> """

        return self._get_simple_field_prompt(field=field)

    def _get_file_field_prompt(self, field: TaskField) -> str:

        """ Specification of a file field. The agent writes the content
            of the files, a tag per file.

            api_name 'report-1', name 'Report', not required,
            no description
            ->
            <field_spec api_name="report-1" name="Report" type="file"
                        required="no" multiple="yes"/> """

        return as_tag(
            tag='field_spec',
            content=self._get_description_prompt(field=field),
            **self._get_field_attrs(field=field),
            multiple='yes',
        )

    def _get_selection_field_prompt(
        self,
        field: TaskField,
        multiple: str = 'no',
    ) -> str:

        """ Specification of a field the value is selected from options.

            api_name 'pizzas-1', name 'Pizzas', required, multiple 'yes',
            options 'Pepperoni' and 'Four Cheese'
            ->
            <field_spec api_name="pizzas-1" name="Pizzas" type="checkbox"
                        required="yes" multiple="yes">
            <options>
            <option>Pepperoni</option>
            <option>Four Cheese</option>
            </options>
            </field_spec> """

        content = (
            self._get_description_prompt(field=field),
            self._get_options_prompt(field=field),
        )
        return as_tag(
            tag='field_spec',
            content='\n'.join(part for part in content if part),
            **self._get_field_attrs(field=field),
            multiple=multiple,
        )

    def _get_radio_field_prompt(self, field: TaskField) -> str:

        """ Specification of a single choice field.

            a radio field 'size-1' with the options 'Large' and 'Medium'
            ->
            <field_spec api_name="size-1" ... type="radio" multiple="no">
            <options>
            <option>Large</option>
            <option>Medium</option>
            </options>
            </field_spec> """

        return self._get_selection_field_prompt(field=field)

    def _get_dropdown_field_prompt(self, field: TaskField) -> str:

        """ Specification of a single choice field, the same as radio.

            a dropdown field 'payment-1' with the option 'Card'
            ->
            <field_spec api_name="payment-1" ... type="dropdown"
                        multiple="no">
            <options>
            <option>Card</option>
            </options>
            </field_spec> """

        return self._get_selection_field_prompt(field=field)

    def _get_checkbox_field_prompt(self, field: TaskField) -> str:

        """ Specification of a multiple choice field.

            a checkbox field 'pizzas-1' with the option 'Pepperoni'
            ->
            <field_spec api_name="pizzas-1" ... type="checkbox"
                        multiple="yes">
            <options>
            <option>Pepperoni</option>
            </options>
            </field_spec> """

        return self._get_selection_field_prompt(field=field, multiple='yes')

    def _get_field_prompt(self, field: TaskField) -> str:

        """ Specification of the single answer field.
            The method of the field type does the work.

            a field of the type 'radio'
            -> <field_spec api_name="size-1" ... type="radio" ...> """

        func = getattr(self, f'_get_{field.type}_field_prompt')
        return func(field=field)

    def _get_fields_message(self) -> str:

        """ Specifications of the fields the answer must be split into.

            output fields 'phone-1' of the type string and 'report-2'
            of the type file
            ->
            <fields>
            <field_spec api_name="phone-1" ... type="string" .../>
            <field_spec api_name="report-2" ... type="file" .../>
            </fields> """

        fields_prompts = []
        for field in self.task.output.all():
            get_field_prompt = getattr(self, f'_get_{field.type}_field_prompt')
            field_message = get_field_prompt(field=field)
            fields_prompts.append(field_message)
        return as_tag(
            tag='fields',
            content='\n'.join(fields_prompts),
        )

    def get_user_message(self) -> str:

        """ The whole message that passes the task to the agent.

            a task 'Take the order' with the output field 'phone-1'
            ->
            <task_name>
            Take the order
            </task_name>

            <task_description>
            Parse the transcript
            </task_description>

            <fields>
            <field_spec api_name="phone-1" ... type="string" .../>
            </fields> """

        parts = (
            self._get_task_message(),
            self._get_attachments_message(),
            self._get_fields_message(),
        )
        return '\n\n'.join(part for part in parts if part)

    def _get_attempt_value(self, value) -> str:

        """ Value of the field the agent answered with in a failed attempt.

            ['Card', 'Cash'] -> 'Card, Cash'
            4 -> '4' """

        if isinstance(value, (list, tuple)):
            return ', '.join(str(item) for item in value)
        return str(value)

    def get_errors_message(
        self,
        errors_stack: List[Tuple[dict, str]],
    ) -> str:

        """ The answers the task could not be completed with and the errors
            they failed with, so that the agent fixes them in a new answer.

            a single attempt with the values {'phone-1': 'call me'}
            and the error '- `phone-1`: Value should be a string.'
            ->
            <previous_attempts>
            The task could not be completed with your previous answers.
            Answer again and fix the errors.

            <attempt number="1">
            <answer>
            - `phone-1`: call me
            </answer>
            <errors>
            - `phone-1`: Value should be a string.
            </errors>
            </attempt>
            </previous_attempts> """

        attempts = []
        for number, (fields_values, error) in enumerate(errors_stack, 1):
            answer = '\n'.join(
                f'- `{api_name}`: {self._get_attempt_value(value)}'
                for api_name, value in fields_values.items()
            )
            content = '\n'.join((
                as_tag(tag='answer', content=escape_closing_tags(answer)),
                as_tag(tag='errors', content=escape_closing_tags(error)),
            ))
            attempts.append(
                as_tag(tag='attempt', content=content, number=number),
            )
        return as_tag(
            tag='previous_attempts',
            content=(
                'The task could not be completed with your previous '
                'answers. Answer again and fix the errors.\n\n'
                + '\n\n'.join(attempts)
            ),
        )

    def get_system_message(self, system_prompt: str) -> str:

        """ Instructions of the agent followed by the answer format rules.

            system_prompt 'You are an operator of a pizza delivery.'
            ->
            You are an operator of a pizza delivery.

            Return one <field> tag per output field listed in the
            <fields> section of the user message:

            <field api_name="FIELD_API_NAME" name="FIELD_NAME">
            value
            </field>

            Rules:
            - Return the fields in the order they are listed.
            ...
            - The value must match the type of the field:
              - string: a single line of plain text, not longer than
                max_length characters;
              - number: digits with a dot as the decimal separator,
                no units;
              ... """

        response_format_prompt = """
        Return one <field> tag per output field listed in the <fields> section
        of the user message:

        <field api_name="FIELD_API_NAME" name="FIELD_NAME">
        value
        </field>

        Rules:
        - Return the fields in the order they are listed.
        - Put no text outside the <field> tags: no greetings, no explanations.
        - Copy api_name and name exactly as they are given, do not translate
          or rename them.
        - Markdown inside a value is allowed, it does not break the tags.
        - The value must match the type of the field:
          - string: a single line of plain text, not longer than max_length
            characters;
          - text: multiline text;
          - number: digits with a dot as the decimal separator, no units;
          - date: a date and time in the format YYYY-MM-DDTHH:MM;
          - url: a full web address;
          - radio, dropdown: exactly one of the <option> values of the field,
            copied character by character;
          - checkbox: one or more of the <option> values of the field, copied
            character by character, a separate <field> tag with the same
            api_name for every chosen value;
          - user: exactly one email of a user or name of a group taken from
            the task description, copied character by character, nothing
            else;
          - file: the plain text content of a file in a text format, no
            binary data, the file name with the extension in the filename
            attribute:
            <field api_name="FIELD_API_NAME" name="FIELD_NAME"
                   filename="report.csv">
            content
            </field>
            a separate <field> tag with the same api_name for every file.
        - If a field is not required and there is nothing to put in it, return
          an empty tag.
        """

        return f'{system_prompt}\n{response_format_prompt}'
