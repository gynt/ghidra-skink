from typing import Generator, Tuple

from skink.architecture.common.exclusion import filter_includes
from ...export.context import DEFAULT, Context
from ...export.types import generate_include_for_class, generate_include_for_type, remap_type
from ...sarif.functions.FunctionResult import FunctionResult

# TODO: needs a context object to understand root path

class Function(object):
    def __init__(self, f: FunctionResult):
        self.f = f
        self.name = self.f.properties.additionalProperties.name

    def this_parameter_type(self, ctx = DEFAULT) -> Tuple[str, str] | None:
        for param in self.f.properties.additionalProperties.params:
            is_class_parameter = param.isAutoParameter and param.name == "this"
            if is_class_parameter:
                return remap_type(param.formalTypeName, param.formalTypeLocation, ctx=ctx)

    def return_type(self, ctx = DEFAULT) -> Tuple[str, str]:
        param = self.f.properties.additionalProperties.ret
        return remap_type(param.formalTypeName, param.formalTypeLocation, ctx=ctx)

    def parameter_types(self, ctx = DEFAULT) -> Generator[Tuple[str, str]]:
        for param in self.f.properties.additionalProperties.params:
            is_class_parameter = param.isAutoParameter and param.name == "this"
            if is_class_parameter:
                continue
            else:
                yield remap_type(param.formalTypeName, param.formalTypeLocation, ctx=ctx)

    # Note: includes return type sometimes
    def _collect_includes(self, ctx = DEFAULT):
        include_this = ctx.include.functions_this_parameter_type
        if include_this:
            needle = self.this_parameter_type(ctx=ctx)
            if needle:
                type_name, type_loc = needle
                yield from generate_include_for_class(type_name, type_loc, ctx=ctx)
        for type_name, type_loc in self.parameter_types(ctx):
            yield from generate_include_for_type(type_name, type_loc, ctx=ctx)
        
        type_name, type_loc = self.return_type(ctx=ctx)
        yield from generate_include_for_type(type_name, type_loc, ctx=ctx) # pyright: ignore[reportArgumentType]

    def includes(self, ctx = DEFAULT):
        return filter_includes(self._collect_includes(ctx), ctx)
    
    def declaration(self, ctx: Context):
        name = self.f.properties.additionalProperties.name
        ret = self.f.properties.additionalProperties.ret.type.name

        if ctx.function_rules.include_convention:
            cc = self.f.properties.additionalProperties.callingConvention
        else:
            cc = ""
        
        if ctx.function_rules.include_this:
            this_candidates = [param for param in self.f.properties.additionalProperties.params if param.name == "this"]
            if this_candidates:
                this = this_candidates[0]
                coretype = this.type.name.split(" *")[0]
                if ctx.promote_to_class:
                    this = f"{ctx.class_rules.prefix}{coretype}{ctx.class_rules.suffix} * {this.name}"
                else:
                    this = f"{coretype} * {this.name}"
            else:
                this = ""
        else:
            this = ""

        params = [param for param in self.f.properties.additionalProperties.params if param.name != "this"]
        
        if this:
            all_params = ", ".join([this] + [f"{param.type.name} {param.name}" for param in params])
        else:
            all_params = ", ".join([f"{param.type.name} {param.name}" for param in params])
        
        virtual_wrapper = lambda x: f"{x};"
        if ctx.class_rules.virtual:
            virtual_wrapper = lambda x: f"virtual {x} = 0;" 
 
        return virtual_wrapper(f"{ret} {cc} {name}({all_params})") # TODO: improve
    
    def namespace(self):
        return self.f.properties.additionalProperties.namespace
    
    def __str__(self):
        includes: str = "\n".join(self._collect_includes())
        declaration: str = self.f.properties.additionalProperties.value

        return '\n\n'.join([includes, declaration])
    
    def export(self, ctx = DEFAULT):
        
        if ctx.style.namespace:
            wrap = lambda x: f"namespace {self.namespace()} {{\n\n  {x}\n\n}}"
        else:
            wrap = lambda x: x

        return f"{"\n".join(self.includes(ctx))}\n\n{wrap(self.declaration(ctx))}"