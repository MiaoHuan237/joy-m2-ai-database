import fcntl
from pathlib import Path
import tempfile
import sqlite3
import unittest
import zipfile

from joy_m2.ingest.ingestion_backup import create_backup,restore_backup


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve()
        self.source=self.root/'original.txt'
        self.source.write_bytes(b'original evidence')
        self.archive=self.root/'checkpoint.zip'
        self.restore=self.root/'restored'

    def test_byte_verified_restore_is_separate_and_exclusive(self):
        result=create_backup([self.source],self.archive,self.root)
        self.assertIsInstance(result,dict)
        restored=restore_backup(self.archive,self.restore)
        self.assertEqual(restored['file_count'],1)
        self.assertEqual((self.restore/'files/00000000').read_bytes(),self.source.read_bytes())
        with self.assertRaises(FileExistsError): restore_backup(self.archive,self.restore)
        with self.assertRaises(FileExistsError): create_backup([self.source],self.archive,self.root)

    def test_corrupt_archive_never_creates_restore_root(self):
        create_backup([self.source],self.archive,self.root)
        self.assertTrue(self.archive.exists())
        with zipfile.ZipFile(self.archive,'a') as archive:
            archive.writestr('foreign',b'bad')
        with self.assertRaises(ValueError): restore_backup(self.archive,self.restore)
        self.assertFalse(self.restore.exists())

    def test_running_writer_lock_prevents_checkpoint(self):
        runtime=self.root/'data/staging/auto-ingestion'
        runtime.mkdir(parents=True)
        with (runtime/'cycle.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.assertRaises(BlockingIOError): create_backup([self.source],self.archive,self.root)
        self.assertFalse(self.archive.exists())

    def test_symlink_input_rejected(self):
        link=self.root/'link'
        link.symlink_to(self.source)
        with self.assertRaises(ValueError): create_backup([link],self.archive,self.root)

    def test_committed_wal_is_rejected_without_checkpointing_source(self):
        database=self.root/'state.sqlite3'
        with sqlite3.connect(database) as connection:
            connection.execute('PRAGMA journal_mode=WAL')
            connection.execute('CREATE TABLE t (value INTEGER)')
            connection.execute('INSERT INTO t VALUES (42)')
            connection.commit()
            before={p.name:p.read_bytes() for p in self.root.glob('state.sqlite3*')}
            with self.assertRaisesRegex(ValueError,'SQLite sidecar'):
                create_backup([database],self.archive,self.root)
            self.assertEqual(before,{p.name:p.read_bytes() for p in self.root.glob('state.sqlite3*')})
            self.assertFalse(self.archive.exists())
        connection.close()

    def test_active_rollback_journal_is_rejected(self):
        database=self.root/'state.sqlite3'
        connection=sqlite3.connect(database)
        self.addCleanup(connection.close)
        connection.execute('CREATE TABLE t (value INTEGER)')
        connection.commit()
        connection.execute('INSERT INTO t VALUES (42)')
        with self.assertRaisesRegex(ValueError,'SQLite sidecar'):
            create_backup([database],self.archive,self.root)
        self.assertFalse(self.archive.exists())
