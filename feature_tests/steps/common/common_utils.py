import json


def render_template_document(context) -> str:
    template_text = context.template_document
    for row in context.table:
        template_text = template_text.replace(f'${row["property"]}', row["value"])
    return template_text
