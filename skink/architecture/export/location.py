from skink.architecture.export.context import DEFAULT

def normalize_location(l: str, ctx = DEFAULT):
    if l[0] == '/':
        tr = ctx.location_rules.transformation_rules
        if tr.use_include_list:
            # TODO: needs a test
            for option in tr.include_list:
                if l.startswith(f'/{option}'):
                    l = l[1:]
                    break
            else:
                l = 'EXE' + l
        elif tr.use_exclude_list:
            raise NotImplementedError()
        else:
            l = l[1:]
    if l.endswith(".h"):
        l = l[:-2]
    return l