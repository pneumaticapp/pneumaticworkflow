

class WorkflowsMixin:

    def _overdue_workflows_cte(self):
        return """
        SELECT DISTINCT workflow_id
        FROM processes_task pt
          JOIN processes_workflow pw
            ON pt.workflow_id = pw.id
              AND pt.number = pw.current_task
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
        return """
        SELECT DISTINCT workflow_id FROM processes_task pt
          JOIN processes_workflow pw
            ON pt.workflow_id = pw.id
              AND pt.number = pw.current_task
          WHERE
            pw.is_deleted IS FALSE AND
            pw.date_completed IS NULL AND
            pw.status = %(status_running)s AND
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
        return """
        WHERE
          pt.status != 'skipped' AND
          pt.date_started <= %(date_to_tsp)s AND
          (
            pt.date_completed IS NULL OR
            pt.date_completed >= %(date_from_tsp)s
          ) AND
          (
            pw.date_completed IS NULL OR
            pw.date_completed >= %(date_from_tsp)s
          )
        """

    def _overdue_tasks_clause(self):
        return """
        WHERE pt.due_date IS NOT NULL AND
          pt.status != 'skipped' AND
          pt.date_started < %(date_to_tsp)s AND
          (
            pt.date_completed IS NULL OR
            pt.date_completed BETWEEN %(date_from_tsp)s AND %(date_to_tsp)s
          ) AND
          (
            pw.date_completed IS NULL OR
            pw.date_completed BETWEEN %(date_from_tsp)s AND %(date_to_tsp)s
          ) AND
          pt.due_date < COALESCE(
            pt.date_completed,
            pw.date_completed,
            NOW()
          )
        """

    def _started_tasks_clause(self):
        return """
        WHERE pt.date_first_started <= %(date_to_tsp)s AND
          pt.date_first_started >= %(date_from_tsp)s AND
          pt.status != 'skipped'
        """

    def _completed_tasks_clause(self):
        return """
        WHERE pt.date_completed BETWEEN %(date_from_tsp)s AND %(date_to_tsp)s
        """


class TasksNowMixin:

    def _tasks_in_progress_now_clause(self):
        return """
        WHERE
          pt.status != 'skipped' AND
          pt.date_completed IS NULL AND
          pt.date_started IS NOT NULL AND
          pw.status = %(status_running)s AND
          pw.date_completed IS NULL
        """

    def _overdue_tasks_now_clause(self):
        return """
        WHERE pt.due_date IS NOT NULL AND
          pt.status != 'skipped' AND
          pt.date_started IS NOT NULL AND
          pt.date_completed IS NULL AND
          pw.date_completed IS NULL AND
          pw.status = %(status_running)s AND
          pt.due_date < %(now)s
        """


class WorkflowTasksMixin(TasksMixin):

    def _overdue_tasks_clause(self):
        return """
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
              AND pw.current_task = pt.number
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
        return """
        WHERE
          pw.is_deleted IS FALSE AND
          pw.date_completed IS NULL AND
          pw.status = %(status_running)s AND
          pt.is_deleted IS FALSE AND
          pt.status != 'skipped' AND
          (
              (
                pt.due_date IS NOT NULL AND
                pt.date_started IS NOT NULL AND
                pt.date_completed IS NULL AND
                pt.due_date < %(now)s
              ) OR (
                pw.current_task = pt.number AND
                pw.due_date IS NOT NULL AND
                pw.due_date < %(now)s
              )
          )
          """
