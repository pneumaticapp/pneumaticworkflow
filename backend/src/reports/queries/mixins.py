from src.processes.enums import TaskStatus, WorkflowStatus


class TemplateViewerMixin:
    """Mixin: template owners and viewers in dashboard queries."""

    def _get_user_workflow_access_clause(self):
        """Access: legacy starter, workflow owner, template owner, viewer."""
        return """
        (
            (
                pw.is_legacy_template IS TRUE AND
                pw.workflow_starter_id = %(user_id)s
            ) OR
            pwo.user_id = %(user_id)s OR
            (
                pto_user.user_id = %(user_id)s AND
                pto_user.is_deleted IS FALSE
            ) OR
            pto_group.user_id = %(user_id)s OR
            (
                ptv_user.user_id = %(user_id)s AND
                ptv_user.is_deleted IS FALSE
            ) OR
            ptv_group.user_id = %(user_id)s
        )
        """

    def _get_template_owner_joins(self):
        """Returns JOIN clauses for template owners."""
        return """
        LEFT JOIN processes_templateowner pto_user ON
            pt.id = pto_user.template_id AND
            pto_user.type = 'user' AND
            pto_user.is_deleted IS FALSE
        LEFT JOIN processes_templateowner pto_grp ON
            pt.id = pto_grp.template_id AND
            pto_grp.type = 'group' AND
            pto_grp.is_deleted IS FALSE
        LEFT JOIN accounts_usergroup_users pto_group ON
            pto_grp.group_id = pto_group.usergroup_id
        """

    def _get_template_viewer_joins(self):
        """Returns JOIN clauses for template viewers."""
        return """
        LEFT JOIN processes_templateviewer ptv_user ON
            pt.id = ptv_user.template_id AND
            ptv_user.type = 'user'
        LEFT JOIN processes_templateviewer ptv_grp ON
            pt.id = ptv_grp.template_id AND
            ptv_grp.type = 'group'
        LEFT JOIN accounts_usergroup_users ptv_group ON
            ptv_grp.group_id = ptv_group.usergroup_id
        """

    def _get_template_access_cte(self):
        """Returns CTE for templates accessible by user (owner or viewer)."""
        return """
        SELECT DISTINCT template_id, user_id
        FROM (
            SELECT template_id, user_id
            FROM processes_templateowner
            WHERE type = 'user' AND is_deleted IS FALSE
            UNION
            SELECT pto.template_id, aug.user_id
            FROM processes_templateowner pto
            JOIN accounts_usergroup_users aug
                ON pto.group_id = aug.usergroup_id
            WHERE pto.type = 'group' AND pto.is_deleted IS FALSE
            UNION
            SELECT template_id, user_id
            FROM processes_templateviewer
            WHERE type = 'user' AND is_deleted IS FALSE
            UNION
            SELECT ptv.template_id, aug.user_id
            FROM processes_templateviewer ptv
            JOIN accounts_usergroup_users aug
                ON ptv.group_id = aug.usergroup_id
            WHERE ptv.type = 'group' AND ptv.is_deleted IS FALSE
        ) AS template_access
        """


class WorkflowsMixin:

    def _overdue_workflows_cte(self):
        return f"""
        SELECT DISTINCT workflow_id
        FROM processes_task pt
          JOIN processes_workflow pw
            ON pt.workflow_id = pw.id
              AND pt.status = '{TaskStatus.ACTIVE}'
        WHERE pw.is_deleted IS FALSE AND
            pt.is_deleted IS FALSE AND
            pt.status != 'skipped' AND
            (
              pt.date_completed IS NULL OR
              pt.date_completed BETWEEN %(date_from_tsp)s AND %(date_to_tsp)s
            ) AND
            (
              pw.date_completed IS NULL OR
              pw.date_completed BETWEEN %(date_from_tsp)s AND %(date_to_tsp)s
            ) AND
            (
                (
                    pt.due_date IS NOT NULL AND
                    pt.due_date < COALESCE(
                      pt.date_completed,
                      pw.date_completed,
                      NOW()
                    ) AND
                    pt.date_started < %(date_to_tsp)s
                ) OR (
                    pw.due_date IS NOT NULL AND
                    pw.due_date < COALESCE(
                      pt.date_completed,
                      pw.date_completed,
                      NOW()
                    ) AND
                    pw.date_created < %(date_to_tsp)s
                )
            )
        """

    def _overdue_workflows_clause(self):
        return """WHERE ow.workflow_id IS NOT NULL"""

    def _workflows_in_progress_clause(self):
        return """
        WHERE pw.date_created <= %(date_to_tsp)s AND
          (pw.date_completed IS NULL OR pw.date_completed >= %(date_from_tsp)s)
        """

    def _started_workflows_clause(self):
        return """
        WHERE pw.date_created <= %(date_to_tsp)s AND
          pw.date_created >= %(date_from_tsp)s
        """

    def _completed_workflows_clause(self):
        return """
        WHERE pw.date_completed BETWEEN %(date_from_tsp)s AND %(date_to_tsp)s
        """


