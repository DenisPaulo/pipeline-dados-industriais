{#
  Por padrão o dbt junta o schema do perfil com o schema do modelo (ex.: analytics_staging).
  Aqui usamos só o nome definido no modelo (ex.: staging), que é mais fácil de ler no banco.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
