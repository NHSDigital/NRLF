from os import scandir

from yaml import Dumper, FullLoader, dump, load

KEYS_TO_REMOVE = ["x-ibm-configuration"]


class Dumper(Dumper):
    def increase_indent(self, flow=False, *args, **kwargs):
        return super().increase_indent(flow=flow, indentless=False)


def get_docs():
    swagger_docs = []
    for entry in scandir("../swagger"):
        if entry.name.endswith(".yaml"):
            swagger_docs.append(entry.name.replace(".yaml", ""))
    return swagger_docs


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
        save_yaml(type, data)


def entry(type: str = ""):
    if type != "":
        process_swagger(type)
    else:
        swagger_docs = get_docs()
        for type in swagger_docs:
            process_swagger(type)