class WorkflowsNowMixin:

    def _overdue_workflows_now_cte(self):
        return f"""
        SELECT DISTINCT workflow_id
        FROM processes_task pt
          JOIN processes_workflow pw
            ON pt.workflow_id = pw.id
              AND pt.status = '{TaskStatus.ACTIVE}'
          WHERE
            pw.is_deleted IS FALSE AND
            pw.date_completed IS NULL AND
            pw.status = '{WorkflowStatus.RUNNING}' AND
            pt.is_deleted IS FALSE AND
            pt.status != 'skipped' AND
            (
                (
                    pt.due_date IS NOT NULL AND
                    pt.due_date < %(now)s
                ) OR (
                    pw.due_date IS NOT NULL AND
                    pw.due_date < %(now)s
                )
            )
        """

    def _overdue_workflows_now_clause(self):
        return """WHERE ow.workflow_id IS NOT NULL"""

    def _workflows_in_progress_now_clause(self):
        return """
        WHERE pw.date_created <= %(now)s AND
        pw.date_completed IS NULL
        """


class TasksMixin:

    def _tasks_in_progress_clause(self):
        return f"""
        WHERE pt.status IN (
            '{TaskStatus.ACTIVE}',
            '{TaskStatus.DELAYED}',
            '{TaskStatus.COMPLETED}'
        )
        AND pt.date_started <= %(date_to_tsp)s
        AND (
            (
                pt.status = '{TaskStatus.COMPLETED}'
                AND pt.date_completed >= %(date_from_tsp)s
            )
            OR pt.status != '{TaskStatus.COMPLETED}'
        )
        AND (
            (
                pw.status = '{WorkflowStatus.DONE}'
                AND pw.date_completed >= %(date_from_tsp)s
            )
            OR pw.status != '{WorkflowStatus.DONE}'
        )
        """

    def _overdue_tasks_clause(self):
        return f"""
        WHERE pt.status IN (
            '{TaskStatus.ACTIVE}',
            '{TaskStatus.DELAYED}',
            '{TaskStatus.COMPLETED}'
        )
        AND pt.due_date IS NOT NULL
        AND pt.due_date < COALESCE(
            pt.date_completed,
            pw.date_completed,
            NOW()
        )
        AND pt.date_started < %(date_to_tsp)s
        AND (
            (
                pt.status = '{TaskStatus.COMPLETED}'
                AND pt.date_completed BETWEEN %(date_from_tsp)s
                  AND %(date_to_tsp)s
            )
            OR pt.status != '{TaskStatus.COMPLETED}'
        )
        AND (
            (
                pw.status = '{WorkflowStatus.DONE}'
                AND pw.date_completed BETWEEN %(date_from_tsp)s
                  AND %(date_to_tsp)s
            )
            OR pw.status != '{WorkflowStatus.DONE}'
        )
        """

    def _started_tasks_clause(self):
        return f"""
        WHERE pt.date_first_started <= %(date_to_tsp)s
            AND pt.date_first_started >= %(date_from_tsp)s
            AND pt.status IN (
                '{TaskStatus.ACTIVE}',
                '{TaskStatus.DELAYED}',
                '{TaskStatus.COMPLETED}'
            )
        """

    def _completed_tasks_clause(self):
        return f"""
        WHERE pt.status = '{TaskStatus.COMPLETED}'
            AND pt.date_completed BETWEEN %(date_from_tsp)s AND %(date_to_tsp)s
        """


class TasksNowMixin:

    def _tasks_in_progress_now_clause(self):
        return f"""
        WHERE
          pt.status = '{TaskStatus.ACTIVE}' AND
          pw.status = '{WorkflowStatus.RUNNING}'
        """

    def _overdue_tasks_now_clause(self):
        return f"""
        WHERE pt.due_date IS NOT NULL AND
          pt.status != 'skipped' AND
          pt.date_started IS NOT NULL AND
          pt.date_completed IS NULL AND
          pw.date_completed IS NULL AND
          pw.status = '{WorkflowStatus.RUNNING}' AND
          pt.due_date < %(now)s
        """


class WorkflowTasksMixin(TasksMixin):

    def _overdue_tasks_clause(self):
        return f"""
        WHERE
          pt.status != 'skipped'
          AND pt.is_deleted IS FALSE
          AND pt.date_started IS NOT NULL
          AND (
            (
              pt.due_date IS NOT NULL
              AND pt.date_started < %(date_to_tsp)s
              AND pt.due_date < COALESCE(pt.date_completed, NOW())
              AND (
                pt.date_completed IS NULL
                OR pt.date_completed
                  BETWEEN %(date_from_tsp)s AND %(date_to_tsp)s
              )
            )
            OR (
              pw.due_date IS NOT NULL
              AND pt.status = '{TaskStatus.ACTIVE}'
              AND (
                pw.date_completed IS NULL
                OR pw.date_completed
                  BETWEEN %(date_from_tsp)s AND %(date_to_tsp)s
              )
              AND pw.due_date IS NOT NULL
              AND pt.date_started < %(date_to_tsp)s
              AND pw.due_date < COALESCE(pw.date_completed, NOW())
            )
          )
        """


class WorkflowTasksNowMixin(TasksNowMixin):

    def _overdue_tasks_now_clause(self):
        return f"""
        WHERE
          pw.is_deleted IS FALSE AND
          pw.date_completed IS NULL AND
          pw.status = '{WorkflowStatus.RUNNING}' AND
          pt.status = '{TaskStatus.ACTIVE}' AND
          pt.is_deleted IS FALSE AND
          (
              (
                pt.due_date IS NOT NULL AND
                pt.due_date < %(now)s
              ) OR (
                pw.due_date IS NOT NULL AND
                pw.due_date < %(now)s
              )
          )
          """
