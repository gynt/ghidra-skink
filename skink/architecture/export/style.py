from dataclasses import dataclass


@dataclass
class AbstractStyle:
    name: str = ""

NamespaceStyle = AbstractStyle("namespace")