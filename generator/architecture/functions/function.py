from generator.architecture.export.context import DEFAULT, Context
from generator.architecture.export.style import NamespaceStyle
from generator.sarif import FunctionResult, Param, TypeInfo

# TODO: needs a context object to understand root path

class Function(object):
    def __init__(self, f: FunctionResult):
        self.f = f

    def _normalize_location(self, l: str):
        if l[0] == '/':
            if not l.startswith('/_HoldStrong'):
                l = 'EXE' + l
            else:
                l = l[1:]
        if l.endswith(".h"):
            l = l[:-2]
        return l
    
    def _include_for_type(self, param: Param):
        t = param.type
        loc = t.location
        if not loc:
            raise Exception(f"no location for type: {param.typeName} {param.name}")
        
        if loc != "/": # TODO: is this too general?
            if loc.endswith(".h"):
                loc = self._normalize_location(loc)
                yield f'#include "{loc}.h"'
            else:
                loc = self._normalize_location(loc)
                name = t.name
                if name.endswith(" *"):
                    name = name[:-2]

                yield f'#include "{loc}/{name}.h"'


    # Note: includes return type sometimes
    def _collect_includes(self, include_this = True):
        for param in self.f.properties.additionalProperties.params:
            if not include_this and param.isAutoParameter and param.name == "this":
                continue
            yield from self._include_for_type(param)
        
        param = self.f.properties.additionalProperties.ret
        yield from self._include_for_type(param)

    def includes(self, include_this = True):
        return self._collect_includes(include_this)
    
    def declaration(self, ctx: Context):
        ret = self.f.properties.additionalProperties.ret.type.name
        cc = self.f.properties.additionalProperties.callingConvention
        name = self.f.properties.additionalProperties.name
        this_candidates = [param for param in self.f.properties.additionalProperties.params if param.name == "this"]
        if this_candidates:
            this = this_candidates[0]
            coretype = this.type.name.split(" *")[0]
            if ctx.promote_to_class:
                this = f"{coretype}Class * {this.name}"
            else:
                this = f"{coretype} * {this.name}"
        else:
            this = ""
        params = [param for param in self.f.properties.additionalProperties.params if param.name != "this"]
        all_params = ", ".join([this] + [f"{param.type.name} {param.name}" for param in params])
        return f"{ret} {cc} {name}({all_params});" # TODO: improve
    
    def namespace(self):
        return self.f.properties.additionalProperties.namespace
    
    def __str__(self):
        includes: str = "\n".join(self._collect_includes())
        declaration: str = self.f.properties.additionalProperties.value

        return '\n\n'.join([includes, declaration])
    
    def export(self, ctx = DEFAULT):
        
        if ctx.style == NamespaceStyle:
            wrap = lambda x: f"namespace {self.namespace()} {{\n\n\t{x}\n\n}}"
        else:
            wrap = lambda x: x

        return f"{"\n".join(self.includes(ctx.include.functions_this_parameter_type))}\n\n{wrap(self.declaration(ctx))}"