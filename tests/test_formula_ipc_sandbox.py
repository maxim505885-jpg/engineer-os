"""Passive formula IPC profile keeps direct Internet access denied."""
import subprocess
import socket
import sys
import unittest


@unittest.skipUnless(sys.platform == 'linux', 'Linux seccomp profile')
class FormulaIpcSandboxTests(unittest.TestCase):
    def child(self, code):
        return subprocess.run([sys.executable, '-c', code], capture_output=True, text=True)

    def test_passive_profile_rejects_new_internet_sockets(self):
        code = '''
import socket
from engineering.local_app.doc_sandbox import apply
apply(passive_local_ipc=True)
for family in (socket.AF_INET, socket.AF_INET6):
    try: socket.socket(family)
    except PermissionError: continue
    raise SystemExit('Internet socket permitted')
print('DIRECT_NETWORK_DENIED')
'''
        result = self.child(code)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('DIRECT_NETWORK_DENIED', result.stdout)

    def test_passive_profile_closes_sockets_opened_before_filter(self):
        code = '''
import os, socket
from engineering.local_app.doc_sandbox import apply
client = socket.socket(socket.AF_INET)
descriptor = client.fileno()
apply(passive_local_ipc=True)
try: os.fstat(descriptor)
except OSError: print('INHERITED_SOCKET_CLOSED')
else: raise SystemExit('Existing socket survived')
'''
        result = self.child(code)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('INHERITED_SOCKET_CLOSED', result.stdout)

    def test_legacy_profile_still_denies_unix_socket_creation(self):
        result = self.child('''
import socket
from engineering.local_app.doc_sandbox import apply
apply()
try: socket.socket(socket.AF_UNIX)
except PermissionError: print('STRICT_PROFILE')
else: raise SystemExit('Legacy profile weakened')
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('STRICT_PROFILE', result.stdout)

    def test_passive_profile_permits_local_pipe_exchange_when_host_allows_it(self):
        try:
            probe=socket.socket(socket.AF_UNIX);probe.close()
        except PermissionError:
            self.skipTest('Host sandbox disallows Unix sockets before app filter')
        result=self.child('''
import socket, os, tempfile
from engineering.local_app.doc_sandbox import apply
with tempfile.TemporaryDirectory() as root:
    apply(passive_local_ipc=True)
    server=socket.socket(socket.AF_UNIX)
    server.bind(root+'/pipe');server.listen(1)
    client=socket.socket(socket.AF_UNIX);client.connect(root+'/pipe')
    peer,_=server.accept()
    os.write(client.fileno(),b'IPC')
    assert os.read(peer.fileno(),3)==b'IPC'
    print('LOCAL_PIPE_OK')
''')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('LOCAL_PIPE_OK',result.stdout)
