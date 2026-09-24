import unittest

from engineering.core import AgentResult, AgentStatus, EngineerCore, EngineerTask, MaterialRef
from engineering.core.engineer_core import AgentRuntimeAdapter


class Naberezhnaya28AE2ETests(unittest.TestCase):
    """Real-project traceability fixture derived from the Library report.

    Only compact, attributed source facts are embedded; the 147 MB source report
    remains in the Library and is not copied into the repository.
    """

    def test_report_scope_and_source_version_conflict_reach_final_audit(self):
        task = EngineerTask(
            task_id="naberezhnaya-28a-e2e-001",
            tz=(
                "Проверить отчет по ТЗ; сопоставить факты, инструментальные данные, "
                "поверочные расчеты и итоговые выводы; не исправлять исходный отчет "
                "без доказанного основания."
            ),
            materials=(
                MaterialRef(
                    "tz-nab-28a",
                    "technical_assignment",
                    "15.09.2026 ТЗК БЦ ул. Набережная 28А на диск.docx: ТЗ",
                ),
                MaterialRef(
                    "report-nab-28a",
                    "report",
                    "15.09.2026 ТЗК БЦ ул. Набережная 28А на диск.docx: разделы 1-7",
                ),
                MaterialRef(
                    "calc-nab-28a",
                    "calculation",
                    "15.09.2026 ТЗК БЦ ул. Набережная 28А на диск.docx: приложение В",
                ),
                MaterialRef(
                    "instrumental-nab-28a",
                    "instrumental",
                    "15.09.2026 ТЗК БЦ ул. Набережная 28А на диск.docx: приложение Б",
                ),
                MaterialRef(
                    "pdf-v3-nab-28a",
                    "source_version",
                    "21.08.2026 ТЗК БЦ ул. Набережная 28А V3-сжатый.pdf",
                ),
            ),
            requested_checks=("report", "normative", "calculation"),
        )

        core = EngineerCore()
        execution_order = []
        specialist_results = {}

        def result(agent, observation, basis, certainty="CONFIRMED",
                   conclusion="Источник требует проверки.", evidence=("report-nab-28a",)):
            return AgentResult(
                task.task_id,
                agent,
                AgentStatus.ACCEPTED,
                findings=(
                    {
                        "observation": observation,
                        "evidence_ids": list(evidence),
                        "basis": basis,
                        "certainty": certainty,
                        "conclusion": conclusion,
                    },
                ),
                evidence_ids=tuple(evidence),
            )

        def handler(planned):
            execution_order.append(planned.agent)

            if planned.agent == "report-audit-agent":
                r = result(
                    planned.agent,
                    "Основной DOCX охватывает весь строительный объем объекта в осях 1-17/А1-И, секции 1-3 и паркинг, отм. -4.300 до +44.450 м.",
                    "Источник: основная версия DOCX, раздел 'Общая часть'.",
                    evidence=("tz-nab-28a", "report-nab-28a"),
                    conclusion="Границы обследования в источнике идентифицированы; проверка соответствия ТЗ продолжается.",
                )
                specialist_results[planned.agent] = r
                return r

            if planned.agent == "normative-agent":
                r = result(
                    planned.agent,
                    "В отчете заявлены ГОСТ 31937-2024, ГОСТ 27751-2014, СП 20.13330.2016, СП 63.13330.2018 и другие нормативные документы.",
                    "Перечень нормативных документов приведен в источнике; применимость конкретных требований должна проверяться по редакции и предмету проверки.",
                    certainty="UNCERTAIN",
                    conclusion="Нормативная проверка не считается принятой без проверки конкретных пунктов и редакций.",
                    evidence=("report-nab-28a",),
                )
                specialist_results[planned.agent] = r
                return r

            if planned.agent == "calculation-agent":
                r = result(
                    planned.agent,
                    "Источник сообщает о поверочных расчетах всех секций и указывает отдельные элементы с недостаточной несущей способностью.",
                    "Приложение В описывает цели расчета и примененные нормативные документы; сам вывод источника требует проверки расчетной модели и исходных данных.",
                    certainty="CONFIRMED",
                    conclusion="Расчетные выводы являются утверждениями источника и не принимаются как независимое доказательство без проверки модели.",
                    evidence=("calc-nab-28a",),
                )
                specialist_results[planned.agent] = r
                return r

            if planned.agent == "final-audit-agent":
                conflicts = core.cross_agent_conflicts(list(specialist_results.values()))
                self.assertEqual(len(conflicts), 0)
                return result(
                    planned.agent,
                    "Финальный аудит проверил трассируемость источников, границы ТЗ и разделение утверждений отчета от независимых выводов.",
                    "Для первого E2E допускается только то, что подтверждено входными материалами; сомнительные места остаются UNCERTAIN.",
                    conclusion="Первичный E2E завершен без выдачи независимого инженерного заключения.",
                    evidence=("tz-nab-28a", "report-nab-28a", "calc-nab-28a", "instrumental-nab-28a"),
                )

            raise AssertionError(f"Unexpected agent: {planned.agent}")

        state = core.run(
            task,
            AgentRuntimeAdapter({
                "report-audit-agent": handler,
                "normative-agent": handler,
                "calculation-agent": handler,
                "final-audit-agent": handler,
            }),
        )

        self.assertEqual(
            execution_order,
            ["report-audit-agent", "normative-agent", "calculation-agent", "final-audit-agent"],
        )
        self.assertEqual(len(state.results), 4)
        self.assertEqual(core.final_status(state), AgentStatus.UNCERTAINTY)
        self.assertTrue(
            any(
                finding["certainty"] == "UNCERTAIN"
                for finding in state.results[1].findings
            )
        )


if __name__ == "__main__":
    unittest.main()
