from collections import OrderedDict
from dataclasses import replace
from ipaddress import v6_int_to_packed
from os import scandir

from yaml import Dumper, FullLoader, add_representer, dump, load

KEYS_TO_REMOVE = ["x-ibm-configuration"]


class Dumper(Dumper):
    def increase_indent(self, flow=False, *args, **kwargs):
        return super().increase_indent(flow=flow, indentless=False)


class literal(str):
    pass


def literal_presenter(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")


add_representer(literal, literal_presenter)


def ordered_dict_presenter(dumper, data):
    return dumper.represent_dict(data.items())


add_representer(OrderedDict, ordered_dict_presenter)


def get_docs(dir: str = "../swagger", file_type: str = ".yaml"):
    docs = []
    for entry in scandir(dir):
        if entry.name.endswith(file_type):
            docs.append(entry.name.replace(file_type, ""))
    return docs


def remove_elements(data):
    for key in KEYS_TO_REMOVE:
        if key in data:
            del data[key]
    return data


def remove_discriminator(data):
    del data["components"]["schemas"]["Resource"]["discriminator"]
    return data


def update_elements(data, static):
    updated = data | static
    return updated


def update_components(data, components):
    for component in components["components"]:
        if component not in data["components"]:
            data["components"][component] = components["components"][component]
        else:
            for attribute in components["components"][component]:
                if attribute not in data["components"][component]:
                    data["components"][component][attribute] = components["components"][
                        component
                    ][attribute]
                else:
                    data["components"][component][attribute].update(
                        components["components"][component][attribute]
                    )
    return data


def list_replace_value(l, key):
    x = []
    for e in l:
        if isinstance(e, list):
            e = list_replace_value(e, key)
        elif isinstance(e, dict):
            e = dict_replace_value(e, key)
        elif isinstance(e, str):
            e = e.replace('_', '')
        x.append(e)
    return x


def dict_replace_value(d, key):
    x = {}
    for k, v in d.items():
        if key == k:
            v = v.replace('_', '')
        elif isinstance(v, dict):
            v = dict_replace_value(v, key)
        elif isinstance(v, list):
            v = list_replace_value(v, key)
        x[k] = v
    return x


def replace_underscore_values(data):
    d = dict_replace_value(data, '$ref')
    for key in list(d['components']['schemas']):
        if "_" in key:
            new_key = key.replace('_', '')
            d['components']['schemas'][new_key] = d['components']['schemas'][key]
            del d['components']['schemas'][key]
    return d


def replace_markdown_variables(data, type):
    d = temp_dict = {}
    files = open_markdown(type)
    if files:
        for file in files:
            keys = file.split("-")
            for index, key in enumerate(keys):
                if index != len(keys) - 1:
                    temp_dict.setdefault(key, {})
                    temp_dict = temp_dict[key]
                else:
                    temp_dict.setdefault(key, literal(open_file(file, type, "md")))
            key__original_value = data.get(keys[0])
            key_merged = key__original_value | d[keys[0]]
            data[keys[0]] = key_merged

    return data


def open_file(file, type, file_type):
    with open(f"../swagger/{type}-static/{file}.{file_type}", "r") as f:
        return f.read()


def open_markdown(type):
    markdown_files = get_docs(f"../swagger/{type}-static", ".md")
    return markdown_files


def open_yaml(type, static=False, name=""):
    if static:
        with open(f"../swagger/{type}-static/{name}.yaml", "r") as f:
            return load(f, Loader=FullLoader)
    else:
        with open(f"../swagger/{type}.yaml", "r") as f:
            return load(f, Loader=FullLoader)


def save_yaml(type, data):
    with open(f"../api/{type}/swagger.yaml", "w") as f:
        output = dump(data, f, sort_keys=False, Dumper=Dumper)


def process_swagger(type):
    data = open_yaml(type)
    if data:
        header = open_yaml(type, True, "header")
        if header:
            data = update_elements(data, header)
        components = open_yaml(type, True, "components")
        if components:
            data = update_components(data, components)
        data = remove_discriminator(data)
        data = remove_elements(data)
        data = replace_underscore_values(data)
        data = replace_markdown_variables(data, type)
        d = OrderedDict(data)
        save_yaml(type, d)


def entry(type: str = ""):
    if type != "":
        process_swagger(type)
    else:
        swagger_docs = get_docs()
        for type in swagger_docs:
            process_swagger(type)
