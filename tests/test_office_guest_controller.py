import contextlib,io,json,subprocess,unittest
from unittest.mock import patch
from runtime.office_guest_controller import main,CONTROL_TIMEOUT

class OfficeGuestControllerTests(unittest.TestCase):
    def test_fixed_command_has_bounded_outer_deadline_and_shutdown(self):
        with patch('runtime.office_guest_controller._dedicated_guest',return_value=True),patch('runtime.office_guest_controller.subprocess.run') as run:
            run.return_value.returncode=0
            self.assertEqual(main(),0)
        self.assertEqual(CONTROL_TIMEOUT,300)
        self.assertEqual(run.call_args_list[0].args[0],['python3','/opt/engineer-office-guest.py'])
        self.assertEqual(run.call_args_list[0].kwargs['timeout'],300)
        self.assertEqual([c.args[0] for c in run.call_args_list[1:]],[['sync'],['poweroff']])
    def test_guest_failure_is_not_duplicated_by_controller(self):
        out=io.StringIO()
        with patch('runtime.office_guest_controller._dedicated_guest',return_value=True),patch('runtime.office_guest_controller.subprocess.run') as run,contextlib.redirect_stdout(out):
            run.return_value.returncode=1
            self.assertEqual(main(),1)
        self.assertEqual(out.getvalue(),'')
    def test_host_execution_cannot_power_off_host(self):
        with patch('runtime.office_guest_controller._dedicated_guest',return_value=False),patch('runtime.office_guest_controller.subprocess.run') as run:
            with self.assertRaises(RuntimeError):main()
        run.assert_not_called()
    def test_timeout_emits_bounded_structured_failure_then_shutdown(self):
        out=io.StringIO()
        with patch('runtime.office_guest_controller._dedicated_guest',return_value=True),patch('runtime.office_guest_controller.subprocess.run',side_effect=[subprocess.TimeoutExpired(['python3'],300),None,None]) as run,contextlib.redirect_stdout(out):
            self.assertEqual(main(),1)
        line=out.getvalue().strip();self.assertTrue(line.startswith('ENGINEER_OFFICE_RESULT '))
        result=json.loads(line.removeprefix('ENGINEER_OFFICE_RESULT '))
        self.assertEqual(result['code'],1);self.assertEqual(result['error'],'TimeoutExpired');self.assertLessEqual(len(result['detail']),1024)
        self.assertEqual(run.call_args_list[-1].args[0],['poweroff'])
if __name__=='__main__':unittest.main()
