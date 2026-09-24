import unittest

from engineering.core import AgentResult, AgentStatus, EngineerCore, EngineerTask, MaterialRef
from engineering.core.engineer_core import AgentRuntimeAdapter


class Naberezhnaya28AE2ETests(unittest.TestCase):
    """Traceability fixtures derived from the Library report.

    Only compact, attributed source facts are embedded; the source reports remain
    in the Library and are not copied into the repository.
    """

    def _task(self):
        return EngineerTask(
            task_id="naberezhnaya-28a-e2e-001",
            tz=(
                "Проверить отчет по ТЗ; трассировать факты, инструментальные данные, "
                "поверочные расчеты и итоговые выводы; не исправлять исходный отчет "
                "без доказанного основания."
            ),
            materials=(
                MaterialRef("tz-nab-28a", "technical_assignment", "DOCX: техническое задание"),
                MaterialRef("report-nab-28a", "report", "DOCX: разделы 1-7"),
                MaterialRef("calc-nab-28a", "calculation", "DOCX: приложение В"),
                MaterialRef("instrumental-nab-28a", "instrumental", "DOCX: приложение Б"),
                MaterialRef("pdf-v3-nab-28a", "source_version", "PDF V3: 21.08.2026"),
            ),
            requested_checks=("report", "normative", "calculation"),
        )

    @staticmethod
    def _finding(observation, basis, certainty, conclusion, evidence):
        return {
            "observation": observation,
            "evidence_ids": list(evidence),
            "basis": basis,
            "certainty": certainty,
            "conclusion": conclusion,
        }

    def test_real_project_traceability_preserves_local_positive_and_negative_results(self):
        task = self._task()
        core = EngineerCore()
        execution_order = []
        specialist_results = {}

        def make_result(agent, status, finding):
            return AgentResult(
                task.task_id,
                agent,
                status,
                findings=(finding,),
                evidence_ids=tuple(finding["evidence_ids"]),
            )

        def handler(planned):
            execution_order.append(planned.agent)

            if planned.agent == "report-audit-agent":
                r = make_result(
                    planned.agent,
                    AgentStatus.ACCEPTED,
                    self._finding(
                        "В источнике заявлен полный строительный объем обследования: секции 1-3 и паркинг.",
                        "Трассировка границ выполнена по основной версии DOCX.",
                        "CONFIRMED",
                        "Границы источника идентифицированы; они должны сопоставляться с ТЗ.",
                        ("tz-nab-28a", "report-nab-28a"),
                    ),
                )
                specialist_results[planned.agent] = r
                return r

            if planned.agent == "normative-agent":
                r = make_result(
                    planned.agent,
                    AgentStatus.UNCERTAINTY,
                    self._finding(
                        "Источник содержит ссылки на нормативные документы, но конкретные требования и редакции требуют отдельной проверки.",
                        "Нельзя считать нормативную применимость доказанной только по наличию документа в перечне.",
                        "UNCERTAIN",
                        "Нормативный вывод блокируется до проверки документа, редакции, пункта и применимости.",
                        ("report-nab-28a", "pdf-v3-nab-28a"),
                    ),
                )
                specialist_results[planned.agent] = r
                return r

            if planned.agent == "calculation-agent":
                # Two deliberately different local outcomes must remain local:
                # some elements are reported as insufficient, while some diaphragms
                # and slab zones are reported as sufficient.
                findings = (
                    self._finding(
                        "Источник сообщает недостаточность армирования отдельных колонн, балок, ригелей и плит.",
                        "Приложение В содержит расчетные выводы по конкретным секциям и участкам.",
                        "PROBABLE",
                        "Это утверждение источника требует проверки расчетной модели, исходных данных и соответствия фактическому армированию.",
                        ("calc-nab-28a", "report-nab-28a"),
                    ),
                    self._finding(
                        "Источник одновременно сообщает обеспеченность отдельных диафрагм и отдельных зон плит.",
                        "Положительные результаты должны сохраняться и не превращаться в искусственные замечания.",
                        "CONFIRMED",
                        "Результат должен оставаться локальным; обобщение на весь объект не допускается.",
                        ("calc-nab-28a", "report-nab-28a"),
                    ),
                )
                r = AgentResult(
                    task.task_id,
                    planned.agent,
                    AgentStatus.ACCEPTED,
                    findings=findings,
                    evidence_ids=("calc-nab-28a", "report-nab-28a"),
                )
                specialist_results[planned.agent] = r
                return r

            if planned.agent == "final-audit-agent":
                # A source-version discrepancy is an explicit uncertainty, not an
                # invented ERROR: the source set contains different numerical claims
                # for the K3 deviation magnitude.
                return make_result(
                    planned.agent,
                    AgentStatus.UNCERTAINTY,
                    self._finding(
                        "В разных версиях источника зафиксированы разные значения максимального отклонения К3.",
                        "DOCX/PDF V3 должны быть reconciled with the primary measurement record before selecting a value.",
                        "UNCERTAIN",
                        "Числовое значение К3 не принимается до установления действующей версии и первичного измерения.",
                        ("report-nab-28a", "pdf-v3-nab-28a"),
                    ),
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

        calculation = state.results[2]
        self.assertEqual(len(calculation.findings), 2)
        self.assertEqual(calculation.findings[0]["certainty"], "PROBABLE")
        self.assertEqual(calculation.findings[1]["certainty"], "CONFIRMED")
        self.assertNotEqual(
            calculation.findings[0]["conclusion"],
            calculation.findings[1]["conclusion"],
        )

    def test_source_version_conflict_is_not_silently_resolved(self):
        task = self._task()
        core = EngineerCore()
        seen = []

        def handler(planned):
            seen.append(planned.agent)
            if planned.agent == "report-audit-agent":
                return AgentResult(
                    task.task_id,
                    planned.agent,
                    AgentStatus.ACCEPTED,
                    findings=(
                        self._finding(
                            "Основная версия DOCX содержит расчетные и обследовательские разделы.",
                            "Источник идентифицирован.",
                            "CONFIRMED",
                            "Источник пригоден для дальнейшей трассировки.",
                            ("report-nab-28a",),
                        ),
                    ),
                    evidence_ids=("report-nab-28a",),
                )
            if planned.agent == "normative-agent":
                return AgentResult(
                    task.task_id,
                    planned.agent,
                    AgentStatus.ACCEPTED,
                    findings=(),
                    evidence_ids=("report-nab-28a",),
                )
            if planned.agent == "calculation-agent":
                return AgentResult(
                    task.task_id,
                    planned.agent,
                    AgentStatus.ACCEPTED,
                    findings=(
                        self._finding(
                            "Источник содержит числовое значение К3, требующее сверки с другой версией.",
                            "Нельзя выбирать одно из конфликтующих чисел без первичного источника.",
                            "UNCERTAIN",
                            "Оставить числовое значение неразрешенным.",
                            ("report-nab-28a", "pdf-v3-nab-28a"),
                        ),
                    ),
                    evidence_ids=("report-nab-28a", "pdf-v3-nab-28a"),
                )
            if planned.agent == "final-audit-agent":
                return AgentResult(
                    task.task_id,
                    planned.agent,
                    AgentStatus.ACCEPTED,
                    findings=(),
                    evidence_ids=("report-nab-28a", "pdf-v3-nab-28a"),
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

        self.assertEqual(seen[-1], "final-audit-agent")
        self.assertEqual(core.final_status(state), AgentStatus.UNCERTAINTY)
        self.assertTrue(
            any(
                finding["certainty"] == "UNCERTAIN"
                for result in state.results
                for finding in result.findings
            )
        )


if __name__ == "__main__":
    unittest.main()
