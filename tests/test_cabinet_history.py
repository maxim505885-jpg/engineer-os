"""History keysets keep old project records reachable under concurrent writes."""
import tempfile
import unittest
from pathlib import Path
from engineering.local_app.store import Store


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(Path(self.tmp.name));self.session=self.store.create_session('Project')['id']

    def test_all_messages_and_jobs_past_snapshot_limits_are_reachable(self):
        for i in range(205):
            job=self.store.enqueue(self.session,str(i),[]);self.store.claim()
            self.store.finish(job['id'],{'text':'reply '+str(i)})
        other=self.store.create_session('Other')['id'];self.store.enqueue(other,'PRIVATE OTHER',[])
        self.assertEqual(len(self.store.snapshot(self.session)['messages']),200)
        for kind,expected in [('messages',410),('jobs',205)]:
            cursor=None;rows=[]
            while True:
                page=self.store.history(self.session,kind=kind,before=cursor,limit=50)
                rows.extend(page['records'])
                if not page['has_more']:break
                cursor=page['next_before']
            self.assertEqual(len(rows),expected)
            self.assertEqual(len({r['seq'] if kind=='messages' else r['id'] for r in rows}),expected)
            self.assertNotIn('PRIVATE OTHER',str(rows))

    def test_new_messages_do_not_shift_an_existing_page_cursor(self):
        for i in range(3):
            job=self.store.enqueue(self.session,str(i),[]);self.store.claim();self.store.finish(job['id'],{'text':'reply'})
        first=self.store.history(self.session,kind='messages',limit=2)
        self.store.enqueue(self.session,'new after first page',[])
        second=self.store.history(self.session,kind='messages',before=first['next_before'],limit=50)
        self.assertEqual(len(second['records']),4)
        self.assertNotIn('new after first page',str(second))
        self.assertFalse(set(r['seq'] for r in first['records']) & set(r['seq'] for r in second['records']))

    def test_invalid_cursors_limits_and_unknown_projects_fail(self):
        for kwargs in [dict(kind='files'),dict(kind='jobs',limit=0),dict(kind='jobs',limit=201),dict(kind='messages',before=-1),dict(kind='jobs',before=True)]:
            with self.assertRaises(ValueError):self.store.history(self.session,**kwargs)
        with self.assertRaises(ValueError):self.store.history('00000000-0000-0000-0000-000000000000',kind='jobs')
