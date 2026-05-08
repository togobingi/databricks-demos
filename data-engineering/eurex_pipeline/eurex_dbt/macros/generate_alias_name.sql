{% macro generate_alias_name(custom_alias_name=none, node=none) -%}
    {%- set user_prefix = var('user_name', '') -%}
    {%- set base_name = custom_alias_name | trim if custom_alias_name else node.name -%}
    {%- if user_prefix -%}
        {{ user_prefix }}_{{ base_name }}
    {%- else -%}
        {{ base_name }}
    {%- endif -%}
{%- endmacro %}
