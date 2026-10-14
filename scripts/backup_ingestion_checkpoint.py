"""Local, explicit-list backup/isolated recovery. Never restores formal paths."""
import argparse
import json
from pathlib import Path
from joy_m2.ingest.ingestion_backup import create_backup,restore_backup


def main():
    parser=argparse.ArgumentParser()
    commands=parser.add_subparsers(dest='mode',required=True)
    backup=commands.add_parser('backup')
    backup.add_argument('--repo',type=Path,required=True)
    backup.add_argument('--file-list',type=Path,required=True,help='JSON array of explicit file paths')
    backup.add_argument('--archive',type=Path,required=True)
    restore=commands.add_parser('restore')
    restore.add_argument('--archive',type=Path,required=True)
    restore.add_argument('--new-root',type=Path,required=True)
    args=parser.parse_args()
    if args.mode=='backup':
        result=create_backup(json.loads(args.file_list.read_text()),args.archive,args.repo)
    else:
        result=restore_backup(args.archive,args.new_root)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
