import unittest

from engineering.core import AgentResult, AgentStatus, EngineerCore, EngineerTask, MaterialRef
from engineering.core.engineer_core import AgentRuntimeAdapter


class DeterministicEndToEndTests(unittest.TestCase):
    """Exercise the full ENGINEER CORE orchestration path without a live model."""

    def test_tz_materials_agents_conflict_final_audit_and_status(self):
        task = EngineerTask(
            task_id="e2e-001",
            tz="Проверить отчет по ТЗ; не менять корректный результат без доказанного основания.",
            materials=(
                MaterialRef("report-1", "report", "inspection-report.docx"),
                MaterialRef("photo-1", "photo", "photo-01.jpg"),
            ),
            requested_checks=("report", "normative", "calculation"),
        )

        core = EngineerCore()
        execution_order = []
        specialist_results = {}

        def handler(planned):
            execution_order.append(planned.agent)

            if planned.agent == "final-audit-agent":
                conflicts = core.cross_agent_conflicts(list(specialist_results.values()))
                self.assertEqual(len(conflicts), 1)
                conflict = conflicts[0]
                return AgentResult(
                    planned.task_id,
                    planned.agent,
                    AgentStatus.ACCEPTED,
                    findings=(
                        {
                            "observation": "Конфликт между специализированными выводами рассмотрен.",
                            "evidence_ids": list(conflict["evidence_ids"]),
                            "basis": "Сопоставление исходных материалов и результатов специалистов.",
                            "certainty": "CONFIRMED",
                            "conclusion": "Противоречие разрешено по исходному доказательству.",
                            "conflict_ids": [conflict["id"]],
                            "resolution_status": "RESOLVED",
                            "resolution_basis": "Исходные материалы подтверждают основание принятого вывода.",
                        },
                    ),
                    evidence_ids=tuple(conflict["evidence_ids"]),
                )

            certainty = "UNCERTAIN" if planned.agent == "normative-agent" else "CONFIRMED"
            result = AgentResult(
                planned.task_id,
                planned.agent,
                AgentStatus.ACCEPTED,
                findings=(
                    {
                        "observation": "Проверяемый признак зафиксирован в исходном материале.",
                        "evidence_ids": ["report-1"],
                        "basis": "Исходный материал задачи.",
                        "certainty": certainty,
                        "conclusion": "Вывод сформирован с указанной степенью определенности.",
                    },
                ),
                evidence_ids=("report-1",),
            )
            specialist_results[planned.agent] = result
            return result

        state = EngineerCore().run(task, AgentRuntimeAdapter({
            "report-audit-agent": handler,
            "normative-agent": handler,
            "calculation-agent": handler,
            "final-audit-agent": handler,
        }))

        self.assertEqual(
            execution_order,
            [
                "report-audit-agent",
                "normative-agent",
                "calculation-agent",
                "final-audit-agent",
            ],
        )
        self.assertEqual(state.planned[-1].agent, "final-audit-agent")
        self.assertEqual(state.planned[-1].tz, task.tz)
        self.assertEqual(
            [material.id for material in state.planned[-1].inputs],
            ["report-1", "photo-1"],
        )
        self.assertEqual(len(state.results), 4)
        self.assertEqual(len(core.cross_agent_conflicts(state.results)), 1)
        self.assertEqual(core.final_status(state), AgentStatus.ACCEPTED)


if __name__ == "__main__":
    unittest.main()
