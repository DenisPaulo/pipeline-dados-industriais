-- Teste genérico de VOLUME: falha se o modelo tiver menos linhas que o mínimo esperado.
-- Uso no YAML (no nível do modelo):
--   data_tests:
--     - volume_minimo:
--         arguments:
--           minimo: 24000
-- Como todo teste do dbt, ele é um SELECT que deve devolver ZERO linhas para passar.
{% test volume_minimo(model, minimo) %}

select count(*) as linhas, {{ minimo }} as minimo_esperado
from {{ model }}
having count(*) < {{ minimo }}

{% endtest %}
