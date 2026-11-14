import sys

from skink.ghidra.verify import verify

def main_ghidra(args):
  if args.ghidra_action != "verify":
    raise Exception(f"not implemented: {args.ghidra_action}")
  if verify(args.gzf, args.sarif, max_reports=args.max_reports):
    sys.exit(1)
