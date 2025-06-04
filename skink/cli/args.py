
import argparse


parser = argparse.ArgumentParser(prog="skink", add_help=True)
parser.add_argument("--debug", required=False, default=False, action='store_true')
parser.add_argument("--verbose", required=False, default=False, action='store_true')
parser.add_argument("--silent", required=False, default=False, action='store_true')

def parse_bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')
    
parser.add_argument("--log-console", required=False, default=True, type=parse_bool)
parser.add_argument("--log-console-to-stderr", required=False, default=False, type=parse_bool)
parser.add_argument("--log-file", required=False, default=False, type=parse_bool)
subparsers = parser.add_subparsers(title="subcommands", required=True, dest='subcommand')

preprocess = subparsers.add_parser('preprocess')
preprocess.add_argument(dest='action', choices=['filter'])
preprocess.add_argument("file", nargs=1, help="sarif file to preprocess")
preprocess.add_argument("--filter-namespace", type=str, default="", required=False)
preprocess.add_argument("--output", default="preprocessed.json")
preprocess.add_argument("--or", default=False, action='store_true', required=False)
preprocess.add_argument("--and", default=False, action='store_true', required=False)

create = subparsers.add_parser('create')
create.add_argument("--dir", required=False, default=".", help="output directory (default: '.')")
create.add_argument("files", nargs='+', help="sarif files to be parsed and processed")
create.add_argument("--export", required=False, default="all", help='what to export (default "all")', choices=['all', 'classes', 'functions', 'structures', 'enums'])
create.add_argument("--limit", type=int, help="limit the export to this amount of entries (default: no limit)", default=0)
create.add_argument("--prefix", required=False, default="", help="filter sarif contents for namespaces with this prefix (default: '')")

export = subparsers.add_parser("export")
export.add_argument("what", choices=["*", "classes", "functions", "variables", "namespaces"])
export.add_argument("--input", required=True, help="input file")
export.add_argument("--output", required=False, default="output", help="outpath path")
export.add_argument("--input-format", default="sarif")

settings = subparsers.add_parser("settings")

sarif = subparsers.add_parser("sarif")
sarif_actions = sarif.add_subparsers(title = "action", dest="sarif_action")
sarif_extract = sarif_actions.add_parser('extract')
sarif_extract.add_argument("--input", required=True, help="input file")
sarif_extract.add_argument("--output", required=False, default="output", help="outpath path")
sarif_extract.add_argument("--input-format", default="sarif")