import marimo

__generated_with = "0.23.9"
app = marimo.App()


@app.cell
def _():
    from project_pivot.data_platform.sql import (
        qualify_table_name,
        quote_identifier,
        quote_string_literal,
    )
    from sandboxes._notebook_init import notebook_init

    notebook_init()
    return qualify_table_name, quote_identifier, quote_string_literal


@app.cell
def _(quote_identifier):
    str_quote_identifier = "quote_identifier"
    print(str_quote_identifier)
    print(quote_identifier(identifier=str_quote_identifier))
    return


@app.cell
def _(qualify_table_name):
    str_qualify_table_name = "raw.hmda_loans"
    print(str_qualify_table_name)
    print(qualify_table_name(table_name=str_qualify_table_name))
    return


@app.cell
def _(quote_string_literal):
    str_quote_string_literal = "borrower's file"
    print(str_quote_string_literal)
    print(quote_string_literal(value=str_quote_string_literal))
    return


if __name__ == "__main__":
    app.run()
